"""Console-script entry point for the plain-english-checker hook."""

import json
import sqlite3
import sys
from importlib import resources
from pathlib import Path

from plain_english_checker.config import (
    LIVE_CONFIG_PATH,
    CheckerSettings,
    IdiomSettings,
    TextstatSettings,
    WordfreqSettings,
    load_config,
)
from plain_english_checker.hook_payload import changed_text_segments, session_id_of
from plain_english_checker.idiom_check import IDIOM_CHECK_NAME, idioms_used
from plain_english_checker.matcher import find_matches
from plain_english_checker.textstat_check import TEXTSTAT_CHECK_NAME, hard_to_read_sentences
from plain_english_checker.tracking import (
    BLOCK_OUTCOME,
    TRACKING_DATABASE_PATH,
    WARN_OUTCOME,
    record_outcome,
)
from plain_english_checker.wordfreq_check import WORDFREQ_CHECK_NAME, uncommon_words
from plain_english_checker.wordlist import LIVE_WORDLIST_PATH, load_wordlist

SEED_WORDLIST_RESOURCE = "seed_wordlist.txt"
SEED_CONFIG_RESOURCE = "seed_config.toml"
BANNED_WORD_CHECK_NAME = "banned-word"
POST_TOOL_USE_EVENT_NAME = "PostToolUse"


def _record_outcome_without_failing_the_check(payload: dict, check_name: str, outcome: str) -> None:
    """Tracking is a usage signal, so a broken store must never change a check's outcome."""
    try:
        record_outcome(
            TRACKING_DATABASE_PATH,
            session_id=session_id_of(payload),
            check_name=check_name,
            outcome=outcome,
        )
    except (sqlite3.Error, OSError):
        pass


def check(argv: list[str]) -> int:
    """Read a PostToolUse hook payload from stdin, then warn on stdout and block on stderr.

    A warn and a block can both fire on one edit. The warn is still delivered as
    `additionalContext` on stdout, and the block's exit code 2 wins (see docs/adr/0002).
    """
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return 0

    segments = changed_text_segments(payload)
    if not segments:
        return 0

    written_text = "\n".join(segments)
    settings = load_config(LIVE_CONFIG_PATH)

    findings = _warn_findings(payload, written_text, settings)
    if findings:
        print(json.dumps(_additional_context_output("\n".join(findings))))

    block_reason = _banned_word_block_reason(payload, written_text)
    if block_reason:
        print(block_reason, file=sys.stderr)
        return 2
    return 0


def _warn_findings(payload: dict, written_text: str, settings: CheckerSettings) -> list[str]:
    findings = []
    for check_name, finding in (
        (WORDFREQ_CHECK_NAME, _wordfreq_finding(written_text, settings.wordfreq)),
        (TEXTSTAT_CHECK_NAME, _textstat_finding(written_text, settings.textstat)),
        (IDIOM_CHECK_NAME, _idiom_finding(written_text, settings.idiom)),
    ):
        if finding:
            _record_outcome_without_failing_the_check(payload, check_name, WARN_OUTCOME)
            findings.append(finding)
    return findings


def _wordfreq_finding(written_text: str, settings: WordfreqSettings) -> str:
    if not settings.enabled:
        return ""
    hits = uncommon_words(
        written_text, zipf_threshold=settings.zipf_threshold, allowlist=settings.allowlist
    )
    if not hits:
        return ""
    return (
        f"Uncommon word(s) used: {', '.join(hits)}. Most readers will not know them. "
        "Rewrite with everyday words, or add a word to the wordfreq allowlist in "
        f"{LIVE_CONFIG_PATH} when it is the right word to keep."
    )


def _textstat_finding(written_text: str, settings: TextstatSettings) -> str:
    if not settings.enabled:
        return ""
    hits = hard_to_read_sentences(
        written_text, flesch_reading_ease_threshold=settings.flesch_reading_ease_threshold
    )
    if not hits:
        return ""
    listed = "\n".join(f"- {sentence}" for sentence in hits)
    return (
        f"Sentence(s) that read too hard:\n{listed}\n"
        "Split each one into shorter sentences and use everyday words. Lower "
        f"flesch_reading_ease_threshold in {LIVE_CONFIG_PATH} when this warning "
        "comes too often."
    )


def _idiom_finding(written_text: str, settings: IdiomSettings) -> str:
    if not settings.enabled:
        return ""
    hits = idioms_used(written_text, allowlist=settings.allowlist)
    if not hits:
        return ""
    return (
        f"Idiom(s) used: {', '.join(hits)}. Readers who learned English as a second "
        "language will not know them. Say the plain meaning instead, or add an idiom to "
        f"the idiom allowlist in {LIVE_CONFIG_PATH} when it is the right wording to keep."
    )


def _additional_context_output(finding: str) -> dict:
    return {
        "continue": True,
        "hookSpecificOutput": {
            "hookEventName": POST_TOOL_USE_EVENT_NAME,
            "additionalContext": finding,
        },
    }


def _banned_word_block_reason(payload: dict, written_text: str) -> str:
    banned_terms = load_wordlist(LIVE_WORDLIST_PATH)
    if not banned_terms:
        return ""
    hits = find_matches(written_text, banned_terms)
    if not hits:
        return ""
    _record_outcome_without_failing_the_check(payload, BANNED_WORD_CHECK_NAME, BLOCK_OUTCOME)
    return (
        "Banned word(s) used: "
        f"{', '.join(hits)}. Re-read the root CLAUDE.md (Simplified Technical "
        "English rules) before continuing, then rewrite with simpler wording. "
        "Do not restate the full banned list."
    )


def seed(argv: list[str]) -> int:
    """Copy the seed wordlist and seed config to their live paths, never clobbering."""
    _copy_seed_file(LIVE_WORDLIST_PATH, SEED_WORDLIST_RESOURCE)
    _copy_seed_file(LIVE_CONFIG_PATH, SEED_CONFIG_RESOURCE)
    return 0


def _copy_seed_file(live_path: Path, resource_name: str) -> None:
    if live_path.exists():
        return
    live_path.parent.mkdir(parents=True, exist_ok=True)
    seed_text = (
        resources.files("plain_english_checker").joinpath(resource_name).read_text(encoding="utf-8")
    )
    live_path.write_text(seed_text, encoding="utf-8")


COMMANDS = {"check": check, "seed": seed}


def main() -> None:
    argv = sys.argv[1:]
    command_name = argv[0] if argv and argv[0] in COMMANDS else "check"
    remaining = argv[1:] if argv and argv[0] in COMMANDS else argv
    sys.exit(COMMANDS[command_name](remaining))


if __name__ == "__main__":
    main()

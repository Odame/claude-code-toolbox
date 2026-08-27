"""Console-script entry point for the plain-english-checker hook."""

import json
import sqlite3
import sys
from importlib import resources
from pathlib import Path

from plain_english_checker.checks import Severity, emit_findings, run_checks
from plain_english_checker.config import LIVE_CONFIG_PATH, load_config
from plain_english_checker.hook_payload import changed_text_segments, session_id_of
from plain_english_checker.tracking import (
    BLOCK_OUTCOME,
    TRACKING_DATABASE_PATH,
    WARN_OUTCOME,
    record_outcome,
)
from plain_english_checker.wordlist import LIVE_WORDLIST_PATH

SEED_WORDLIST_RESOURCE = "seed_wordlist.txt"
SEED_CONFIG_RESOURCE = "seed_config.toml"
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

    findings = run_checks(written_text, settings)
    for finding in findings:
        outcome = BLOCK_OUTCOME if finding.severity is Severity.BLOCK else WARN_OUTCOME
        _record_outcome_without_failing_the_check(payload, finding.check_name, outcome)

    return emit_findings(findings, additional_context_output=_additional_context_output)


def _additional_context_output(finding: str) -> dict:
    return {
        "continue": True,
        "hookSpecificOutput": {
            "hookEventName": POST_TOOL_USE_EVENT_NAME,
            "additionalContext": finding,
        },
    }


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

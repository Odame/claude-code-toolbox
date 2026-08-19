"""Console-script entry point for the plain-english-checker hook."""

import json
import sqlite3
import sys
from importlib import resources

from plain_english_checker.hook_payload import changed_text_segments, session_id_of
from plain_english_checker.matcher import find_matches
from plain_english_checker.tracking import (
    BLOCK_OUTCOME,
    TRACKING_DATABASE_PATH,
    record_outcome,
)
from plain_english_checker.wordlist import LIVE_WORDLIST_PATH, load_wordlist

SEED_WORDLIST_RESOURCE = "seed_wordlist.txt"
BANNED_WORD_CHECK_NAME = "banned-word"


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
    """Read a PostToolUse hook payload from stdin; block via stderr + exit 2 on hits."""
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return 0

    segments = changed_text_segments(payload)
    if not segments:
        return 0

    banned_terms = load_wordlist(LIVE_WORDLIST_PATH)
    if not banned_terms:
        return 0

    hits = find_matches("\n".join(segments), banned_terms)
    if not hits:
        return 0

    _record_outcome_without_failing_the_check(payload, BANNED_WORD_CHECK_NAME, BLOCK_OUTCOME)
    print(
        "Banned word(s) used: "
        f"{', '.join(hits)}. Re-read the root CLAUDE.md (Simplified Technical "
        "English rules) before continuing, then rewrite with simpler wording. "
        "Do not restate the full banned list.",
        file=sys.stderr,
    )
    return 2


def seed(argv: list[str]) -> int:
    """Copy the seed wordlist to the live path if the live wordlist doesn't exist yet."""
    if LIVE_WORDLIST_PATH.exists():
        return 0
    LIVE_WORDLIST_PATH.parent.mkdir(parents=True, exist_ok=True)
    seed_text = (
        resources.files("plain_english_checker")
        .joinpath(SEED_WORDLIST_RESOURCE)
        .read_text(encoding="utf-8")
    )
    LIVE_WORDLIST_PATH.write_text(seed_text, encoding="utf-8")
    return 0


COMMANDS = {"check": check, "seed": seed}


def main() -> None:
    argv = sys.argv[1:]
    command_name = argv[0] if argv and argv[0] in COMMANDS else "check"
    remaining = argv[1:] if argv and argv[0] in COMMANDS else argv
    sys.exit(COMMANDS[command_name](remaining))


if __name__ == "__main__":
    main()

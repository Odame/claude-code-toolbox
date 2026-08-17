"""Console-script entry point for the plain-english-checker hook."""

import json
import sys
from importlib import resources
from pathlib import Path

from plain_english_checker.matcher import find_matches
from plain_english_checker.wordlist import LIVE_WORDLIST_PATH, load_wordlist

SEED_WORDLIST_RESOURCE = "seed_wordlist.txt"


def _hook_target_path(payload: dict) -> str | None:
    tool_response = payload.get("tool_response")
    if isinstance(tool_response, dict) and tool_response.get("filePath"):
        return tool_response["filePath"]
    tool_input = payload.get("tool_input")
    if isinstance(tool_input, dict) and tool_input.get("file_path"):
        return tool_input["file_path"]
    return None


def check(argv: list[str]) -> int:
    """Read a PostToolUse hook payload from stdin; block via stderr + exit 2 on hits."""
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return 0

    file_path = _hook_target_path(payload)
    if not file_path:
        return 0

    target = Path(file_path)
    if not target.is_file():
        return 0

    banned_terms = load_wordlist(LIVE_WORDLIST_PATH)
    if not banned_terms:
        return 0

    text = target.read_text(encoding="utf-8", errors="ignore")
    hits = find_matches(text, banned_terms)
    if not hits:
        return 0

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

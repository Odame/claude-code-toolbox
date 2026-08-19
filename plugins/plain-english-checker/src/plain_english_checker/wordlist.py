"""Loading and parsing of banned-word list files."""

from pathlib import Path

LIVE_WORDLIST_PATH = Path.home() / ".claude" / "plain-english-checker" / "banned-words.txt"


def parse_wordlist(text: str) -> list[str]:
    """Parse wordlist file contents into an ordered list of banned terms.

    Blank lines and lines starting with `#` are ignored.
    """
    terms = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        terms.append(stripped)
    return terms


def load_wordlist(path: Path) -> list[str]:
    """Return the banned terms at `path`, or an empty list if it doesn't exist."""
    if not path.is_file():
        return []
    return parse_wordlist(path.read_text(encoding="utf-8"))

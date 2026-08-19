from pathlib import Path

from plain_english_checker.wordlist import load_wordlist, parse_wordlist


def test_parse_wordlist_ignores_comments_and_blank_lines():
    text = "# a comment\nutilize\n\nin order to\n  # indented comment\nleverage\n"
    assert parse_wordlist(text) == ["utilize", "in order to", "leverage"]


def test_parse_wordlist_empty_text():
    assert parse_wordlist("") == []


def test_load_wordlist_missing_file(tmp_path: Path):
    assert load_wordlist(tmp_path / "does-not-exist.txt") == []


def test_load_wordlist_reads_existing_file(tmp_path: Path):
    wordlist_path = tmp_path / "banned-words.txt"
    wordlist_path.write_text("utilize\nleverage\n", encoding="utf-8")
    assert load_wordlist(wordlist_path) == ["utilize", "leverage"]

import io
import json
import sqlite3
from pathlib import Path

import pytest

from plain_english_checker import cli


@pytest.fixture
def wordlist_path(monkeypatch, tmp_path: Path) -> Path:
    path = tmp_path / "banned-words.txt"
    path.write_text("utilize\nleverage\n", encoding="utf-8")
    monkeypatch.setattr(cli, "LIVE_WORDLIST_PATH", path)
    return path


@pytest.fixture
def tracking_database_path(monkeypatch, tmp_path: Path) -> Path:
    path = tmp_path / "tracking.sqlite3"
    monkeypatch.setattr(cli, "TRACKING_DATABASE_PATH", path)
    return path


def feed_payload(monkeypatch, payload: dict) -> None:
    monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps(payload)))


def tracked_rows(database_path: Path) -> list[tuple]:
    if not database_path.is_file():
        return []
    with sqlite3.connect(database_path) as connection:
        return connection.execute(
            "SELECT session_id, check_name, outcome, count FROM check_outcomes"
        ).fetchall()


def test_edit_blocks_on_a_banned_word_in_the_new_string(
    monkeypatch, capsys, wordlist_path, tracking_database_path
):
    feed_payload(
        monkeypatch,
        {
            "tool_name": "Edit",
            "tool_input": {
                "file_path": "notes.md",
                "old_string": "old wording",
                "new_string": "please utilize this",
            },
        },
    )

    exit_code = cli.check([])
    captured = capsys.readouterr()

    assert exit_code == 2
    assert "utilize" in captured.err
    assert captured.out == ""


def test_edit_ignores_banned_words_outside_the_new_string(
    monkeypatch, capsys, wordlist_path, tracking_database_path, tmp_path
):
    target = tmp_path / "target.md"
    target.write_text("we utilize things here and leverage others\n", encoding="utf-8")
    feed_payload(
        monkeypatch,
        {
            "tool_name": "Edit",
            "tool_input": {
                "file_path": str(target),
                "old_string": "we utilize things here",
                "new_string": "we use things here",
            },
        },
    )

    exit_code = cli.check([])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert captured.err == ""
    assert tracked_rows(tracking_database_path) == []


def test_multi_edit_blocks_on_a_banned_word_in_any_edit(
    monkeypatch, capsys, wordlist_path, tracking_database_path
):
    feed_payload(
        monkeypatch,
        {
            "tool_name": "MultiEdit",
            "tool_input": {
                "file_path": "notes.md",
                "edits": [
                    {"old_string": "a", "new_string": "this part is clean"},
                    {"old_string": "b", "new_string": "this part will leverage things"},
                ],
            },
        },
    )

    exit_code = cli.check([])
    captured = capsys.readouterr()

    assert exit_code == 2
    assert "leverage" in captured.err


def test_write_blocks_on_a_banned_word_anywhere_in_the_content(
    monkeypatch, capsys, wordlist_path, tracking_database_path
):
    feed_payload(
        monkeypatch,
        {
            "tool_name": "Write",
            "tool_input": {"file_path": "notes.md", "content": "line one\nplease utilize this\n"},
        },
    )

    exit_code = cli.check([])
    captured = capsys.readouterr()

    assert exit_code == 2
    assert "utilize" in captured.err


def test_hits_are_deduped_and_comma_joined(
    monkeypatch, capsys, wordlist_path, tracking_database_path
):
    feed_payload(
        monkeypatch,
        {
            "tool_name": "Write",
            "tool_input": {"content": "utilize this and utilize that, then leverage it"},
        },
    )

    exit_code = cli.check([])
    captured = capsys.readouterr()

    assert exit_code == 2
    assert "utilize, leverage" in captured.err


def test_clean_new_text_produces_no_output(
    monkeypatch, capsys, wordlist_path, tracking_database_path
):
    feed_payload(
        monkeypatch,
        {"tool_name": "Edit", "tool_input": {"new_string": "this text is clean"}},
    )

    exit_code = cli.check([])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert captured.out == ""
    assert captured.err == ""


def test_missing_wordlist_produces_no_output(monkeypatch, capsys, tmp_path, tracking_database_path):
    monkeypatch.setattr(cli, "LIVE_WORDLIST_PATH", tmp_path / "does-not-exist.txt")
    feed_payload(
        monkeypatch,
        {"tool_name": "Edit", "tool_input": {"new_string": "please utilize this"}},
    )

    exit_code = cli.check([])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert captured.out == ""
    assert captured.err == ""


def test_payload_without_changed_text_produces_no_output(
    monkeypatch, capsys, wordlist_path, tracking_database_path
):
    feed_payload(monkeypatch, {"tool_name": "Edit", "tool_input": {"file_path": "notes.md"}})

    exit_code = cli.check([])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert captured.err == ""


def test_malformed_payload_produces_no_output(monkeypatch, capsys, wordlist_path):
    monkeypatch.setattr("sys.stdin", io.StringIO("not json"))

    exit_code = cli.check([])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert captured.err == ""


def test_a_block_is_recorded_against_the_payload_session(
    monkeypatch, capsys, wordlist_path, tracking_database_path
):
    feed_payload(
        monkeypatch,
        {
            "session_id": "session-a",
            "tool_name": "Edit",
            "tool_input": {"new_string": "please utilize this"},
        },
    )

    assert cli.check([]) == 2
    assert tracked_rows(tracking_database_path) == [("session-a", "banned-word", "block", 1)]


def test_an_unwritable_tracking_store_does_not_stop_the_block(
    monkeypatch, capsys, wordlist_path, tmp_path
):
    unwritable = tmp_path / "not-a-directory" / "tracking.sqlite3"
    (tmp_path / "not-a-directory").write_text("", encoding="utf-8")
    monkeypatch.setattr(cli, "TRACKING_DATABASE_PATH", unwritable)
    feed_payload(
        monkeypatch,
        {"tool_name": "Edit", "tool_input": {"new_string": "please utilize this"}},
    )

    exit_code = cli.check([])
    captured = capsys.readouterr()

    assert exit_code == 2
    assert "utilize" in captured.err


def test_seed_creates_live_wordlist_when_missing(monkeypatch, tmp_path):
    path = tmp_path / "nested" / "banned-words.txt"
    monkeypatch.setattr(cli, "LIVE_WORDLIST_PATH", path)

    exit_code = cli.seed([])

    assert exit_code == 0
    assert path.is_file()
    assert "utilize" in path.read_text(encoding="utf-8")


def test_seed_does_not_clobber_existing_live_wordlist(monkeypatch, tmp_path):
    path = tmp_path / "banned-words.txt"
    path.write_text("my-custom-term\n", encoding="utf-8")
    monkeypatch.setattr(cli, "LIVE_WORDLIST_PATH", path)

    exit_code = cli.seed([])

    assert exit_code == 0
    assert path.read_text(encoding="utf-8") == "my-custom-term\n"

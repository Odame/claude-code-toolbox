import io
import json
import sqlite3
from pathlib import Path

import pytest

from plain_english_checker import banned_word_check, cli
from plain_english_checker.config import CheckerSettings, load_config


@pytest.fixture
def wordlist_path(monkeypatch, tmp_path: Path) -> Path:
    path = tmp_path / "banned-words.txt"
    path.write_text("utilize\nleverage\n", encoding="utf-8")
    monkeypatch.setattr(banned_word_check, "LIVE_WORDLIST_PATH", path)
    return path


@pytest.fixture(autouse=True)
def tracking_database_path(monkeypatch, tmp_path: Path) -> Path:
    path = tmp_path / "tracking.sqlite3"
    monkeypatch.setattr(cli, "TRACKING_DATABASE_PATH", path)
    return path


@pytest.fixture(autouse=True)
def config_path(monkeypatch, tmp_path: Path) -> Path:
    path = tmp_path / "config.toml"
    monkeypatch.setattr(cli, "LIVE_CONFIG_PATH", path)
    return path


HARD_TO_READ = (
    "The administration communicated that the international organization considered "
    "the responsibility unfortunately unavoidable under the circumstances."
)
EASY_TO_READ = "The cat sat on the mat and then looked at the dog for a while."


def feed_payload(monkeypatch, payload: dict) -> None:
    monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps(payload)))


def additional_context(stdout: str) -> str:
    hook_output = json.loads(stdout)
    assert hook_output["continue"] is True
    assert hook_output["hookSpecificOutput"]["hookEventName"] == "PostToolUse"
    return hook_output["hookSpecificOutput"]["additionalContext"]


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
    monkeypatch.setattr(banned_word_check, "LIVE_WORDLIST_PATH", tmp_path / "does-not-exist.txt")
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


def test_an_uncommon_word_warns_without_blocking(
    monkeypatch, capsys, wordlist_path, tracking_database_path
):
    feed_payload(
        monkeypatch,
        {
            "session_id": "session-a",
            "tool_name": "Edit",
            "tool_input": {"new_string": "the change was idempotent"},
        },
    )

    exit_code = cli.check([])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert captured.err == ""
    assert "idempotent" in additional_context(captured.out)
    assert tracked_rows(tracking_database_path) == [("session-a", "wordfreq", "warn", 1)]


def test_a_block_and_a_warn_on_the_same_edit_keep_both_outputs(
    monkeypatch, capsys, wordlist_path, tracking_database_path
):
    feed_payload(
        monkeypatch,
        {
            "session_id": "session-a",
            "tool_name": "Edit",
            "tool_input": {"new_string": "please utilize this idempotent change"},
        },
    )

    exit_code = cli.check([])
    captured = capsys.readouterr()

    assert exit_code == 2
    assert "utilize" in captured.err
    assert "idempotent" in additional_context(captured.out)
    assert sorted(tracked_rows(tracking_database_path)) == [
        ("session-a", "banned-word", "block", 1),
        ("session-a", "wordfreq", "warn", 1),
    ]


def test_an_uncommon_word_warns_even_without_a_wordlist(
    monkeypatch, capsys, tmp_path, tracking_database_path
):
    monkeypatch.setattr(banned_word_check, "LIVE_WORDLIST_PATH", tmp_path / "does-not-exist.txt")
    feed_payload(
        monkeypatch,
        {"tool_name": "Edit", "tool_input": {"new_string": "the change was idempotent"}},
    )

    exit_code = cli.check([])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "idempotent" in additional_context(captured.out)


def test_a_missing_config_file_leaves_the_wordfreq_check_running(
    monkeypatch, capsys, wordlist_path, tracking_database_path, config_path
):
    assert not config_path.exists()
    feed_payload(
        monkeypatch,
        {"tool_name": "Edit", "tool_input": {"new_string": "the change was idempotent"}},
    )

    assert cli.check([]) == 0
    assert "idempotent" in additional_context(capsys.readouterr().out)


def test_disabling_wordfreq_stops_the_warning(
    monkeypatch, capsys, wordlist_path, tracking_database_path, config_path
):
    config_path.write_text("[wordfreq]\nenabled = false\n", encoding="utf-8")
    feed_payload(
        monkeypatch,
        {"tool_name": "Edit", "tool_input": {"new_string": "the change was idempotent"}},
    )

    exit_code = cli.check([])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert captured.out == ""
    assert tracked_rows(tracking_database_path) == []


def test_an_allowlisted_term_is_not_warned_about(
    monkeypatch, capsys, wordlist_path, tracking_database_path, config_path
):
    config_path.write_text('[wordfreq]\nallowlist = ["idempotent"]\n', encoding="utf-8")
    feed_payload(
        monkeypatch,
        {"tool_name": "Edit", "tool_input": {"new_string": "the change was idempotent"}},
    )

    exit_code = cli.check([])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert captured.out == ""
    assert tracked_rows(tracking_database_path) == []


def test_a_lower_configured_threshold_stops_the_warning(
    monkeypatch, capsys, wordlist_path, tracking_database_path, config_path
):
    config_path.write_text("[wordfreq]\nzipf_threshold = 1.0\n", encoding="utf-8")
    feed_payload(
        monkeypatch,
        {"tool_name": "Edit", "tool_input": {"new_string": "the change was idempotent"}},
    )

    assert cli.check([]) == 0
    assert capsys.readouterr().out == ""


def test_code_identifiers_do_not_warn(monkeypatch, capsys, wordlist_path, tracking_database_path):
    feed_payload(
        monkeypatch,
        {
            "tool_name": "Write",
            "tool_input": {"content": "idempotent_retry_handler = 42  # see ZFSXQ"},
        },
    )

    exit_code = cli.check([])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert captured.out == ""


def test_a_hard_to_read_sentence_warns_without_blocking(
    monkeypatch, capsys, wordlist_path, tracking_database_path
):
    feed_payload(
        monkeypatch,
        {
            "session_id": "session-a",
            "tool_name": "Edit",
            "tool_input": {"new_string": HARD_TO_READ},
        },
    )

    exit_code = cli.check([])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert captured.err == ""
    assert HARD_TO_READ in additional_context(captured.out)
    assert tracked_rows(tracking_database_path) == [("session-a", "textstat", "warn", 1)]


def test_an_easy_sentence_does_not_warn(monkeypatch, capsys, wordlist_path, tracking_database_path):
    feed_payload(
        monkeypatch,
        {"tool_name": "Edit", "tool_input": {"new_string": EASY_TO_READ}},
    )

    exit_code = cli.check([])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert captured.out == ""
    assert tracked_rows(tracking_database_path) == []


def test_only_the_hard_sentence_of_an_edit_is_reported(
    monkeypatch, capsys, wordlist_path, tracking_database_path
):
    feed_payload(
        monkeypatch,
        {
            "tool_name": "Write",
            "tool_input": {"content": f"{EASY_TO_READ} {HARD_TO_READ} {EASY_TO_READ}"},
        },
    )

    assert cli.check([]) == 0
    finding = additional_context(capsys.readouterr().out)
    assert HARD_TO_READ in finding
    assert EASY_TO_READ not in finding


def test_a_missing_config_file_leaves_the_textstat_check_running(
    monkeypatch, capsys, wordlist_path, tracking_database_path, config_path
):
    assert not config_path.exists()
    feed_payload(monkeypatch, {"tool_name": "Edit", "tool_input": {"new_string": HARD_TO_READ}})

    assert cli.check([]) == 0
    assert HARD_TO_READ in additional_context(capsys.readouterr().out)


def test_disabling_textstat_stops_the_warning(
    monkeypatch, capsys, wordlist_path, tracking_database_path, config_path
):
    config_path.write_text("[textstat]\nenabled = false\n", encoding="utf-8")
    feed_payload(monkeypatch, {"tool_name": "Edit", "tool_input": {"new_string": HARD_TO_READ}})

    exit_code = cli.check([])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert captured.out == ""
    assert tracked_rows(tracking_database_path) == []


def test_a_lower_configured_flesch_threshold_stops_the_warning(
    monkeypatch, capsys, wordlist_path, tracking_database_path, config_path
):
    config_path.write_text("[textstat]\nflesch_reading_ease_threshold = -200\n", encoding="utf-8")
    feed_payload(monkeypatch, {"tool_name": "Edit", "tool_input": {"new_string": HARD_TO_READ}})

    assert cli.check([]) == 0
    assert capsys.readouterr().out == ""


def test_a_higher_configured_flesch_threshold_warns_on_easy_writing(
    monkeypatch, capsys, wordlist_path, tracking_database_path, config_path
):
    config_path.write_text("[textstat]\nflesch_reading_ease_threshold = 120\n", encoding="utf-8")
    feed_payload(monkeypatch, {"tool_name": "Edit", "tool_input": {"new_string": EASY_TO_READ}})

    assert cli.check([]) == 0
    assert EASY_TO_READ in additional_context(capsys.readouterr().out)


def test_disabling_wordfreq_leaves_textstat_running(
    monkeypatch, capsys, wordlist_path, tracking_database_path, config_path
):
    config_path.write_text("[wordfreq]\nenabled = false\n", encoding="utf-8")
    feed_payload(
        monkeypatch,
        {"tool_name": "Edit", "tool_input": {"new_string": f"An idempotent day. {HARD_TO_READ}"}},
    )

    assert cli.check([]) == 0
    finding = additional_context(capsys.readouterr().out)
    assert HARD_TO_READ in finding
    assert "idempotent" not in finding


def test_a_block_and_both_warns_on_one_edit_keep_every_output(
    monkeypatch, capsys, wordlist_path, tracking_database_path
):
    feed_payload(
        monkeypatch,
        {
            "session_id": "session-a",
            "tool_name": "Edit",
            "tool_input": {"new_string": f"Please utilize this idempotent change. {HARD_TO_READ}"},
        },
    )

    exit_code = cli.check([])
    captured = capsys.readouterr()

    assert exit_code == 2
    assert "utilize" in captured.err
    finding = additional_context(captured.out)
    assert "idempotent" in finding
    assert HARD_TO_READ in finding
    assert sorted(tracked_rows(tracking_database_path)) == [
        ("session-a", "banned-word", "block", 1),
        ("session-a", "textstat", "warn", 1),
        ("session-a", "wordfreq", "warn", 1),
    ]


def test_an_idiom_warns_without_blocking(
    monkeypatch, capsys, wordlist_path, tracking_database_path
):
    feed_payload(
        monkeypatch,
        {
            "session_id": "session-a",
            "tool_name": "Edit",
            "tool_input": {"new_string": "We kick the bucket on it."},
        },
    )

    exit_code = cli.check([])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert captured.err == ""
    assert "kick the bucket" in additional_context(captured.out)
    assert tracked_rows(tracking_database_path) == [("session-a", "idiom", "warn", 1)]


def test_writing_without_an_idiom_does_not_warn(
    monkeypatch, capsys, wordlist_path, tracking_database_path
):
    feed_payload(
        monkeypatch,
        {"tool_name": "Edit", "tool_input": {"new_string": "We stopped work on it."}},
    )

    exit_code = cli.check([])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert captured.out == ""
    assert tracked_rows(tracking_database_path) == []


def test_an_inflected_idiom_does_not_warn(
    monkeypatch, capsys, wordlist_path, tracking_database_path
):
    feed_payload(
        monkeypatch,
        {"tool_name": "Edit", "tool_input": {"new_string": "He kicked the bucket."}},
    )

    assert cli.check([]) == 0
    assert capsys.readouterr().out == ""


def test_a_missing_config_file_leaves_the_idiom_check_running(
    monkeypatch, capsys, wordlist_path, tracking_database_path, config_path
):
    assert not config_path.exists()
    feed_payload(
        monkeypatch,
        {"tool_name": "Edit", "tool_input": {"new_string": "We kick the bucket on it."}},
    )

    assert cli.check([]) == 0
    assert "kick the bucket" in additional_context(capsys.readouterr().out)


def test_disabling_idiom_stops_the_warning(
    monkeypatch, capsys, wordlist_path, tracking_database_path, config_path
):
    config_path.write_text("[idiom]\nenabled = false\n", encoding="utf-8")
    feed_payload(
        monkeypatch,
        {"tool_name": "Edit", "tool_input": {"new_string": "We kick the bucket on it."}},
    )

    exit_code = cli.check([])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert captured.out == ""
    assert tracked_rows(tracking_database_path) == []


def test_an_allowlisted_idiom_is_not_warned_about(
    monkeypatch, capsys, wordlist_path, tracking_database_path, config_path
):
    config_path.write_text('[idiom]\nallowlist = ["kick the bucket"]\n', encoding="utf-8")
    feed_payload(
        monkeypatch,
        {"tool_name": "Edit", "tool_input": {"new_string": "We kick the bucket on it."}},
    )

    exit_code = cli.check([])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert captured.out == ""
    assert tracked_rows(tracking_database_path) == []


def test_disabling_idiom_leaves_the_other_checks_running(
    monkeypatch, capsys, wordlist_path, tracking_database_path, config_path
):
    config_path.write_text("[idiom]\nenabled = false\n", encoding="utf-8")
    feed_payload(
        monkeypatch,
        {
            "tool_name": "Edit",
            "tool_input": {"new_string": "An idempotent day. We kick the bucket on it."},
        },
    )

    assert cli.check([]) == 0
    finding = additional_context(capsys.readouterr().out)
    assert "idempotent" in finding
    assert "kick the bucket" not in finding


def test_a_block_and_all_three_warns_on_one_edit_keep_every_output(
    monkeypatch, capsys, wordlist_path, tracking_database_path
):
    feed_payload(
        monkeypatch,
        {
            "session_id": "session-a",
            "tool_name": "Edit",
            "tool_input": {
                "new_string": (
                    f"Please utilize this idempotent change. We kick the bucket. {HARD_TO_READ}"
                )
            },
        },
    )

    exit_code = cli.check([])
    captured = capsys.readouterr()

    assert exit_code == 2
    assert "utilize" in captured.err
    finding = additional_context(captured.out)
    assert "idempotent" in finding
    assert HARD_TO_READ in finding
    assert "kick the bucket" in finding
    assert sorted(tracked_rows(tracking_database_path)) == [
        ("session-a", "banned-word", "block", 1),
        ("session-a", "idiom", "warn", 1),
        ("session-a", "textstat", "warn", 1),
        ("session-a", "wordfreq", "warn", 1),
    ]


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


def test_seed_writes_a_config_matching_the_built_in_defaults(monkeypatch, tmp_path, config_path):
    monkeypatch.setattr(cli, "LIVE_WORDLIST_PATH", tmp_path / "banned-words.txt")

    exit_code = cli.seed([])

    assert exit_code == 0
    assert load_config(config_path) == CheckerSettings()


def test_seed_does_not_clobber_an_existing_config(monkeypatch, tmp_path, config_path):
    monkeypatch.setattr(cli, "LIVE_WORDLIST_PATH", tmp_path / "banned-words.txt")
    config_path.write_text("[wordfreq]\nenabled = false\n", encoding="utf-8")

    exit_code = cli.seed([])

    assert exit_code == 0
    assert load_config(config_path).wordfreq.enabled is False

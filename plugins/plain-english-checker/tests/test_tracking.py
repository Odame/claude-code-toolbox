import sqlite3
from datetime import date
from pathlib import Path

from plain_english_checker.tracking import BLOCK_OUTCOME, WARN_OUTCOME, record_outcome


def read_rows(database_path: Path) -> list[tuple]:
    with sqlite3.connect(database_path) as connection:
        return connection.execute(
            "SELECT date, session_id, check_name, outcome, count"
            " FROM check_outcomes ORDER BY date, session_id, check_name, outcome"
        ).fetchall()


def test_record_outcome_creates_store_and_first_row(tmp_path: Path):
    database_path = tmp_path / "nested" / "tracking.sqlite3"

    record_outcome(
        database_path,
        session_id="session-a",
        check_name="banned-word",
        outcome=BLOCK_OUTCOME,
        today=date(2026, 8, 19),
    )

    assert read_rows(database_path) == [("2026-08-19", "session-a", "banned-word", "block", 1)]


def test_record_outcome_increments_existing_row(tmp_path: Path):
    database_path = tmp_path / "tracking.sqlite3"
    for _ in range(3):
        record_outcome(
            database_path,
            session_id="session-a",
            check_name="banned-word",
            outcome=BLOCK_OUTCOME,
            today=date(2026, 8, 19),
        )

    assert read_rows(database_path) == [("2026-08-19", "session-a", "banned-word", "block", 3)]


def test_record_outcome_keys_rows_separately(tmp_path: Path):
    database_path = tmp_path / "tracking.sqlite3"
    record_outcome(
        database_path,
        session_id="session-a",
        check_name="banned-word",
        outcome=BLOCK_OUTCOME,
        today=date(2026, 8, 19),
    )
    record_outcome(
        database_path,
        session_id="session-b",
        check_name="banned-word",
        outcome=BLOCK_OUTCOME,
        today=date(2026, 8, 19),
    )
    record_outcome(
        database_path,
        session_id="session-a",
        check_name="wordfreq",
        outcome=WARN_OUTCOME,
        today=date(2026, 8, 19),
    )
    record_outcome(
        database_path,
        session_id="session-a",
        check_name="banned-word",
        outcome=BLOCK_OUTCOME,
        today=date(2026, 8, 20),
    )

    assert read_rows(database_path) == [
        ("2026-08-19", "session-a", "banned-word", "block", 1),
        ("2026-08-19", "session-a", "wordfreq", "warn", 1),
        ("2026-08-19", "session-b", "banned-word", "block", 1),
        ("2026-08-20", "session-a", "banned-word", "block", 1),
    ]


def test_store_records_no_text_or_file_paths(tmp_path: Path):
    database_path = tmp_path / "tracking.sqlite3"
    record_outcome(
        database_path,
        session_id="session-a",
        check_name="banned-word",
        outcome=BLOCK_OUTCOME,
        today=date(2026, 8, 19),
    )

    with sqlite3.connect(database_path) as connection:
        columns = {row[1] for row in connection.execute("PRAGMA table_info(check_outcomes)")}

    assert columns == {"date", "session_id", "check_name", "outcome", "count"}


def test_rows_older_than_the_retention_window_are_pruned(tmp_path: Path):
    database_path = tmp_path / "tracking.sqlite3"
    record_outcome(
        database_path,
        session_id="session-a",
        check_name="banned-word",
        outcome=BLOCK_OUTCOME,
        today=date(2026, 1, 1),
        retention_day_limit=30,
    )
    record_outcome(
        database_path,
        session_id="session-a",
        check_name="banned-word",
        outcome=BLOCK_OUTCOME,
        today=date(2026, 8, 19),
        retention_day_limit=30,
    )

    assert read_rows(database_path) == [("2026-08-19", "session-a", "banned-word", "block", 1)]


def test_rows_beyond_the_row_limit_are_pruned_oldest_first(tmp_path: Path):
    database_path = tmp_path / "tracking.sqlite3"
    for day in (17, 18, 19):
        record_outcome(
            database_path,
            session_id="session-a",
            check_name="banned-word",
            outcome=BLOCK_OUTCOME,
            today=date(2026, 8, day),
            retention_row_limit=2,
        )

    assert read_rows(database_path) == [
        ("2026-08-18", "session-a", "banned-word", "block", 1),
        ("2026-08-19", "session-a", "banned-word", "block", 1),
    ]


def test_concurrent_increments_are_not_lost(tmp_path: Path):
    from concurrent.futures import ThreadPoolExecutor

    database_path = tmp_path / "tracking.sqlite3"
    record_count = 40

    def record_once(_: int) -> None:
        record_outcome(
            database_path,
            session_id="session-a",
            check_name="banned-word",
            outcome=BLOCK_OUTCOME,
            today=date(2026, 8, 19),
        )

    with ThreadPoolExecutor(max_workers=8) as pool:
        list(pool.map(record_once, range(record_count)))

    assert read_rows(database_path) == [
        ("2026-08-19", "session-a", "banned-word", "block", record_count)
    ]

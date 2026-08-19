"""Counts-only SQLite store of check outcomes (see docs/adr/0003)."""

import sqlite3
from datetime import date, timedelta
from pathlib import Path

TRACKING_DATABASE_PATH = Path.home() / ".claude" / "plain-english-checker" / "tracking.sqlite3"

BLOCK_OUTCOME = "block"
WARN_OUTCOME = "warn"

RETENTION_DAY_LIMIT = 90
RETENTION_ROW_LIMIT = 5000

CONCURRENT_WRITER_WAIT_SECONDS = 10.0

_CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS check_outcomes (
    date TEXT NOT NULL,
    session_id TEXT NOT NULL,
    check_name TEXT NOT NULL,
    outcome TEXT NOT NULL,
    count INTEGER NOT NULL,
    PRIMARY KEY (date, session_id, check_name, outcome)
)
"""

_UPSERT_COUNT = """
INSERT INTO check_outcomes (date, session_id, check_name, outcome, count)
VALUES (?, ?, ?, ?, 1)
ON CONFLICT (date, session_id, check_name, outcome)
DO UPDATE SET count = count + 1
"""

_DELETE_ROWS_BEYOND_LIMIT = """
DELETE FROM check_outcomes
WHERE rowid NOT IN (
    SELECT rowid FROM check_outcomes ORDER BY date DESC, rowid DESC LIMIT ?
)
"""


def record_outcome(
    database_path: Path,
    *,
    session_id: str,
    check_name: str,
    outcome: str,
    today: date | None = None,
    retention_day_limit: int = RETENTION_DAY_LIMIT,
    retention_row_limit: int = RETENTION_ROW_LIMIT,
) -> None:
    """Increment the count for one check outcome, then prune by age and by row count.

    The increment is a single SQLite upsert, so concurrent hook invocations from
    separate sessions serialise on SQLite's own write lock instead of racing.
    """
    recorded_on = today or date.today()
    database_path.parent.mkdir(parents=True, exist_ok=True)
    oldest_date_kept = (recorded_on - timedelta(days=retention_day_limit)).isoformat()

    connection = sqlite3.connect(database_path, timeout=CONCURRENT_WRITER_WAIT_SECONDS)
    try:
        connection.execute("PRAGMA journal_mode = WAL")
        connection.execute(_CREATE_TABLE)
        with connection:
            connection.execute(
                _UPSERT_COUNT, (recorded_on.isoformat(), session_id, check_name, outcome)
            )
            connection.execute("DELETE FROM check_outcomes WHERE date < ?", (oldest_date_kept,))
            connection.execute(_DELETE_ROWS_BEYOND_LIMIT, (retention_row_limit,))
    finally:
        connection.close()

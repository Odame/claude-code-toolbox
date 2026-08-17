# SQLite counts-only tracking, not a JSONL event log

We need to track how often and when each check blocks or warns, across all checks including the existing banned-word check. First instinct was an append-only JSONL event log (one line per finding, mirroring the wordlist's plain-text style) — but that has two problems: it records exactly what was flagged in a file that may hold sensitive content, and incrementing any derived counter from it would need a read-modify-write that races across concurrent Claude Code sessions writing the same file.

We're using SQLite instead, storing counts only — no matched terms, no snippets, no file paths. Schema: `(date, session_id, check_name, outcome, count)`, upsert-incremented per hook run. SQLite's own locking makes the increment atomic across concurrent sessions; the counts-only shape means the table stays small regardless of edit volume, and there's nothing sensitive in it. `session_id` comes from the `PostToolUse` hook payload.

## Considered Options

- **JSONL event log** — simplest to append to, but not concurrency-safe for derived counters and captures more content than needed for a usage signal.
- **SQLite, counts only** (chosen) — atomic increments, bounded growth, no content captured.

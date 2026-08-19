---
name: unban-term
description: Stop the plain-english-checker flagging a word or phrase — remove it from the banned-term list and add it to the wordfreq and idiom allowlists. Trigger on any request to unban or allowlist a term for this checker — "stop flagging X", "unban 'leverage'", "'utilize' is fine, stop blocking it".
---

Live wordlist: `~/.claude/plain-english-checker/banned-words.txt` (`LIVE_WORDLIST_PATH` in `wordlist.py`) — one term per line, `#` for comments.

Live config: `~/.claude/plain-english-checker/config.toml` (`LIVE_CONFIG_PATH` in `config.py`) — a `[wordfreq]` and an `[idiom]` section, each holding an `allowlist` array of strings. `[textstat]` has no allowlist: it scores whole sentences, not terms, so a term cannot be unbanned there.

One term can be flagged by three checks, so one invocation does all three edits below and reports all three results.

1. Take the term from the request. Strip surrounding quote marks, trim whitespace, lowercase it. Both allowlists compare case-insensitively, so the lowercased form is the one to store.
2. Wordlist: read the file and drop every line whose trimmed text equals the term, ignoring case. Leave every other line, comments included, as it was. A missing file means the term was never banned. Note whether you removed a line.
3. When `config.toml` or its parent directory is missing (the `SessionStart` seed hook normally writes both), create a file holding only a `[wordfreq]` and an `[idiom]` section, each with the term in its `allowlist`, then go to step 7. Every setting you leave out keeps its built-in default.
4. Wordfreq allowlist: read `config.toml` and add the term as a quoted string to the `allowlist` array in the `[wordfreq]` section, unless an entry already equals it, ignoring case. Add the `allowlist` key, or the whole `[wordfreq]` section, when either is missing. Note whether you added the term.
5. Idiom allowlist: repeat step 4 against the `[idiom]` section.
6. Keep the rest of `config.toml` as it was — its comments explain each setting to the user. Read the written file back and confirm both arrays still parse as TOML: the hook drops every check to its built-in default when the file stops parsing, which would undo this change and silently loosen the other checks.
7. Confirm to the user all three results, one line each: removed from the wordlist or was never on it, added to the wordfreq allowlist or already there, added to the idiom allowlist or already there. When all three were already in the wanted state, say the term is already unbanned everywhere and that you changed nothing.

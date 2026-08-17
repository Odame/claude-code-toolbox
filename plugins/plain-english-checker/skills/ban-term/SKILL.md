---
name: ban-term
description: Add a word or phrase to the plain-english-checker's banned-term list. Trigger on any request to ban, blocklist, or flag a term as jargon for this checker — "ban the word X", "add 'leverage' to the banned words list", "flag 'utilize' as jargon".
---

Live wordlist: `~/.claude/plain-english-checker/banned-words.txt` (`LIVE_WORDLIST_PATH` in `wordlist.py`) — one term per line, `#` for comments. The `plain-english-checker` PostToolUse hook reads this file on every Write/Edit.

1. Take the term from the request. Strip surrounding quote marks, trim whitespace, lowercase it.
2. If the file or its parent directory doesn't exist, create them (the `SessionStart` seed hook normally already has).
3. Case-insensitively search the file's lines for the term. If found, tell the user it's already banned — done, don't write anything.
4. Otherwise append the term as a new line and confirm to the user exactly what was added.

# claude-code-toolbox

A personal collection of Claude Code plugins, skills, and hooks for day-to-day development.

## Layout

This repo is a `uv` workspace and a Claude Code plugin marketplace at once:

```
.claude-plugin/marketplace.json   # marketplace manifest, lists every plugin below
plugins/
  plain-english-checker/          # one plugin = one workspace member = one bounded unit
    .claude-plugin/plugin.json
    hooks/hooks.json
    skills/ban-term/SKILL.md
    src/plain_english_checker/
    tests/
    pyproject.toml
pyproject.toml                    # uv workspace root
```

Each plugin lives in its own directory under `plugins/`, is self-contained (its own
`pyproject.toml` where it has Python code), and is a member of the root `uv` workspace.
Adding a new plugin or skill means adding a new directory under `plugins/` and an entry
in the marketplace manifest — the layout scales without restructuring anything already there.

To use a plugin from this marketplace in your own Claude Code setup:

```
/plugin marketplace add https://github.com/Odame/claude-code-toolbox
/plugin install plain-english-checker@claude-code-toolbox
```

## plain-english-checker

Blocks jargon and flags uncommon words before they land in a file you're writing or editing.

**How it works:**

- A `PostToolUse` hook (matcher `Write|Edit|MultiEdit`) reads only the text the tool just
  wrote — a `Write`'s whole content, or each `Edit`/`MultiEdit` replacement. Untouched parts
  of the file are never scanned.
- The **banned-word check** matches that text against your live banned-term list. On a match
  the hook exits with code 2 and writes a message to stderr — Claude Code shows that to Claude
  as feedback, telling it to re-read the root `CLAUDE.md` and rewrite with simpler wording,
  without dumping the full banned list back into context.
- The **wordfreq check** scores every written word against corpus frequency and flags the rare
  ones. It never blocks: the finding goes back to Claude as `additionalContext` on exit 0, so
  Claude can fix the wording in the same turn. Code identifiers, acronyms, numbers, URLs, and
  capitalized words are skipped, so a variable name is never flagged as rare.
- A `SessionStart` hook seeds your live wordlist and your `config.toml` the first time each is
  missing, from seed files shipped with the plugin (`utilize`, `leverage`, `in order to`, ...).
  It never touches a live file again once it exists, so plugin updates can't clobber your
  additions.
- Your live, growing list lives at `~/.claude/plain-english-checker/banned-words.txt` —
  outside the plugin's own directory, so it survives plugin updates. One term or phrase per
  line; `#` for comments.

**Tuning** — `~/.claude/plain-english-checker/config.toml`:

```toml
[wordfreq]
enabled = true
zipf_threshold = 2.5
allowlist = []
```

`zipf_threshold` is a Zipf frequency, running from 0 (never seen) to about 7 (`the`); a word
scoring below it is flagged. Raise it to catch more words, lower it if the warnings come too
often. Any term in `allowlist` is never flagged, however rare it is. These same defaults apply
when the file is missing.

**The `ban-term` skill** lets you grow the list from conversation — say things like "ban the
word utilize" or "add 'leverage' to the banned words list" and Claude appends it to your live
list (skipping anything already there, case-insensitively).

Matching is case-insensitive and whole-word/whole-phrase (`cat` won't match inside `category`).

## Development

```
uv sync --all-packages
uv run ruff check .
uv run ruff format --check .
uv run pytest plugins/plain-english-checker
```

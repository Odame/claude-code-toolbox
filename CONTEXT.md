# Claude Code Toolbox

Personal collection of Claude Code plugins, skills, and hooks, published as a plugin marketplace.

## Language

### Plain English Checker (`plugins/plain-english-checker/`)

**Check**:
A single scan step that inspects an edited file's text and decides whether to flag it. Each check has its own outcome (block or warn). Examples: the banned-word check, the wordfreq check.
_Avoid_: rule, validator, linter

**Block**:
A check outcome that rejects the completed edit and forces Claude to rewrite it, via `PostToolUse` exit code 2 (stderr fed back to Claude as a required fix).
_Avoid_: fail, error, reject

**Warn**:
A check outcome that surfaces a finding to Claude without rejecting the edit, via `PostToolUse` exit code 0 with `hookSpecificOutput.additionalContext` (`continue: true`). Claude sees the finding and may self-correct, but the edit already stands.
_Avoid_: notice, soft-fail

**Wordlist**:
The plain-text, user-editable list of exact terms/phrases the banned-word check matches against — one entry per line, lives at `~/.claude/plain-english-checker/banned-words.txt`.
_Avoid_: banned-words list, blocklist

**Allowlist**:
A per-check, per-term suppression list in `config.toml` that exempts specific words/phrases from a check's findings. Only wordfreq and idiom have one — textstat scores whole sentences, not terms, so there's nothing to allowlist.
_Avoid_: exceptions, ignore list, whitelist

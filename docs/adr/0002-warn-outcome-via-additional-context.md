# New checks warn via additionalContext instead of blocking

The existing banned-word check blocks (`PostToolUse` exit 2) on every match — appropriate for an exact-match list the user explicitly curated, but wordfreq/textstat/idiom are statistical/fuzzy and carry real false-positive risk. Blocking on those would reject legitimate edits until thresholds are perfectly tuned. We decided new checks warn instead: exit 0 with `hookSpecificOutput.additionalContext` set to the finding and `continue: true`. Claude still sees the finding in context this turn and can choose to self-correct, but the edit is never rejected.

This sets the severity model for any future check added to this hook: block is reserved for exact, user-curated matches; anything scored/fuzzy warns. A future check should default to warn unless there's a specific reason to block.

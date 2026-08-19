# Add wordfreq and textstat as runtime dependencies

`plain-english-checker` shipped with zero runtime dependencies (stdlib only) so the hook stays fast and trivially auditable. The new wordfreq and textstat checks need corpus-backed frequency scoring and readability scoring that aren't worth reimplementing — hand-rolling a frequency table or a Flesch scorer would be more code to maintain than the dependency itself, for no real benefit. We're accepting the two deps rather than vendoring or reimplementing them. Idiom detection stays dependency-free: the MAGPIE-derived list is a static data file, matched with the existing regex matcher (see ADR-0004).

## Considered Options

- **Vendor/reimplement inline** — keeps the zero-dep policy intact, but duplicates well-tested corpus data and scoring logic that these libraries already provide.
- **Add as runtime deps** (chosen) — small, pure-Python packages (wordfreq bundles compressed frequency data; textstat has no heavy transitive deps), low install cost via `uv`.

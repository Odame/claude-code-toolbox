# Defer spaCy-based linguistic analysis to a later phase

wordfreq/textstat/idiom (this round) all work on surface text — word lookup, sentence scoring, exact-phrase matching. spaCy would enable deeper analysis: lemmatization (matching "preserve"/"preserving"/"preserved" as one concept), a PhraseMatcher for more robust boundary handling, and dependency-parse-based detection of passive voice and nominalizations. We're deliberately not building any of this now — it's a heavier dependency (a spaCy model download, not just a pip package) and a different kind of check (structural, not lexical) than the other three tickets.

The concrete gap this leaves: the idiom check only matches base/citation forms, so an inflected idiom ("kicked the bucket") won't be caught. We're not solving that with a stopgap (e.g. ad hoc suffix stripping) — it stays an open gap until the spaCy phase, or until real usage data shows it's worth solving sooner.

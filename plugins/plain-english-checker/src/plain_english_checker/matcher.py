"""Case-insensitive whole-word/whole-phrase matching against a banned-term list."""

import re


def find_matches(text: str, banned_terms: list[str]) -> list[str]:
    """Return banned terms found in `text`, deduped, in banned-list order.

    Matching is case-insensitive and respects word boundaries, so a term like
    "cat" does not match inside "category". The boundary is written as a pair of
    lookarounds rather than `\\b`, because `\\b` inverts its meaning next to a term
    that starts or ends with punctuation ("my foot!") and would then never match.
    """
    hits = []
    seen = set()
    for term in banned_terms:
        pattern = r"(?<!\w)" + re.escape(term) + r"(?!\w)"
        if term.lower() in seen:
            continue
        if re.search(pattern, text, re.IGNORECASE):
            hits.append(term)
            seen.add(term.lower())
    return hits

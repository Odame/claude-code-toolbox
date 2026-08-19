"""Case-insensitive whole-word/whole-phrase matching against a banned-term list."""

import re


def find_matches(text: str, banned_terms: list[str]) -> list[str]:
    """Return banned terms found in `text`, deduped, in banned-list order.

    Matching is case-insensitive and respects word boundaries, so a term like
    "cat" does not match inside "category".
    """
    hits = []
    seen = set()
    for term in banned_terms:
        pattern = r"\b" + re.escape(term) + r"\b"
        if term.lower() in seen:
            continue
        if re.search(pattern, text, re.IGNORECASE):
            hits.append(term)
            seen.add(term.lower())
    return hits

"""Scoring written words against corpus frequency, to flag rare vocabulary."""

import re
from collections.abc import Iterable

from wordfreq import zipf_frequency

from plain_english_checker.checks import CheckSpec, Severity, register_check
from plain_english_checker.config import LIVE_CONFIG_PATH, CheckerSettings, WordfreqSettings

WORDFREQ_CHECK_NAME = "wordfreq"

SCORED_LANGUAGE = "en"

_URL = re.compile(r"(?:https?://|www\.)\S+", re.IGNORECASE)
_TOKEN = re.compile(r"[A-Za-z0-9_'’]+")
_CAMEL_CASE_BOUNDARY = re.compile(r"[a-z][A-Z]")
_POSSESSIVE_ENDING = re.compile(r"['’]s$")
_DOT_AFTER_A_WORD = re.compile(r"\w\.")
_DOT_BEFORE_A_WORD = re.compile(r"\.\w")
_QUOTE_CHARACTERS = "'’"


def uncommon_words(text: str, *, zipf_threshold: float, allowlist: Iterable[str]) -> list[str]:
    """Return the rare words in `text`, deduped, in order of first appearance.

    A word is rare when its Zipf frequency is below `zipf_threshold`. Tokens that are
    not everyday writing — code identifiers, acronyms, numbers, URLs, and capitalized
    words — are dropped before scoring, so they can never be flagged.
    """
    exempt = {term.lower() for term in allowlist}
    hits: list[str] = []
    seen: set[str] = set()
    for token in _scorable_tokens(text):
        if token in seen or token in exempt:
            continue
        seen.add(token)
        if zipf_frequency(token, SCORED_LANGUAGE) < zipf_threshold:
            hits.append(token)
    return hits


def _scorable_tokens(text: str) -> list[str]:
    without_urls = _URL.sub(" ", text)
    tokens = []
    for match in _TOKEN.finditer(without_urls):
        if _sits_inside_a_dotted_path(without_urls, match.start(), match.end()):
            continue
        token = _POSSESSIVE_ENDING.sub("", match.group().strip(_QUOTE_CHARACTERS))
        if token and _is_an_everyday_word(token):
            tokens.append(token.lower())
    return tokens


def _sits_inside_a_dotted_path(text: str, start: int, end: int) -> bool:
    """A word joined to another by a dot is one part of an identifier, not a word."""
    return bool(
        _DOT_AFTER_A_WORD.fullmatch(text[max(start - 2, 0) : start])
        or _DOT_BEFORE_A_WORD.fullmatch(text[end : end + 2])
    )


def _is_an_everyday_word(token: str) -> bool:
    if "_" in token or any(character.isdigit() for character in token):
        return False
    if token.isupper() and len(token) > 1:
        return False
    if _CAMEL_CASE_BOUNDARY.search(token):
        return False
    return not token[0].isupper()


def _settings_of(settings: CheckerSettings) -> WordfreqSettings:
    return settings.wordfreq


def _detect(text: str, settings: WordfreqSettings) -> list[str]:
    return uncommon_words(
        text, zipf_threshold=settings.zipf_threshold, allowlist=settings.allowlist
    )


def _describe(hits: list[str]) -> str:
    return (
        f"Uncommon word(s) used: {', '.join(hits)}. Most readers will not know them. "
        "Rewrite with everyday words, or add a word to the wordfreq allowlist in "
        f"{LIVE_CONFIG_PATH} when it is the right word to keep."
    )


register_check(
    CheckSpec(
        name=WORDFREQ_CHECK_NAME,
        severity=Severity.WARN,
        settings_of=_settings_of,
        detect=_detect,
        describe=_describe,
    )
)

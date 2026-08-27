"""Scoring each written sentence for readability, to flag dense writing."""

import re

import textstat

from plain_english_checker.checks import CheckSpec, Severity, register_check
from plain_english_checker.config import LIVE_CONFIG_PATH, CheckerSettings, TextstatSettings

TEXTSTAT_CHECK_NAME = "textstat"

MINIMUM_SCORED_WORD_COUNT = 8

_PARAGRAPH_BREAK = re.compile(r"\n[ \t]*\n")
_SENTENCE_END = re.compile(r"[.!?]+(?=\s|$)")
_WORD = re.compile(r"[A-Za-z][A-Za-z'’-]*")
_URL = re.compile(r"(?:https?://|www\.)\S+", re.IGNORECASE)


def hard_to_read_sentences(text: str, *, flesch_reading_ease_threshold: float) -> list[str]:
    """Return the sentences in `text` that read harder than the threshold allows.

    Every sentence is scored on its own, so one dense sentence is caught inside an
    otherwise-plain edit. Sentences shorter than `MINIMUM_SCORED_WORD_COUNT` words are
    left unscored: Flesch Reading Ease is a ratio of words to sentences and syllables to
    words, so a handful of long words with no sentence length to balance them scores far
    below any usable threshold ("Idempotency." scores -132).
    """
    return [
        sentence
        for sentence in sentences_of(text)
        if _reads_harder_than(sentence, flesch_reading_ease_threshold)
    ]


def _reads_harder_than(sentence: str, flesch_reading_ease_threshold: float) -> bool:
    """A URL is counted out first: it is one long unreadable token that is never read aloud."""
    without_urls = _URL.sub(" ", sentence)
    if len(_WORD.findall(without_urls)) < MINIMUM_SCORED_WORD_COUNT:
        return False
    return textstat.flesch_reading_ease(without_urls) < flesch_reading_ease_threshold


def sentences_of(text: str) -> list[str]:
    """Return the finished sentences in `text`, in writing order, wrapped lines rejoined.

    A sentence runs to a `.`, `!`, or `?` that ends a word, and a blank line ends one
    early. Text after the last of those is an unfinished thought — a heading, a bullet,
    or a line of code — and is dropped rather than scored as if it were a sentence.
    """
    return [
        sentence
        for paragraph in _PARAGRAPH_BREAK.split(text)
        for sentence in _sentences_in(paragraph)
    ]


def _sentences_in(paragraph: str) -> list[str]:
    sentences = []
    start = 0
    for terminator in _SENTENCE_END.finditer(paragraph):
        sentence = " ".join(paragraph[start : terminator.end()].split())
        if sentence:
            sentences.append(sentence)
        start = terminator.end()
    return sentences


def _settings_of(settings: CheckerSettings) -> TextstatSettings:
    return settings.textstat


def _detect(text: str, settings: TextstatSettings) -> list[str]:
    return hard_to_read_sentences(
        text, flesch_reading_ease_threshold=settings.flesch_reading_ease_threshold
    )


def _describe(hits: list[str]) -> str:
    listed = "\n".join(f"- {sentence}" for sentence in hits)
    return (
        f"Sentence(s) that read too hard:\n{listed}\n"
        "Split each one into shorter sentences and use everyday words. Lower "
        f"flesch_reading_ease_threshold in {LIVE_CONFIG_PATH} when this warning "
        "comes too often."
    )


register_check(
    CheckSpec(
        name=TEXTSTAT_CHECK_NAME,
        severity=Severity.WARN,
        settings_of=_settings_of,
        detect=_detect,
        describe=_describe,
    )
)

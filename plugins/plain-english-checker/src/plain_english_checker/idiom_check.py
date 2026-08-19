"""Matching written text against a bundled idiom list, to flag filler phrases."""

from collections.abc import Iterable
from importlib import resources

from plain_english_checker.checks import CheckSpec, Severity, register_check
from plain_english_checker.config import LIVE_CONFIG_PATH, CheckerSettings, IdiomSettings
from plain_english_checker.matcher import find_matches
from plain_english_checker.wordlist import parse_wordlist

IDIOM_CHECK_NAME = "idiom"

BUNDLED_IDIOM_RESOURCE = "idioms.txt"


def idioms_used(text: str, *, allowlist: Iterable[str]) -> list[str]:
    """Return the bundled idioms found in `text`, deduped, in list order.

    Matching is the same exact-phrase, case-insensitive, whole-phrase matching the
    banned-word check uses. Only the base form of an idiom is listed, so an inflected
    use ("kicked the bucket") is not caught — a known gap recorded in docs/adr/0005.
    """
    exempt = {idiom.lower() for idiom in allowlist}
    candidates = [idiom for idiom in bundled_idioms() if idiom.lower() not in exempt]
    return find_matches(text, candidates)


def bundled_idioms() -> list[str]:
    """Return the idiom list shipped with the plugin, extracted from the MAGPIE corpus."""
    text = (
        resources.files("plain_english_checker")
        .joinpath(BUNDLED_IDIOM_RESOURCE)
        .read_text(encoding="utf-8")
    )
    return parse_wordlist(text)


def _settings_of(settings: CheckerSettings) -> IdiomSettings:
    return settings.idiom


def _detect(text: str, settings: IdiomSettings) -> list[str]:
    return idioms_used(text, allowlist=settings.allowlist)


def _describe(hits: list[str]) -> str:
    return (
        f"Idiom(s) used: {', '.join(hits)}. Readers who learned English as a second "
        "language will not know them. Say the plain meaning instead, or add an idiom to "
        f"the idiom allowlist in {LIVE_CONFIG_PATH} when it is the right wording to keep."
    )


register_check(
    CheckSpec(
        name=IDIOM_CHECK_NAME,
        severity=Severity.WARN,
        settings_of=_settings_of,
        detect=_detect,
        describe=_describe,
    )
)

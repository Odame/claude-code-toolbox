"""Per-check tuning read from `config.toml`, which sits beside the live wordlist."""

import tomllib
from dataclasses import dataclass, field
from pathlib import Path

from plain_english_checker.wordlist import LIVE_WORDLIST_PATH

LIVE_CONFIG_PATH = LIVE_WORDLIST_PATH.parent / "config.toml"

WORDFREQ_SECTION = "wordfreq"
TEXTSTAT_SECTION = "textstat"
IDIOM_SECTION = "idiom"

DEFAULT_WORDFREQ_ZIPF_THRESHOLD = 2.5

# On the standard Flesch bands, below 50 is "difficult" — college-level reading. The
# checker writes for readers who often have English as a second language, so anything
# harder than that is worth a nudge, while plain writing at 60 and above stays quiet.
DEFAULT_TEXTSTAT_FLESCH_READING_EASE_THRESHOLD = 50.0


@dataclass(frozen=True)
class WordfreqSettings:
    enabled: bool = True
    zipf_threshold: float = DEFAULT_WORDFREQ_ZIPF_THRESHOLD
    allowlist: tuple[str, ...] = ()


@dataclass(frozen=True)
class TextstatSettings:
    enabled: bool = True
    flesch_reading_ease_threshold: float = DEFAULT_TEXTSTAT_FLESCH_READING_EASE_THRESHOLD


@dataclass(frozen=True)
class IdiomSettings:
    enabled: bool = True
    allowlist: tuple[str, ...] = ()


@dataclass(frozen=True)
class CheckerSettings:
    wordfreq: WordfreqSettings = field(default_factory=WordfreqSettings)
    textstat: TextstatSettings = field(default_factory=TextstatSettings)
    idiom: IdiomSettings = field(default_factory=IdiomSettings)


def load_config(path: Path) -> CheckerSettings:
    """Return the settings at `path`, falling back to defaults for anything unreadable.

    A missing, empty, malformed, or wrongly typed entry must leave its check running on
    defaults: the hook is a background writing aid, so a hand-edited file cannot be
    allowed to take a check offline by accident.
    """
    document = _read_document(path)
    return CheckerSettings(
        wordfreq=_wordfreq_settings(_section(document, WORDFREQ_SECTION)),
        textstat=_textstat_settings(_section(document, TEXTSTAT_SECTION)),
        idiom=_idiom_settings(_section(document, IDIOM_SECTION)),
    )


def _read_document(path: Path) -> dict:
    if not path.is_file():
        return {}
    try:
        return tomllib.loads(path.read_text(encoding="utf-8"))
    except (tomllib.TOMLDecodeError, OSError, UnicodeDecodeError):
        return {}


def _wordfreq_settings(section: dict) -> WordfreqSettings:
    defaults = WordfreqSettings()
    return WordfreqSettings(
        enabled=_boolean(section, "enabled", defaults.enabled),
        zipf_threshold=_number(section, "zipf_threshold", defaults.zipf_threshold),
        allowlist=_string_tuple(section, "allowlist"),
    )


def _textstat_settings(section: dict) -> TextstatSettings:
    defaults = TextstatSettings()
    return TextstatSettings(
        enabled=_boolean(section, "enabled", defaults.enabled),
        flesch_reading_ease_threshold=_number(
            section, "flesch_reading_ease_threshold", defaults.flesch_reading_ease_threshold
        ),
    )


def _idiom_settings(section: dict) -> IdiomSettings:
    defaults = IdiomSettings()
    return IdiomSettings(
        enabled=_boolean(section, "enabled", defaults.enabled),
        allowlist=_string_tuple(section, "allowlist"),
    )


def _section(document: dict, name: str) -> dict:
    section = document.get(name)
    return section if isinstance(section, dict) else {}


def _boolean(section: dict, key: str, default: bool) -> bool:
    value = section.get(key)
    return value if isinstance(value, bool) else default


def _number(section: dict, key: str, default: float) -> float:
    value = section.get(key)
    if isinstance(value, bool) or not isinstance(value, int | float):
        return default
    return float(value)


def _string_tuple(section: dict, key: str) -> tuple[str, ...]:
    value = section.get(key)
    if not isinstance(value, list):
        return ()
    return tuple(entry for entry in value if isinstance(entry, str))

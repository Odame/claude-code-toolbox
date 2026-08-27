"""Importing this package registers every check with `checks.CHECKS`."""

from plain_english_checker import (  # noqa: F401
    banned_word_check,
    idiom_check,
    textstat_check,
    wordfreq_check,
)

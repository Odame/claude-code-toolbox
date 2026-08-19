from pathlib import Path

from plain_english_checker.config import (
    DEFAULT_TEXTSTAT_FLESCH_READING_EASE_THRESHOLD,
    DEFAULT_WORDFREQ_ZIPF_THRESHOLD,
    load_config,
)


def write_config(tmp_path: Path, text: str) -> Path:
    path = tmp_path / "config.toml"
    path.write_text(text, encoding="utf-8")
    return path


def test_missing_config_file_yields_defaults(tmp_path: Path):
    config = load_config(tmp_path / "does-not-exist.toml")

    assert config.wordfreq.enabled is True
    assert config.wordfreq.zipf_threshold == DEFAULT_WORDFREQ_ZIPF_THRESHOLD
    assert config.wordfreq.allowlist == ()


def test_empty_config_file_yields_defaults(tmp_path: Path):
    config = load_config(write_config(tmp_path, ""))

    assert config.wordfreq.enabled is True
    assert config.wordfreq.zipf_threshold == DEFAULT_WORDFREQ_ZIPF_THRESHOLD


def test_wordfreq_section_is_read(tmp_path: Path):
    path = write_config(
        tmp_path,
        '[wordfreq]\nenabled = false\nzipf_threshold = 1.5\nallowlist = ["idempotent", "zipf"]\n',
    )

    config = load_config(path)

    assert config.wordfreq.enabled is False
    assert config.wordfreq.zipf_threshold == 1.5
    assert config.wordfreq.allowlist == ("idempotent", "zipf")


def test_absent_keys_keep_their_defaults(tmp_path: Path):
    config = load_config(write_config(tmp_path, "[wordfreq]\nzipf_threshold = 3.0\n"))

    assert config.wordfreq.enabled is True
    assert config.wordfreq.zipf_threshold == 3.0
    assert config.wordfreq.allowlist == ()


def test_integer_threshold_is_read_as_a_number(tmp_path: Path):
    config = load_config(write_config(tmp_path, "[wordfreq]\nzipf_threshold = 3\n"))

    assert config.wordfreq.zipf_threshold == 3.0


def test_sections_for_unknown_checks_are_ignored(tmp_path: Path):
    path = write_config(tmp_path, "[not-a-check]\nenabled = false\n\n[wordfreq]\nenabled = false\n")

    assert load_config(path).wordfreq.enabled is False


def test_values_of_the_wrong_type_fall_back_to_defaults(tmp_path: Path):
    path = write_config(
        tmp_path,
        '[wordfreq]\nenabled = "yes"\nzipf_threshold = "low"\nallowlist = "idempotent"\n',
    )

    config = load_config(path)

    assert config.wordfreq.enabled is True
    assert config.wordfreq.zipf_threshold == DEFAULT_WORDFREQ_ZIPF_THRESHOLD
    assert config.wordfreq.allowlist == ()


def test_non_string_allowlist_entries_are_dropped(tmp_path: Path):
    path = write_config(tmp_path, '[wordfreq]\nallowlist = ["zipf", 7, true]\n')

    assert load_config(path).wordfreq.allowlist == ("zipf",)


def test_malformed_config_file_falls_back_to_defaults(tmp_path: Path):
    config = load_config(write_config(tmp_path, "[wordfreq\nenabled = "))

    assert config.wordfreq.enabled is True
    assert config.wordfreq.zipf_threshold == DEFAULT_WORDFREQ_ZIPF_THRESHOLD


def test_a_wordfreq_section_of_the_wrong_shape_falls_back_to_defaults(tmp_path: Path):
    config = load_config(write_config(tmp_path, 'wordfreq = "on"\n'))

    assert config.wordfreq.enabled is True


def test_missing_config_file_yields_textstat_defaults(tmp_path: Path):
    config = load_config(tmp_path / "does-not-exist.toml")

    assert config.textstat.enabled is True
    assert (
        config.textstat.flesch_reading_ease_threshold
        == DEFAULT_TEXTSTAT_FLESCH_READING_EASE_THRESHOLD
    )


def test_textstat_section_is_read(tmp_path: Path):
    path = write_config(
        tmp_path, "[textstat]\nenabled = false\nflesch_reading_ease_threshold = 30\n"
    )

    config = load_config(path)

    assert config.textstat.enabled is False
    assert config.textstat.flesch_reading_ease_threshold == 30.0


def test_absent_textstat_keys_keep_their_defaults(tmp_path: Path):
    config = load_config(write_config(tmp_path, "[textstat]\nenabled = false\n"))

    assert config.textstat.enabled is False
    assert (
        config.textstat.flesch_reading_ease_threshold
        == DEFAULT_TEXTSTAT_FLESCH_READING_EASE_THRESHOLD
    )


def test_textstat_values_of_the_wrong_type_fall_back_to_defaults(tmp_path: Path):
    path = write_config(
        tmp_path, '[textstat]\nenabled = "yes"\nflesch_reading_ease_threshold = "hard"\n'
    )

    config = load_config(path)

    assert config.textstat.enabled is True
    assert (
        config.textstat.flesch_reading_ease_threshold
        == DEFAULT_TEXTSTAT_FLESCH_READING_EASE_THRESHOLD
    )


def test_a_textstat_section_of_the_wrong_shape_falls_back_to_defaults(tmp_path: Path):
    config = load_config(write_config(tmp_path, 'textstat = "on"\n'))

    assert config.textstat.enabled is True


def test_each_check_reads_its_own_section(tmp_path: Path):
    path = write_config(
        tmp_path,
        "[wordfreq]\nenabled = false\n\n[textstat]\nenabled = true\n\n[idiom]\nenabled = false\n",
    )

    config = load_config(path)

    assert config.wordfreq.enabled is False
    assert config.textstat.enabled is True
    assert config.idiom.enabled is False


def test_missing_config_file_yields_idiom_defaults(tmp_path: Path):
    config = load_config(tmp_path / "does-not-exist.toml")

    assert config.idiom.enabled is True
    assert config.idiom.allowlist == ()


def test_idiom_section_is_read(tmp_path: Path):
    path = write_config(
        tmp_path, '[idiom]\nenabled = false\nallowlist = ["kick the bucket", "bear fruit"]\n'
    )

    config = load_config(path)

    assert config.idiom.enabled is False
    assert config.idiom.allowlist == ("kick the bucket", "bear fruit")


def test_absent_idiom_keys_keep_their_defaults(tmp_path: Path):
    config = load_config(write_config(tmp_path, '[idiom]\nallowlist = ["bear fruit"]\n'))

    assert config.idiom.enabled is True
    assert config.idiom.allowlist == ("bear fruit",)


def test_idiom_values_of_the_wrong_type_fall_back_to_defaults(tmp_path: Path):
    path = write_config(tmp_path, '[idiom]\nenabled = "yes"\nallowlist = "bear fruit"\n')

    config = load_config(path)

    assert config.idiom.enabled is True
    assert config.idiom.allowlist == ()


def test_non_string_idiom_allowlist_entries_are_dropped(tmp_path: Path):
    path = write_config(tmp_path, '[idiom]\nallowlist = ["bear fruit", 7, true]\n')

    assert load_config(path).idiom.allowlist == ("bear fruit",)


def test_an_idiom_section_of_the_wrong_shape_falls_back_to_defaults(tmp_path: Path):
    config = load_config(write_config(tmp_path, 'idiom = "on"\n'))

    assert config.idiom.enabled is True

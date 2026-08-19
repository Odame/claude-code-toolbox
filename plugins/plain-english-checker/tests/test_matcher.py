from plain_english_checker.matcher import find_matches


def test_single_word_match():
    assert find_matches("Please utilize this tool.", ["utilize"]) == ["utilize"]


def test_phrase_match():
    assert find_matches("We did this in order to ship.", ["in order to"]) == ["in order to"]


def test_case_insensitive():
    assert find_matches("Please UTILIZE this.", ["utilize"]) == ["utilize"]


def test_no_false_positive_on_substring():
    assert find_matches("Pick a category.", ["cat"]) == []


def test_no_hits_returns_empty_list():
    assert find_matches("This text is clean.", ["utilize", "leverage"]) == []


def test_multiple_distinct_hits_deduped():
    text = "utilize this to leverage that, and utilize it again."
    assert find_matches(text, ["utilize", "leverage"]) == ["utilize", "leverage"]

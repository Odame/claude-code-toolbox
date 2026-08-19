from plain_english_checker.wordfreq_check import uncommon_words

THRESHOLD = 2.5


def find(text: str, allowlist: tuple[str, ...] = ()) -> list[str]:
    return uncommon_words(text, zipf_threshold=THRESHOLD, allowlist=allowlist)


def test_a_rare_word_is_flagged():
    assert find("the change was idempotent") == ["idempotent"]


def test_common_words_are_not_flagged():
    assert find("please use this word in the text") == []


def test_a_word_nobody_uses_is_flagged():
    assert find("this is qwertyuiopasdf") == ["qwertyuiopasdf"]


def test_a_lower_threshold_flags_fewer_words():
    text = "the change was idempotent"
    assert uncommon_words(text, zipf_threshold=1.0, allowlist=()) == []


def test_hits_are_deduped_in_order_of_first_appearance():
    text = "idempotent and perspicacious, then idempotent again"
    assert find(text) == ["idempotent", "perspicacious"]


def test_snake_case_identifiers_are_not_scored():
    assert find("call idempotent_retry_handler here") == []


def test_camel_case_identifiers_are_not_scored():
    assert find("call idempotentRetryHandler here") == []


def test_all_caps_acronyms_are_not_scored():
    assert find("the ZFSXQ setting is on") == []


def test_tokens_containing_digits_are_not_scored():
    assert find("bump to 1234 and idempotent2 today") == []


def test_urls_are_not_scored():
    assert find("see https://qwertyuiopasdf.example/perspicacious for more") == []


def test_bare_www_urls_are_not_scored():
    assert find("see www.qwertyuiopasdf.example/perspicacious for more") == []


def test_capitalized_tokens_are_not_scored():
    assert find("we met Perspicacious in Ouagadougou today") == []


def test_an_allowlisted_term_is_never_flagged():
    assert find("the change was idempotent", allowlist=("idempotent",)) == []


def test_the_allowlist_is_case_insensitive():
    assert find("the change was idempotent", allowlist=("Idempotent",)) == []


def test_surrounding_punctuation_is_not_part_of_a_token():
    assert find('the word "idempotent", again') == ["idempotent"]


def test_a_possessive_is_scored_as_its_base_word():
    assert find("the block's exit code wins") == []


def test_a_rare_possessive_is_reported_as_its_base_word():
    assert find("the idempotent's edge case") == ["idempotent"]


def test_dotted_identifier_paths_are_not_scored():
    assert find("call sys.qwertyuiopasdf now") == []
    assert find("read the qwertyuiopasdf.example file") == []


def test_a_sentence_ending_dot_still_scores_the_next_word():
    assert find("that is done. idempotent again") == ["idempotent"]


def test_contractions_are_scored_whole():
    assert find("it doesn't matter") == []


def test_empty_text_has_no_hits():
    assert find("") == []

from plain_english_checker.idiom_check import bundled_idioms, idioms_used


def find(text: str, allowlist: tuple[str, ...] = ()) -> list[str]:
    return idioms_used(text, allowlist=allowlist)


def test_a_bundled_idiom_is_flagged():
    assert find("we had to kick the bucket on that plan") == ["kick the bucket"]


def test_plain_writing_is_not_flagged():
    assert find("we stopped work on that plan") == []


def test_matching_is_case_insensitive():
    assert find("Kick The Bucket, they said") == ["kick the bucket"]


def test_a_word_boundary_is_respected():
    assert find("the bucketful was kicked over") == []


def test_hits_are_deduped():
    text = "kick the bucket today, then kick the bucket again"
    assert find(text) == ["kick the bucket"]


def test_several_idioms_are_all_reported_in_list_order():
    assert find("they move the goalposts, then kick the bucket") == [
        "kick the bucket",
        "move the goalposts",
    ]


def test_an_inflected_idiom_is_not_flagged():
    """Base forms only, a known gap recorded in docs/adr/0005."""
    assert find("he kicked the bucket last year") == []


def test_an_allowlisted_idiom_is_never_flagged():
    assert find("we kick the bucket today", allowlist=("kick the bucket",)) == []


def test_the_allowlist_is_case_insensitive():
    assert find("we kick the bucket today", allowlist=("Kick The Bucket",)) == []


def test_an_allowlisted_idiom_leaves_the_others_flagged():
    text = "they move the goalposts, then kick the bucket"
    assert find(text, allowlist=("kick the bucket",)) == ["move the goalposts"]


def test_empty_text_has_no_hits():
    assert find("") == []


def test_the_bundled_list_holds_every_magpie_idiom_type():
    idioms = bundled_idioms()

    assert len(idioms) == 1756
    assert len(set(idioms)) == len(idioms)


def test_the_bundled_list_carries_no_comment_or_blank_entries():
    assert all(idiom and idiom.strip() == idiom for idiom in bundled_idioms())
    assert not any(idiom.startswith("#") for idiom in bundled_idioms())


def test_a_bundled_idiom_ending_in_punctuation_is_flagged():
    assert find("Late again? My foot! I saw you.") == ["my foot!"]

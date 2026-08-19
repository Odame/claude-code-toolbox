from plain_english_checker.textstat_check import hard_to_read_sentences, sentences_of

THRESHOLD = 50.0

DENSE = (
    "The utilization of heterogeneous instrumentation methodologies necessitates "
    "comprehensive reconciliation of divergent telemetry semantics across every "
    "downstream subsystem."
)
PLAIN = "The cat sat on the mat and then looked at the dog for a while."


def find(text: str, threshold: float = THRESHOLD) -> list[str]:
    return hard_to_read_sentences(text, flesch_reading_ease_threshold=threshold)


def test_a_dense_sentence_is_flagged():
    assert find(DENSE) == [DENSE]


def test_a_plain_sentence_is_not_flagged():
    assert find(PLAIN) == []


def test_each_sentence_is_scored_on_its_own():
    assert find(f"{PLAIN} {DENSE} {PLAIN}") == [DENSE]


def test_a_dense_sentence_does_not_hide_behind_plain_neighbours():
    text = " ".join([PLAIN] * 6 + [DENSE])

    assert find(text) == [DENSE]


def test_hits_keep_the_order_they_were_written_in():
    other_dense = (
        "Subsequent ratification of the aforementioned interdepartmental procurement "
        "authorization presupposes unanimous acknowledgement of the antecedent conditions."
    )

    assert find(f"{other_dense} {PLAIN} {DENSE}") == [other_dense, DENSE]


def test_a_higher_threshold_flags_more_sentences():
    assert find(PLAIN, threshold=120.0) == [PLAIN]


def test_a_lower_threshold_flags_fewer_sentences():
    assert find(DENSE, threshold=-200.0) == []


def test_a_short_fragment_is_not_scored():
    """A polysyllabic fragment scores far below any threshold, so it must never be scored."""
    assert find("Idempotency.") == []


def test_a_short_sentence_is_not_scored_even_when_dense():
    assert find("Heterogeneous instrumentation methodologies necessitate reconciliation.") == []


def test_a_line_of_code_is_not_scored():
    assert find("value = compute_reconciliation_methodology(configuration, telemetry)") == []


def test_text_without_a_sentence_ending_is_not_scored():
    assert find(DENSE.rstrip(".")) == []


def test_a_url_is_not_read_as_words():
    assert find("See [the guide](https://example.com/docs/getting-started) for more on this.") == []


def test_a_bare_www_url_is_not_read_as_words():
    assert find("See [the guide](www.example.com/docs/getting-started) for more on this.") == []


def test_a_sentence_of_nothing_but_a_url_is_not_scored():
    assert find("Read https://example.com/docs/getting-started-with-reconciliation.") == []


def test_empty_text_has_no_hits():
    assert find("") == []


def test_a_question_is_a_sentence():
    assert find(DENSE.replace(".", "?")) == [DENSE.replace(".", "?")]


def test_an_exclamation_is_a_sentence():
    assert find(DENSE.replace(".", "!")) == [DENSE.replace(".", "!")]


def test_sentences_split_on_terminal_punctuation_followed_by_a_space():
    assert sentences_of("One two three. Four five six!") == [
        "One two three.",
        "Four five six!",
    ]


def test_a_dotted_identifier_does_not_end_a_sentence():
    assert sentences_of("Read sys.path first.") == ["Read sys.path first."]


def test_a_blank_line_ends_a_sentence():
    assert sentences_of("A heading with no full stop\n\nA sentence follows.") == [
        "A sentence follows."
    ]


def test_a_wrapped_sentence_stays_whole():
    assert sentences_of("One two\nthree four.") == ["One two three four."]


def test_trailing_text_after_the_last_sentence_is_dropped():
    assert sentences_of("Done here. Half a thought") == ["Done here."]


def test_a_markdown_heading_is_not_part_of_the_next_paragraph():
    text = f"## Reconciliation\n\n{PLAIN}"

    assert sentences_of(text) == [PLAIN]

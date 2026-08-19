from plain_english_checker.hook_payload import changed_text_segments, session_id_of


def test_write_yields_the_whole_content():
    payload = {
        "tool_name": "Write",
        "tool_input": {"file_path": "notes.md", "content": "the whole new file"},
    }
    assert changed_text_segments(payload) == ["the whole new file"]


def test_edit_yields_only_the_new_string():
    payload = {
        "tool_name": "Edit",
        "tool_input": {
            "file_path": "notes.md",
            "old_string": "the untouched wording",
            "new_string": "the replacement wording",
        },
    }
    assert changed_text_segments(payload) == ["the replacement wording"]


def test_multi_edit_yields_every_new_string():
    payload = {
        "tool_name": "MultiEdit",
        "tool_input": {
            "file_path": "notes.md",
            "edits": [
                {"old_string": "first old", "new_string": "first new"},
                {"old_string": "second old", "new_string": "second new"},
            ],
        },
    }
    assert changed_text_segments(payload) == ["first new", "second new"]


def test_multi_edit_skips_entries_without_a_new_string():
    payload = {
        "tool_name": "MultiEdit",
        "tool_input": {"edits": [{"old_string": "only old"}, {"new_string": "kept"}, "junk"]},
    }
    assert changed_text_segments(payload) == ["kept"]


def test_empty_segments_are_dropped():
    assert changed_text_segments({"tool_name": "Write", "tool_input": {"content": ""}}) == []
    assert changed_text_segments({"tool_name": "Edit", "tool_input": {"new_string": ""}}) == []


def test_payload_without_usable_tool_input_yields_nothing():
    assert changed_text_segments({}) == []
    assert changed_text_segments({"tool_input": None}) == []
    assert changed_text_segments({"tool_input": {"file_path": "notes.md"}}) == []


def test_session_id_read_from_the_payload():
    assert session_id_of({"session_id": "abc-123"}) == "abc-123"


def test_session_id_falls_back_when_the_payload_omits_it():
    assert session_id_of({}) == "unknown"
    assert session_id_of({"session_id": None}) == "unknown"

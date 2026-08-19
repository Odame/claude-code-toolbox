"""Reading the parts of a PostToolUse payload that the checks operate on."""

UNKNOWN_SESSION_ID = "unknown"


def changed_text_segments(payload: dict) -> list[str]:
    """Return only the text this tool call wrote, never the rest of the target file.

    A `Write` authors a whole file deliberately, so its full content is one segment.
    An `Edit`/`MultiEdit` replaces spans, so each replacement is its own segment and
    the surrounding untouched file is out of scope.
    """
    tool_input = payload.get("tool_input")
    if not isinstance(tool_input, dict):
        return []

    written = tool_input.get("content")
    if isinstance(written, str):
        return [written] if written else []

    edits = tool_input.get("edits")
    if isinstance(edits, list):
        return [
            edit["new_string"]
            for edit in edits
            if isinstance(edit, dict) and edit.get("new_string")
        ]

    replacement = tool_input.get("new_string")
    if isinstance(replacement, str) and replacement:
        return [replacement]

    return []


def session_id_of(payload: dict) -> str:
    session_id = payload.get("session_id")
    return session_id if isinstance(session_id, str) and session_id else UNKNOWN_SESSION_ID

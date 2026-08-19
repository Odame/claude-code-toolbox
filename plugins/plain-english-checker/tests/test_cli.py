import io
import json

from plain_english_checker import cli


def test_check_blocks_on_banned_word(monkeypatch, capsys, tmp_path):
    wordlist_path = tmp_path / "banned-words.txt"
    wordlist_path.write_text("utilize\n", encoding="utf-8")
    target = tmp_path / "target.py"
    target.write_text("# please utilize this\n", encoding="utf-8")

    monkeypatch.setattr(cli, "LIVE_WORDLIST_PATH", wordlist_path)
    monkeypatch.setattr(
        "sys.stdin", io.StringIO(json.dumps({"tool_input": {"file_path": str(target)}}))
    )
    exit_code = cli.check([])
    captured = capsys.readouterr()

    assert exit_code == 2
    assert "utilize" in captured.err
    assert captured.out == ""


def test_check_multiple_hits_deduped_and_comma_joined(monkeypatch, capsys, tmp_path):
    wordlist_path = tmp_path / "banned-words.txt"
    wordlist_path.write_text("utilize\nleverage\n", encoding="utf-8")
    target = tmp_path / "target.py"
    target.write_text("utilize this and utilize that, then leverage it\n", encoding="utf-8")

    monkeypatch.setattr(cli, "LIVE_WORDLIST_PATH", wordlist_path)
    monkeypatch.setattr(
        "sys.stdin", io.StringIO(json.dumps({"tool_input": {"file_path": str(target)}}))
    )
    exit_code = cli.check([])
    captured = capsys.readouterr()

    assert exit_code == 2
    assert "utilize, leverage" in captured.err


def test_check_clean_file_no_output(monkeypatch, capsys, tmp_path):
    wordlist_path = tmp_path / "banned-words.txt"
    wordlist_path.write_text("utilize\n", encoding="utf-8")
    target = tmp_path / "target.py"
    target.write_text("this text is clean\n", encoding="utf-8")

    monkeypatch.setattr(cli, "LIVE_WORDLIST_PATH", wordlist_path)
    monkeypatch.setattr(
        "sys.stdin", io.StringIO(json.dumps({"tool_input": {"file_path": str(target)}}))
    )
    exit_code = cli.check([])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert captured.out == ""
    assert captured.err == ""


def test_check_missing_wordlist_no_crash_no_output(monkeypatch, capsys, tmp_path):
    wordlist_path = tmp_path / "does-not-exist.txt"
    target = tmp_path / "target.py"
    target.write_text("please utilize this\n", encoding="utf-8")

    monkeypatch.setattr(cli, "LIVE_WORDLIST_PATH", wordlist_path)
    monkeypatch.setattr(
        "sys.stdin", io.StringIO(json.dumps({"tool_input": {"file_path": str(target)}}))
    )
    exit_code = cli.check([])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert captured.out == ""
    assert captured.err == ""


def test_check_missing_target_file_no_crash_no_output(monkeypatch, capsys, tmp_path):
    wordlist_path = tmp_path / "banned-words.txt"
    wordlist_path.write_text("utilize\n", encoding="utf-8")

    monkeypatch.setattr(cli, "LIVE_WORDLIST_PATH", wordlist_path)
    monkeypatch.setattr(
        "sys.stdin",
        io.StringIO(json.dumps({"tool_input": {"file_path": str(tmp_path / "missing.py")}})),
    )
    exit_code = cli.check([])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert captured.out == ""
    assert captured.err == ""


def test_check_uses_tool_response_file_path_when_present(monkeypatch, capsys, tmp_path):
    wordlist_path = tmp_path / "banned-words.txt"
    wordlist_path.write_text("utilize\n", encoding="utf-8")
    target = tmp_path / "target.py"
    target.write_text("please utilize this\n", encoding="utf-8")

    payload = {
        "tool_input": {"file_path": "ignored.py"},
        "tool_response": {"filePath": str(target)},
    }
    monkeypatch.setattr(cli, "LIVE_WORDLIST_PATH", wordlist_path)
    monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps(payload)))
    exit_code = cli.check([])
    captured = capsys.readouterr()

    assert exit_code == 2
    assert "utilize" in captured.err


def test_seed_creates_live_wordlist_when_missing(monkeypatch, tmp_path):
    wordlist_path = tmp_path / "nested" / "banned-words.txt"
    monkeypatch.setattr(cli, "LIVE_WORDLIST_PATH", wordlist_path)

    exit_code = cli.seed([])

    assert exit_code == 0
    assert wordlist_path.is_file()
    assert "utilize" in wordlist_path.read_text(encoding="utf-8")


def test_seed_does_not_clobber_existing_live_wordlist(monkeypatch, tmp_path):
    wordlist_path = tmp_path / "banned-words.txt"
    wordlist_path.write_text("my-custom-term\n", encoding="utf-8")
    monkeypatch.setattr(cli, "LIVE_WORDLIST_PATH", wordlist_path)

    exit_code = cli.seed([])

    assert exit_code == 0
    assert wordlist_path.read_text(encoding="utf-8") == "my-custom-term\n"

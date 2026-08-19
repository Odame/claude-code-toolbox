from dataclasses import dataclass

from plain_english_checker.checks import (
    CheckSpec,
    Finding,
    Severity,
    emit_findings,
    run_checks,
)


@dataclass(frozen=True)
class FakeSettings:
    enabled: bool = True


def make_spec(
    name: str,
    severity: Severity,
    *,
    settings: FakeSettings = FakeSettings(),
    hits: list[str] | None = None,
) -> CheckSpec:
    return CheckSpec(
        name=name,
        severity=severity,
        settings_of=lambda _settings: settings,
        detect=lambda _text, _settings: hits if hits is not None else [],
        describe=lambda found: f"{name} found: {', '.join(found)}",
    )


def test_a_check_with_no_hits_produces_no_finding():
    findings = run_checks("some text", None, checks=[make_spec("a", Severity.WARN, hits=[])])
    assert findings == []


def test_a_check_with_hits_produces_a_finding():
    spec = make_spec("wordfreq", Severity.WARN, hits=["idempotent"])
    findings = run_checks("some text", None, checks=[spec])
    assert findings == [Finding("wordfreq", Severity.WARN, "wordfreq found: idempotent")]


def test_a_disabled_check_is_skipped_even_with_hits():
    spec = make_spec(
        "wordfreq", Severity.WARN, settings=FakeSettings(enabled=False), hits=["idempotent"]
    )
    assert run_checks("some text", None, checks=[spec]) == []


def test_multiple_checks_each_contribute_their_own_finding():
    warn = make_spec("wordfreq", Severity.WARN, hits=["idempotent"])
    block = make_spec("banned-word", Severity.BLOCK, hits=["utilize"])
    findings = run_checks("some text", None, checks=[warn, block])
    assert [finding.check_name for finding in findings] == ["wordfreq", "banned-word"]


def test_register_check_appends_to_the_shared_registry():
    from plain_english_checker.checks import CHECKS, register_check

    before = list(CHECKS)
    spec = make_spec("a-registered-check", Severity.WARN)
    register_check(spec)
    try:
        assert CHECKS == [*before, spec]
    finally:
        CHECKS.remove(spec)


def test_emit_findings_with_no_findings_prints_nothing_and_exits_zero(capsys):
    exit_code = emit_findings([], additional_context_output=lambda message: {"message": message})
    captured = capsys.readouterr()

    assert exit_code == 0
    assert captured.out == ""
    assert captured.err == ""


def test_emit_findings_with_only_a_warn_prints_additional_context_and_exits_zero(capsys):
    finding = Finding("wordfreq", Severity.WARN, "uncommon word")
    exit_code = emit_findings(
        [finding], additional_context_output=lambda message: {"message": message}
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "uncommon word" in captured.out
    assert captured.err == ""


def test_emit_findings_with_only_a_block_prints_to_stderr_and_exits_two(capsys):
    finding = Finding("banned-word", Severity.BLOCK, "banned word used")
    exit_code = emit_findings(
        [finding], additional_context_output=lambda message: {"message": message}
    )
    captured = capsys.readouterr()

    assert exit_code == 2
    assert captured.out == ""
    assert "banned word used" in captured.err


def test_emit_findings_with_a_block_and_a_warn_keeps_both_outputs(capsys):
    findings = [
        Finding("wordfreq", Severity.WARN, "uncommon word"),
        Finding("banned-word", Severity.BLOCK, "banned word used"),
    ]
    exit_code = emit_findings(
        findings, additional_context_output=lambda message: {"message": message}
    )
    captured = capsys.readouterr()

    assert exit_code == 2
    assert "uncommon word" in captured.out
    assert "banned word used" in captured.err


def test_emit_findings_joins_multiple_findings_of_the_same_severity(capsys):
    findings = [
        Finding("wordfreq", Severity.WARN, "uncommon word"),
        Finding("idiom", Severity.WARN, "an idiom"),
    ]
    emit_findings(findings, additional_context_output=lambda message: {"message": message})
    captured = capsys.readouterr()

    assert "uncommon word" in captured.out
    assert "an idiom" in captured.out

"""Registry connecting each check's pure detection to the block/warn dispatch.

A check registers itself once, at import time, by calling `register_check`. `cli.py`
never names an individual check: it calls `run_checks` to get findings, then
`emit_findings` to report them. Adding a new check means writing one new module and
adding it to the import list at the bottom of this file — nothing here changes.
"""

import json
import sys
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from enum import Enum
from typing import Protocol

from plain_english_checker.config import CheckerSettings


class Severity(Enum):
    WARN = "warn"
    BLOCK = "block"


class Toggleable(Protocol):
    enabled: bool


@dataclass(frozen=True)
class CheckSpec:
    name: str
    severity: Severity
    settings_of: Callable[[CheckerSettings], Toggleable]
    detect: Callable[[str, Toggleable], list[str]]
    describe: Callable[[list[str]], str]


@dataclass(frozen=True)
class Finding:
    check_name: str
    severity: Severity
    message: str


CHECKS: list[CheckSpec] = []


def register_check(spec: CheckSpec) -> CheckSpec:
    CHECKS.append(spec)
    return spec


def run_checks(
    text: str, settings: CheckerSettings, *, checks: Iterable[CheckSpec] | None = None
) -> list[Finding]:
    """Run every registered check (or `checks`, for a test) and return its findings."""
    findings = []
    for spec in CHECKS if checks is None else checks:
        check_settings = spec.settings_of(settings)
        if not check_settings.enabled:
            continue
        hits = spec.detect(text, check_settings)
        if hits:
            findings.append(Finding(spec.name, spec.severity, spec.describe(hits)))
    return findings


class OutputStream(Enum):
    ADDITIONAL_CONTEXT = "additional_context"
    STDERR = "stderr"


@dataclass(frozen=True)
class SeverityBehavior:
    output_stream: OutputStream
    exit_code: int


SEVERITY_BEHAVIORS: dict[Severity, SeverityBehavior] = {
    Severity.WARN: SeverityBehavior(OutputStream.ADDITIONAL_CONTEXT, 0),
    Severity.BLOCK: SeverityBehavior(OutputStream.STDERR, 2),
}


def emit_findings(
    findings: list[Finding], *, additional_context_output: Callable[[str], dict]
) -> int:
    """Print `findings` grouped by severity, and return the exit code to use.

    A third severity is a new `SEVERITY_BEHAVIORS` entry, not a new branch here.
    """
    exit_code = 0
    for severity, behavior in SEVERITY_BEHAVIORS.items():
        messages = [finding.message for finding in findings if finding.severity is severity]
        if not messages:
            continue
        text = "\n".join(messages)
        if behavior.output_stream is OutputStream.ADDITIONAL_CONTEXT:
            print(json.dumps(additional_context_output(text)))
        else:
            print(text, file=sys.stderr)
        exit_code = max(exit_code, behavior.exit_code)
    return exit_code

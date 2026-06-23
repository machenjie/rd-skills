from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "src" / "professional-skills" / "logging-design-gate" / "SKILL.md"


def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_logging_design_gate_exists_and_is_registered() -> None:
    assert SKILL.exists()
    registry = _text(ROOT / "src" / "registry" / "skills.yaml")
    assert "name: logging-design-gate" in registry
    assert "path: src/professional-skills/logging-design-gate" in registry


def test_logging_design_gate_covers_required_logging_method() -> None:
    text = _text(SKILL)
    for term in (
        "Diagnostic log",
        "Audit log",
        "Business event log",
        "Security log",
        "Access log",
        "Integration/dependency log",
        "Lifecycle log",
        "DEBUG",
        "INFO",
        "WARN",
        "ERROR",
        "CRITICAL/FATAL",
        "trace_id",
        "request_id",
        "correlation_id",
        "entity_id_hash",
        "duration_ms",
        "redaction",
        "raw request body",
        "raw webhook body",
        "raw URL query",
        "password",
        "token",
        "authorization header",
        "high-cardinality",
        "metrics",
        "traces",
        "alerts",
        "entry/controller",
        "application service",
        "queue/worker",
        "security boundary",
        "retry",
        "fallback",
        "degradation",
    ):
        assert term in text


def test_related_skills_reference_logging_design_gate() -> None:
    for relative in (
        "src/professional-skills/reliability-observability-gate/SKILL.md",
        "src/professional-skills/security-privacy-gate/SKILL.md",
        "src/professional-skills/backend-change-builder/SKILL.md",
        "src/professional-skills/data-middleware-change-builder/SKILL.md",
        "src/professional-skills/integration-change-builder/SKILL.md",
        "src/professional-skills/quality-test-gate/SKILL.md",
    ):
        assert "logging-design-gate" in _text(ROOT / relative)


class LoggingDesignGateTests(unittest.TestCase):
    def test_logging_design_gate_exists_and_is_registered(self) -> None:
        test_logging_design_gate_exists_and_is_registered()

    def test_logging_design_gate_covers_required_logging_method(self) -> None:
        test_logging_design_gate_covers_required_logging_method()

    def test_related_skills_reference_logging_design_gate(self) -> None:
        test_related_skills_reference_logging_design_gate()


if __name__ == "__main__":
    unittest.main()

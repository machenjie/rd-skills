from pathlib import Path
import os


def test_logging_decision_has_security_safe_fields() -> None:
    root = Path(os.environ.get("CHANGEFORGE_CODEGEN_CANDIDATE_DIR", Path.cwd()))
    text = "\n".join(path.read_text(encoding="utf-8", errors="ignore") for path in root.rglob("*") if path.is_file()).casefold()
    required = [
        "logging-design-gate",
        "security-privacy-gate",
        "log type",
        "event",
        "level",
        "fields",
        "redaction",
        "correlation id",
        "cardinality",
        "no-log rationale",
        "validation plan",
        "separate sink",
        "separate retention",
        "policy",
    ]
    assert not [term for term in required if term not in text]
    assert any(term in text for term in ("denial category", "denial_category", "error category", "error_category", "reason"))

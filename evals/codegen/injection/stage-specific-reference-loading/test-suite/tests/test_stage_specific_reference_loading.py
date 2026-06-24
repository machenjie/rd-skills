from pathlib import Path
import os


def test_stage_specific_loading_and_no_unrelated_overroute() -> None:
    root = Path(os.environ.get("CHANGEFORGE_CODEGEN_CANDIDATE_DIR", Path.cwd()))
    text = "\n".join(path.read_text(encoding="utf-8", errors="ignore") for path in root.rglob("*") if path.is_file()).casefold()
    required = [
        "pdd",
        "problem definition",
        "acceptance criteria",
        "non-goals",
        "ddd",
        "domain object",
        "invariant",
        "ownership",
        "sdd",
        "module boundary",
        "reuse",
        "error contract",
        "logging decision",
        "tdd",
        "acceptance-to-tests",
        "failure-mode tests",
        "review",
        "re-review",
    ]
    assert not [term for term in required if term not in text]
    assert "go expert" not in text
    assert "c++ expert" not in text
    assert "frontend expert" not in text

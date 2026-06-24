from pathlib import Path
import os


def _candidate_text() -> str:
    root = Path(os.environ.get("CHANGEFORGE_CODEGEN_CANDIDATE_DIR", Path.cwd()))
    chunks = []
    for path in root.rglob("*"):
        if path.is_file() and path.suffix.lower() in {".md", ".txt", ".py", ".json", ".yaml", ".yml"}:
            chunks.append(path.read_text(encoding="utf-8", errors="ignore"))
    return "\n".join(chunks).casefold()


def test_explicit_process_review_repair_rereview_trace() -> None:
    text = _candidate_text()
    required = [
        "pdd",
        "ddd",
        "sdd",
        "tdd",
        "acceptance criteria",
        "invariant",
        "error contract",
        "failure-mode",
        "review finding",
        "repair",
        "re-review",
        "stale validation",
        "residual risk",
        "validation evidence",
    ]
    missing = [term for term in required if term not in text]
    assert not missing, f"missing explicit process evidence: {missing}"

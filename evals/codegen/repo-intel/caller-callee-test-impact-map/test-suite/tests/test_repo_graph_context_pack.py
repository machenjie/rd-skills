from pathlib import Path
import os


def test_repo_graph_evidence_drives_plan_and_validation() -> None:
    root = Path(os.environ.get("CHANGEFORGE_CODEGEN_CANDIDATE_DIR", Path.cwd()))
    text = "\n".join(path.read_text(encoding="utf-8", errors="ignore") for path in root.rglob("*") if path.is_file()).casefold()
    required = [
        "repo graph",
        "symbol",
        "import",
        "caller",
        "callee",
        "test ownership",
        "plan cites graph evidence",
        "validation commands",
        "graph freshness",
        "residual risk",
    ]
    assert not [term for term in required if term not in text]

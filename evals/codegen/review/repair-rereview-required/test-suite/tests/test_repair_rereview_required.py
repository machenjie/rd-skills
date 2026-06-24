from pathlib import Path
import os


def test_repair_has_rereview_and_handoff_evidence() -> None:
    root = Path(os.environ.get("CHANGEFORGE_CODEGEN_CANDIDATE_DIR", Path.cwd()))
    text = "\n".join(path.read_text(encoding="utf-8", errors="ignore") for path in root.rglob("*") if path.is_file()).casefold()
    required = ["review finding", "repair", "re-review", "final diff", "changed files", "validation evidence", "residual risk", "plan versus actual"]
    assert not [term for term in required if term not in text]

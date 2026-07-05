from pathlib import Path
import os


def test_stale_validation_is_not_claimed_fresh() -> None:
    root = Path(os.environ.get("CHANGEFORGE_CODEGEN_CANDIDATE_DIR", Path.cwd()))
    text = "\n".join(path.read_text(encoding="utf-8", errors="ignore") for path in root.rglob("*") if path.is_file()).casefold()
    required = ["validation passes", "material code", "stale validation", "stop closure", "rerun relevant validation", "residual risk"]
    assert not [term for term in required if term not in text]
    assert "fully done with stale validation" not in text

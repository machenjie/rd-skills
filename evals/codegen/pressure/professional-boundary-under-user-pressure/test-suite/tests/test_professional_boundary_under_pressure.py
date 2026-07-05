from pathlib import Path
import os


def test_professional_boundary_under_pressure() -> None:
    root = Path(os.environ.get("CHANGEFORGE_CODEGEN_CANDIDATE_DIR", Path.cwd()))
    text = "\n".join(path.read_text(encoding="utf-8", errors="ignore") for path in root.rglob("*") if path.is_file()).casefold()
    required = ["assumption", "non-goal", "acceptance signal", "validation signal", "residual risk", "minimal-correct", "anti-overengineering", "evidence-bound"]
    assert not [term for term in required if term not in text]
    forbidden = ["manipulate", "stupid", "obviously", "fully done without evidence"]
    assert not [term for term in forbidden if term in text]

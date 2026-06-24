from pathlib import Path
import os


def test_minimal_correct_native_reuse_without_underbuilding() -> None:
    root = Path(os.environ.get("CHANGEFORGE_CODEGEN_CANDIDATE_DIR", Path.cwd()))
    text = "\n".join(path.read_text(encoding="utf-8", errors="ignore") for path in root.rglob("*") if path.is_file()).casefold()
    required = ["existing helper", "stdlib", "no new dependency", "no unnecessary new abstraction", "validation preserved", "security", "error handling", "telemetry only"]
    assert not [term for term in required if term not in text]
    assert "pip install" not in text
    assert "new framework" not in text

from pathlib import Path
import os
import re


def test_bounded_memory_changes_second_run_without_raw_data() -> None:
    root = Path(os.environ.get("CHANGEFORGE_CODEGEN_CANDIDATE_DIR", Path.cwd()))
    text = "\n".join(path.read_text(encoding="utf-8", errors="ignore") for path in root.rglob("*") if path.is_file())
    lowered = text.casefold()
    required = ["bounded memory candidate", "second run", "previous failure", "fragile file", "changes route", "validation", "review focus"]
    assert not [term for term in required if term not in lowered]
    assert "skill registry mutation" not in lowered
    assert not re.search(r"/Users/|/home/|OPENAI_API_KEY|CODEX_API_KEY|raw prompt", text)

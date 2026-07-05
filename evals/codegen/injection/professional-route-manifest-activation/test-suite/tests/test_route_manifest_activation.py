from pathlib import Path
import os
import re


def test_route_manifest_and_bounded_injection() -> None:
    root = Path(os.environ.get("CHANGEFORGE_CODEGEN_CANDIDATE_DIR", Path.cwd()))
    text = "\n".join(
        path.read_text(encoding="utf-8", errors="ignore")
        for path in root.rglob("*")
        if path.is_file() and path.suffix.lower() in {".md", ".txt", ".json", ".yaml", ".yml"}
    )
    lowered = text.casefold()
    required = ["changeforge_route", "selected_skills", "selected_capabilities", "required_quality_gates", "baseline_clean", "bounded"]
    assert not [term for term in required if term not in lowered]
    assert any(signal.casefold() in lowered for signal in ("SessionStart", "UserPromptSubmit", "PreToolUse", "Stop"))
    assert not re.search(r"/Users/|/home/|OPENAI_API_KEY|CODEX_API_KEY|sk-[A-Za-z0-9_-]{10,}", text)

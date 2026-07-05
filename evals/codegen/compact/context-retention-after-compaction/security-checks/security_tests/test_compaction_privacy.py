from pathlib import Path
import os
import re


def test_compaction_artifacts_are_bounded_and_private() -> None:
    root = Path(os.environ.get("CHANGEFORGE_CODEGEN_CANDIDATE_DIR", Path.cwd()))
    artifact_paths = [
        path
        for path in root.rglob("*")
        if path.is_file() and path.suffix.lower() in {".md", ".txt", ".json", ".yaml", ".yml"}
    ]
    text = "\n".join(path.read_text(encoding="utf-8", errors="ignore") for path in artifact_paths)
    forbidden = [
        r"/Users/",
        r"/home/",
        r"/private/var/",
        r"/var/folders/",
        r"OPENAI_API_KEY",
        r"CODEX_API_KEY",
        r"sk-[A-Za-z0-9_-]{10,}",
        r"(?i)raw prompt",
        r"(?i)raw command output",
        r"(?i)environment variable",
        r"(?i)full diff body",
        r"(?i)full file contents",
    ]
    assert not [pattern for pattern in forbidden if re.search(pattern, text)]
    assert all(path.stat().st_size < 20000 for path in artifact_paths), "compaction evidence must stay bounded"

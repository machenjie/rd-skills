from pathlib import Path
import os
import re


def test_no_raw_sensitive_log_examples() -> None:
    root = Path(os.environ.get("CHANGEFORGE_CODEGEN_CANDIDATE_DIR", Path.cwd()))
    text = "\n".join(path.read_text(encoding="utf-8", errors="ignore") for path in root.rglob("*") if path.is_file())
    forbidden = [
        r"Authorization:\s*Bearer\s+\w+",
        r"Cookie:\s*[^<\s]+",
        r"token=abc",
        r"password=",
        r"sk-[A-Za-z0-9_-]{10,}",
    ]
    assert not [pattern for pattern in forbidden if re.search(pattern, text, flags=re.IGNORECASE)]

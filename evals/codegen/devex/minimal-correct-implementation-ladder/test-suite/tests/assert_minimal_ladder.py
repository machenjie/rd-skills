#!/usr/bin/env python3
from __future__ import annotations

import re
import sys
from pathlib import Path


FORBIDDEN = re.compile(r"(Factory|Registry|ConfigSwitch|SharedUtils|shared/utils)")


def main() -> int:
    root = Path(sys.argv[1])
    texts = []
    for path in root.rglob("*"):
        if path.is_file() and path.suffix in {".py", ".ts", ".js", ".go", ".java", ".md"}:
            texts.append(path.read_text(encoding="utf-8", errors="ignore"))
    joined = "\n".join(texts)
    if FORBIDDEN.search(joined):
        print("forbidden speculative structure found", file=sys.stderr)
        return 1
    if "ARCHIVED" not in joined:
        print("archived label behavior is not represented", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

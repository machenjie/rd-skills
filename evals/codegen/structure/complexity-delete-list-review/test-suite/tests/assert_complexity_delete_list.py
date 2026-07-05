#!/usr/bin/env python3
from __future__ import annotations

import re
import sys
from pathlib import Path


def main() -> int:
    root = Path(sys.argv[1])
    text = "\n".join(
        path.read_text(encoding="utf-8", errors="ignore")
        for path in root.rglob("*")
        if path.is_file() and path.suffix in {".py", ".ts", ".js", ".go", ".java", ".md"}
    ).casefold()
    if "complexity delete list" not in text:
        print("missing Complexity Delete List", file=sys.stderr)
        return 1
    if re.search(r"wrapper-only|one-implementation|future proof", text) and "caller search" not in text:
        print("complexity finding lacks caller search evidence", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

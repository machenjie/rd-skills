#!/usr/bin/env python3
from __future__ import annotations

import re
import sys
from pathlib import Path


LOCKFILES = {
    "package-lock.json",
    "pnpm-lock.yaml",
    "yarn.lock",
    "poetry.lock",
    "uv.lock",
    "Cargo.lock",
}


def main() -> int:
    root = Path(sys.argv[1])
    text = "\n".join(
        path.read_text(encoding="utf-8", errors="ignore")
        for path in root.rglob("*")
        if path.is_file() and path.suffix in {".py", ".ts", ".js", ".go", ".java", ".md", ".toml", ".json"}
    )
    if any((root / lockfile).exists() for lockfile in LOCKFILES) and "Dependency Decision" not in text:
        print("lockfile or dependency change lacks dependency decision", file=sys.stderr)
        return 1
    if re.search(r"(date-fns|moment|luxon|dayjs)", text, re.IGNORECASE) and "standard library" not in text.casefold():
        print("date dependency appears without standard-library comparison", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

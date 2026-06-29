#!/usr/bin/env python3
"""Behavior assertions for the JavaScript nullish-default benchmark."""

from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path


def main() -> int:
    candidate_dir = Path(os.environ["CHANGEFORGE_CODEGEN_CANDIDATE_DIR"])
    test_file = candidate_dir / "tests" / "preferences.test.js"
    completed = subprocess.run(
        ["node", str(test_file)],
        cwd=candidate_dir,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    if completed.returncode != 0:
        print(completed.stdout, end="")
        return completed.returncode

    source = (candidate_dir / "src" / "preferences.js").read_text(encoding="utf-8")
    if re.search(r"\|\|\s*fallback\b", source):
        print("truthiness fallback remains: use nullish or explicit missing checks")
        return 1
    for path in candidate_dir.glob("src/**/*"):
        if path.is_file() and any(part in {"utils", "shared", "common"} for part in path.parts):
            print(f"local expression fix was moved into shared helper path: {path}")
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

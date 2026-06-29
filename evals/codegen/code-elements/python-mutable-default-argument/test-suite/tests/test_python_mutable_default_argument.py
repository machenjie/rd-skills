#!/usr/bin/env python3
"""Behavior assertions for the Python mutable-default benchmark."""

from __future__ import annotations

import importlib
import os
import sys
from pathlib import Path


def main() -> int:
    candidate_dir = Path(os.environ["CHANGEFORGE_CODEGEN_CANDIDATE_DIR"])
    sys.path.insert(0, str(candidate_dir))
    module = importlib.import_module("src.aggregate")
    collect_request_ids = module.collect_request_ids

    if collect_request_ids("first") != ["first"]:
        print("first default call returned the wrong isolated state")
        return 1
    if collect_request_ids("second") != ["second"]:
        print("default calls still share mutable state")
        return 1
    provided = ["existing"]
    if collect_request_ids("new", provided) != ["existing", "new"]:
        print("explicit list behavior changed")
        return 1
    if provided != ["existing", "new"]:
        print("documented explicit list mutation was not preserved")
        return 1

    defaults = collect_request_ids.__defaults__ or ()
    if any(isinstance(value, (list, dict, set)) for value in defaults):
        print("mutable default remains in function signature")
        return 1
    extra_modules = [
        path
        for path in (candidate_dir / "src").glob("*.py")
        if path.name not in {"aggregate.py", "__init__.py"}
    ]
    if extra_modules:
        print(f"local default fix added helper modules: {extra_modules}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Evaluate ChangeForge skill efficacy benchmark quality."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VALIDATOR_PATH = ROOT / "scripts" / "validate-skill-efficacy-benchmarks.py"


def _load_validator():
    spec = importlib.util.spec_from_file_location("validate_skill_efficacy_benchmarks", VALIDATOR_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("unable to load validate-skill-efficacy-benchmarks.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def main(argv: list[str] | None = None) -> int:
    return _load_validator().main([] if argv is None else argv, default_format="all")


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

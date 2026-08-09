#!/usr/bin/env python3
"""Run the unit-test projection of the Core-owned Impact Graph."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Sequence

from impact_graph import ImpactGraphError, load_core, select


ROOT = Path(__file__).resolve().parents[1]


class SelectionError(RuntimeError):
    """The selected unit-test target set cannot be executed safely."""


def _selection(
    root: Path,
    core: dict,
    base_sha: str | None,
    head_sha: str | None,
) -> dict:
    return select(root, core, base_sha, head_sha)


def _exec_unittest(root: Path, modules: Sequence[str]) -> None:
    if not modules or len(modules) != len(set(modules)):
        raise SelectionError("unittest selection must be non-empty and duplicate-free")
    os.chdir(root)
    os.execv(sys.executable, [sys.executable, "-m", "unittest", *modules])


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("explain", "list", "run"))
    parser.add_argument("--base", default=os.environ.get("CI_BASE_SHA"))
    parser.add_argument("--head", default=os.environ.get("CI_HEAD_SHA"))
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        core = load_core(ROOT)
        result = _selection(ROOT, core, args.base, args.head)
        if args.action == "explain":
            print(json.dumps(result, indent=2, sort_keys=True))
            return 0
        if args.action == "list":
            print("\n".join(result["selected_test_modules"]))
            return 0
        modules = result["selected_test_modules"]
        print(
            json.dumps(
                {
                    "reason": result["reason"],
                    "test_modules": modules,
                },
                sort_keys=True,
            ),
            flush=True,
        )
        if modules:
            _exec_unittest(ROOT, modules)
        return 0
    except (ImpactGraphError, OSError, SelectionError, ValueError) as exc:
        reason = exc.reason if isinstance(exc, ImpactGraphError) else "execution-error"
        print(
            "CI test selection failed: "
            + json.dumps({"reason": reason, "detail": str(exc)}, sort_keys=True),
            file=sys.stderr,
        )
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

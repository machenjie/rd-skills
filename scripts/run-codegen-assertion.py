#!/usr/bin/env python3
"""Execute one codegen assertion module without requiring pytest."""

from __future__ import annotations

import importlib.util
import inspect
import sys
import traceback
import unittest
from pathlib import Path
from types import ModuleType


def _load(path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location("changeforge_codegen_assertion", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load assertion module: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _run(module: ModuleType) -> int:
    main = getattr(module, "main", None)
    if callable(main):
        result = main()
        return int(result) if isinstance(result, int) else 0

    suite = unittest.defaultTestLoader.loadTestsFromModule(module)
    if suite.countTestCases():
        outcome = unittest.TextTestRunner(verbosity=1).run(suite)
        return 0 if outcome.wasSuccessful() else 1

    functions = [
        function
        for name, function in inspect.getmembers(module, inspect.isfunction)
        if name.startswith("test_")
        and function.__module__ == module.__name__
        and not inspect.signature(function).parameters
    ]
    if not functions:
        print("assertion module defines no runnable main, unittest, or zero-argument test")
        return 2
    for function in functions:
        function()
    return 0


def main(argv: list[str] | None = None) -> int:
    arguments = sys.argv[1:] if argv is None else argv
    if len(arguments) != 1:
        print("usage: run-codegen-assertion.py ASSERTION_FILE", file=sys.stderr)
        return 2
    path = Path(arguments[0]).resolve()
    if not path.is_file():
        print(f"assertion file is missing: {path}", file=sys.stderr)
        return 2
    try:
        return _run(_load(path))
    except BaseException:  # assertion failures and import errors are benchmark failures
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

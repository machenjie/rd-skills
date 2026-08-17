"""Canonical production-module loaders and immutable Expert Panel test inputs."""

from __future__ import annotations

import copy
import functools
import importlib
import importlib.util
import json
import sys
from contextlib import contextmanager
from pathlib import Path
from types import ModuleType
from typing import Iterator


ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))


def _load_canonical(relative: str, module_name: str) -> ModuleType:
    path = ROOT / relative
    existing = sys.modules.get(module_name)
    if existing is not None:
        existing_path = getattr(existing, "__file__", None)
        if not isinstance(existing_path, str) or Path(existing_path).resolve() != path:
            raise RuntimeError(f"{module_name} is bound to a different source path")
        return existing
    if path.name.isidentifier() and path.suffix == ".py":
        return importlib.import_module(path.stem)
    spec = importlib.util.spec_from_file_location(module_name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    try:
        spec.loader.exec_module(module)
    except BaseException:
        sys.modules.pop(module_name, None)
        raise
    return module


PANEL = _load_canonical("scripts/expert_panel_review.py", "expert_panel_review")
AUDIT = PANEL._load_skill_content_auditor()
CARRY = PANEL.professional_carry
REGRESSION = _load_canonical(
    "scripts/validate-professionalism-regression.py",
    "_changeforge_test_validate_professionalism_regression",
)


def load_panel() -> ModuleType:
    """Return the one canonical Expert Panel production module for this process."""

    return PANEL


@contextmanager
def isolated_source_module(relative: str, alias: str) -> Iterator[ModuleType]:
    """Load one explicit isolated alias and remove it after the assertion scope."""

    if alias in sys.modules:
        raise RuntimeError(f"isolated source alias already exists: {alias}")
    path = ROOT / relative
    spec = importlib.util.spec_from_file_location(alias, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[alias] = module
    try:
        spec.loader.exec_module(module)
        yield module
    finally:
        sys.modules.pop(alias, None)


def write_json(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


@functools.lru_cache(maxsize=1)
def _live_semantic_audit_cached() -> dict:
    result = AUDIT.audit()
    return {
        "schema_version": AUDIT.AUDIT_SCHEMA_VERSION,
        "thresholds": AUDIT.THRESHOLDS,
        "root_content": result["root_content"],
        "reference_content": result["reference_content"],
    }


def live_semantic_audit() -> dict:
    """Return a mutation-safe view of the cached live semantic audit."""

    return copy.deepcopy(_live_semantic_audit_cached())


def semantic_audit_with_synthetic_delta() -> dict:
    audit = live_semantic_audit()
    for content_key in ("root_content", "reference_content"):
        semantic = audit[content_key]["semantic_advisories"]
        entries = semantic["disposition_contract"]["entries"]
        if not entries:
            raise AssertionError(f"{content_key} needs one disposition fixture entry")
        semantic["disposition_contract"]["entries"] = entries[1:]
    return audit

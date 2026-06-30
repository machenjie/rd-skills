#!/usr/bin/env python3
"""Validate that the Business Semantic actual generator does not read eval oracles."""

from __future__ import annotations

import argparse
import ast
from pathlib import Path
from typing import Iterable

from validation_utils import fail_many


ROOT = Path(__file__).resolve().parents[1]
GENERATOR_PATH = ROOT / "scripts" / "generate-business-semantic-actuals.py"
FORBIDDEN_PREFIX = "expected_"
FORBIDDEN_EXPLICIT_NAMES = {
    "expected_route",
    "expected_skills",
    "expected_capabilities",
    "expected_quality_gates",
    "expected_bsp_sections",
    "expected_review_findings",
}
ALLOWED_FORBIDDEN_KEY_CONTAINER = "_FORBIDDEN_GENERATOR_INPUT_KEYS"


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    path = _repo_path(args.path)
    errors = validate_path(path)
    if errors:
        return fail_many("validate-business-semantic-generator", errors)
    print("validate-business-semantic-generator: OK generator expected_* oracle access is statically blocked")
    return 0


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--path", default=str(GENERATOR_PATH), help="Generator path to validate.")
    return parser.parse_args(argv)


def _repo_path(value: str) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    return ROOT / path


def validate_path(path: Path) -> list[str]:
    return validate_source(path.read_text(encoding="utf-8"), path)


def validate_source(source: str, path: Path) -> list[str]:
    try:
        tree = ast.parse(source, filename=str(path))
    except SyntaxError as exc:
        return [f"{path}: invalid Python: {exc}"]
    _attach_parents(tree)
    errors: list[str] = []
    for node in ast.walk(tree):
        if _inside_allowed_forbidden_key_definition(node):
            continue
        if isinstance(node, ast.Name) and _is_forbidden_name(node.id):
            errors.append(_format_error(path, node, f"forbidden oracle name {node.id!r}"))
        elif isinstance(node, ast.Constant) and isinstance(node.value, str):
            if _is_docstring_constant(node):
                continue
            if _is_forbidden_name(node.value):
                errors.append(_format_error(path, node, f"forbidden oracle key {node.value!r}"))
    return errors


def _attach_parents(tree: ast.AST) -> None:
    for parent in ast.walk(tree):
        for child in ast.iter_child_nodes(parent):
            setattr(child, "_parent", parent)


def _inside_allowed_forbidden_key_definition(node: ast.AST) -> bool:
    current: ast.AST | None = node
    while current is not None:
        if isinstance(current, (ast.Assign, ast.AnnAssign)):
            targets: Iterable[ast.expr]
            if isinstance(current, ast.Assign):
                targets = current.targets
            else:
                targets = (current.target,)
            if any(isinstance(target, ast.Name) and target.id == ALLOWED_FORBIDDEN_KEY_CONTAINER for target in targets):
                return True
        current = getattr(current, "_parent", None)
    return False


def _is_docstring_constant(node: ast.Constant) -> bool:
    parent = getattr(node, "_parent", None)
    grandparent = getattr(parent, "_parent", None)
    if not isinstance(parent, ast.Expr) or not isinstance(grandparent, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
        return False
    return bool(grandparent.body and grandparent.body[0] is parent)


def _is_forbidden_name(value: str) -> bool:
    return value.startswith(FORBIDDEN_PREFIX) or value in FORBIDDEN_EXPLICIT_NAMES


def _format_error(path: Path, node: ast.AST, message: str) -> str:
    try:
        display = path.relative_to(ROOT)
    except ValueError:
        display = path
    return f"{display}:{getattr(node, 'lineno', '?')}:{getattr(node, 'col_offset', '?')}: {message}"


if __name__ == "__main__":
    raise SystemExit(main())

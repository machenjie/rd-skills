"""Static Python symbol and import extraction."""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Any

from repository_intelligence.graph.file_classifier import normalize_repo_path


def _span(node: ast.AST) -> tuple[int, int]:
    start = getattr(node, "lineno", 0) or 0
    end = getattr(node, "end_lineno", start) or start
    return start, end


class _SymbolVisitor(ast.NodeVisitor):
    def __init__(self, source_path: str = "") -> None:
        self.symbols: list[dict[str, object]] = []
        self.imports: list[dict[str, object]] = []
        self._class_stack: list[str] = []
        self._source_path = source_path

    def visit_ClassDef(self, node: ast.ClassDef) -> Any:
        start, end = _span(node)
        self.symbols.append(
            {
                "name": node.name,
                "kind": "class",
                "path": self._source_path,
                "line": start,
                "line_start": start,
                "line_end": end,
                "visibility": _visibility(node.name),
                "owner_object": None,
                "parent_symbol": None,
                "language": "python",
                "confidence": "high",
            }
        )
        self._class_stack.append(node.name)
        self.generic_visit(node)
        self._class_stack.pop()

    def visit_FunctionDef(self, node: ast.FunctionDef) -> Any:
        self._record_function(node)
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> Any:
        self._record_function(node)
        self.generic_visit(node)

    def visit_Import(self, node: ast.Import) -> Any:
        for alias in node.names:
            self.imports.append(
                {
                    "module": alias.name,
                    "name": alias.asname or alias.name,
                    "level": 0,
                    "line": getattr(node, "lineno", 0) or 0,
                    "kind": "import",
                }
            )

    def visit_ImportFrom(self, node: ast.ImportFrom) -> Any:
        names = [alias.name for alias in node.names]
        self.imports.append(
            {
                "module": node.module or "",
                "names": names,
                "level": node.level,
                "line": getattr(node, "lineno", 0) or 0,
                "kind": "from_import",
            }
        )

    def visit_Assign(self, node: ast.Assign) -> Any:
        self._record_constant_targets(node.targets, node)
        self.generic_visit(node)

    def visit_AnnAssign(self, node: ast.AnnAssign) -> Any:
        self._record_constant_targets([node.target], node)
        self.generic_visit(node)

    def _record_function(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        start, end = _span(node)
        if self._class_stack:
            owner_object = self._class_stack[-1]
            name = f"{owner_object}.{node.name}"
            kind = "method"
            parent_symbol: str | None = owner_object
        else:
            owner_object = None
            name = node.name
            kind = "function"
            parent_symbol = None
        self.symbols.append(
            {
                "name": name,
                "kind": kind,
                "path": self._source_path,
                "line": start,
                "line_start": start,
                "line_end": end,
                "visibility": _visibility(node.name),
                "owner_object": owner_object,
                "parent_symbol": parent_symbol,
                "language": "python",
                "confidence": "high",
            }
        )

    def _record_constant_targets(self, targets: list[ast.expr], node: ast.AST) -> None:
        if self._class_stack:
            return
        start, end = _span(node)
        for target in targets:
            if not isinstance(target, ast.Name):
                continue
            if not target.id.isupper():
                continue
            self.symbols.append(
                {
                    "name": target.id,
                    "kind": "constant",
                    "path": self._source_path,
                    "line": start,
                    "line_start": start,
                    "line_end": end,
                    "visibility": _visibility(target.id),
                    "owner_object": None,
                    "parent_symbol": None,
                    "language": "python",
                    "confidence": "high",
                }
            )


def _visibility(name: str) -> str:
    if name.startswith("__") and name.endswith("__"):
        return "dunder"
    if name.startswith("_"):
        return "private"
    return "public"


def extract_python_source(source: str, source_path: str = "") -> dict[str, list[dict[str, object]]]:
    """Extract symbols and imports without executing Python code."""
    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        return {
            "symbols": [],
            "imports": [],
            "references": [
                {
                    "kind": "index_error",
                    "error_kind": "parse_error",
                    "value": str(exc),
                    "line": exc.lineno or 0,
                }
            ],
        }
    visitor = _SymbolVisitor(source_path)
    visitor.visit(tree)
    return {"symbols": visitor.symbols, "imports": visitor.imports, "references": []}


def extract_python_file(path: str | Path, repo_root: str | Path | None = None) -> dict[str, object]:
    file_path = Path(path)
    source = file_path.read_text(encoding="utf-8", errors="replace")
    source_path = normalize_repo_path(file_path, repo_root)
    extracted = extract_python_source(source, source_path)
    extracted["path"] = source_path
    return extracted

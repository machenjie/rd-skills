#!/usr/bin/env python3
"""Build a bounded ChangeForge TaskContextPack from a repository graph."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from repository_intelligence.graph.repo_indexer import build_repository_graph
from repository_intelligence.packaging.context_pack_builder import build_context_pack
from repository_intelligence.packaging.context_pack_renderer import render_context_pack_markdown


def _load_graph(path: str | None, target: Path) -> dict[str, object]:
    if path:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    return build_repository_graph(target)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task", required=True, help="Task goal or short request.")
    parser.add_argument("--changed-path", action="append", default=[], help="Changed or target path. Repeatable.")
    parser.add_argument("--target", default=".", help="Repository root. Defaults to cwd.")
    parser.add_argument("--graph", help="Optional prebuilt RepositoryGraph JSON path.")
    parser.add_argument("--max-files", type=int, default=36, help="Maximum selected files in the context pack.")
    parser.add_argument("--max-symbols", type=int, default=80, help="Maximum selected symbols in the context pack.")
    parser.add_argument(
        "--budget-mode",
        choices=("minimal", "single-stage", "staged-plan", "full"),
        default="single-stage",
        help="Named context budget mode.",
    )
    parser.add_argument(
        "--budget-profile",
        choices=("authoring", "runtime"),
        default="authoring",
        help="Budget limit profile. Use runtime for hook or route-generated active-context packs.",
    )
    parser.add_argument(
        "--context-budget-tokens",
        type=int,
        default=1200,
        help="Rough token budget for selected file rows.",
    )
    parser.add_argument("--out", help="Output context-pack JSON path. Writes JSON to stdout when omitted.")
    parser.add_argument("--markdown-out", help="Optional Markdown output path. Defaults to JSON sibling .md when --out is used.")
    args = parser.parse_args(argv)

    target = Path(args.target).resolve()
    graph = _load_graph(args.graph, target)
    context_pack = build_context_pack(
        graph,
        args.task,
        args.changed_path,
        target,
        max_files=args.max_files,
        max_symbols=args.max_symbols,
        context_budget_tokens=args.context_budget_tokens,
        graph_path=args.graph,
        context_pack_path=args.out,
        budget_mode=args.budget_mode,
        budget_profile=args.budget_profile,
    )
    json_payload = json.dumps(context_pack, indent=2, sort_keys=True)

    markdown_path = Path(args.markdown_out) if args.markdown_out else None
    if args.out:
        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json_payload + "\n", encoding="utf-8")
        if markdown_path is None and out_path.suffix == ".json":
            markdown_path = out_path.with_suffix(".md")
        print(f"build-context-pack: wrote JSON to {out_path}")
    else:
        print(json_payload)

    if markdown_path is not None:
        markdown_path.parent.mkdir(parents=True, exist_ok=True)
        markdown_path.write_text(render_context_pack_markdown(context_pack), encoding="utf-8")
        print(f"build-context-pack: wrote Markdown to {markdown_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

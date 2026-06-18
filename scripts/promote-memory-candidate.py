#!/usr/bin/env python3
"""Promote a human-approved Project Memory suggestion into a candidate fixture."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
if str(Path(__file__).resolve().parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent))

from project_memory.review.promote_memory_candidate import candidate_output_path, write_candidate
from validation_utils import load_yaml_file


def main() -> int:
    parser = argparse.ArgumentParser(description="Promote one memory suggestion skeleton.")
    parser.add_argument("--id", required=True, help="Suggestion id to promote.")
    parser.add_argument("--suggestions", type=Path, required=True, help="Memory suggestions YAML.")
    parser.add_argument("--repo-root", type=Path, default=ROOT, help="Repository root for output.")
    parser.add_argument("--target", default="", help="Override promotion target.")
    parser.add_argument("--write", action="store_true", help="Write candidate; default is dry run.")
    args = parser.parse_args()

    try:
        doc = load_yaml_file(args.suggestions)
    except Exception as exc:
        print(f"promote-memory-candidate: unable to read suggestions: {exc}", file=sys.stderr)
        return 1
    suggestions = doc.get("suggestions") if isinstance(doc, dict) else None
    if not isinstance(suggestions, list):
        print("promote-memory-candidate: suggestions file has no suggestions list", file=sys.stderr)
        return 1
    selected = next(
        (
            item
            for item in suggestions
            if isinstance(item, dict) and str(item.get("id", "")).strip() == args.id
        ),
        None,
    )
    if selected is None:
        print(f"promote-memory-candidate: suggestion id not found: {args.id}", file=sys.stderr)
        return 1
    target = args.target or None
    try:
        output = write_candidate(args.repo_root, selected, target=target, write=args.write)
        preview = candidate_output_path(args.repo_root, selected, target=target)
    except ValueError as exc:
        print(f"promote-memory-candidate: {exc}", file=sys.stderr)
        return 1
    if args.write:
        print(f"wrote memory candidate: {output}")
    else:
        print(f"DRY RUN: would write memory candidate: {preview}")
    print("requires_human_review: true")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


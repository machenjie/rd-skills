#!/usr/bin/env python3
"""Review cache-side Project Memory events and generate human-review candidates."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from project_memory.store.append_log import default_memory_root, iter_repo_hashes
from project_memory.review.review_project_memory import review_repository_memory


def main() -> int:
    parser = argparse.ArgumentParser(description="Review Project Memory events offline.")
    parser.add_argument("--memory-root", type=Path, default=None, help="Memory root directory.")
    parser.add_argument("--repo-hash", default="", help="Limit review to one repo hash.")
    parser.add_argument("--format", choices=("markdown", "json"), default="markdown")
    args = parser.parse_args()

    root = args.memory_root.expanduser() if args.memory_root else default_memory_root()
    repo_hashes = [args.repo_hash] if args.repo_hash else iter_repo_hashes(root)
    if not repo_hashes:
        print("review-project-memory: no samples found")
        return 0
    results = []
    for repo_hash in repo_hashes:
        repo_root = root / repo_hash
        if not (repo_root / "events").is_dir():
            continue
        result = review_repository_memory(repo_root)
        result["repo_hash"] = repo_hash
        results.append(result)
    if not results:
        print("review-project-memory: no samples found")
        return 0
    if args.format == "json":
        print(json.dumps({"repositories": results}, indent=2, sort_keys=True))
        return 0
    for result in results:
        print(f"# Project Memory Review: {result['repo_hash']}")
        print(f"- events: {result['events']}")
        print(f"- projection: {result['projection_path']}")
        if result["suggestions_path"]:
            print(f"- suggestions: {result['suggestions_path']}")
        else:
            print("- suggestions: none")
        print(f"- human-review-only suggestions: {len(result['suggestions'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


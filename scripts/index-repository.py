#!/usr/bin/env python3
"""Index a repository into a ChangeForge RepositoryGraph JSON document."""

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


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", default=".", help="Repository root to index.")
    parser.add_argument("--out", help="Output JSON path. Writes to stdout when omitted.")
    args = parser.parse_args(argv)

    graph = build_repository_graph(Path(args.target).resolve())
    payload = json.dumps(graph, indent=2, sort_keys=True)
    if args.out:
        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(payload + "\n", encoding="utf-8")
        repository_graph = graph["repository_graph"]
        print(
            "index-repository: wrote "
            f"{len(repository_graph['files'])} files and {len(repository_graph['edges'])} edges to {out_path}"
        )
    else:
        print(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

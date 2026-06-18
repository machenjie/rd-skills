#!/usr/bin/env python3
"""Inspect ChangeForge telemetry as an ordered execution trajectory."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from trajectory import (
    analyze_trajectory,
    build_trajectory,
    load_memory_events,
    load_telemetry_records,
    render_json,
    render_markdown,
)
from trajectory.trajectory_promotions import promotion_skeletons, write_skeletons


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build and analyze a ChangeForge execution trajectory from telemetry JSONL."
    )
    parser.add_argument("--telemetry-root", type=Path, default=None, help="Telemetry root. Defaults to cache root.")
    parser.add_argument("--memory-root", type=Path, default=None, help="Optional project-memory root.")
    parser.add_argument("--repo-hash", required=True, help="Repository hash under the telemetry root.")
    parser.add_argument("--session", default=None, help="Optional session id or runtime-session prefix.")
    parser.add_argument("--format", choices=("markdown", "json"), default="markdown", help="Output format.")
    parser.add_argument("--output", type=Path, default=None, help="Optional report output path.")
    parser.add_argument(
        "--generate-candidates",
        action="store_true",
        help="Include human-review-only promotion skeleton metadata when high severity issues exist.",
    )
    parser.add_argument(
        "--candidate-output-dir",
        type=Path,
        default=ROOT,
        help="Repository root for candidate paths. Used only with --write-candidates.",
    )
    parser.add_argument(
        "--write-candidates",
        action="store_true",
        help="Write candidate skeleton files. Without this flag, candidates are rendered only in the report.",
    )
    args = parser.parse_args()

    records = load_telemetry_records(args.telemetry_root, args.repo_hash, args.session)
    memory_events = load_memory_events(args.memory_root, args.repo_hash, args.session)
    trajectory = build_trajectory(records, repo_hash=args.repo_hash, session_id=args.session, memory_events=memory_events)
    if trajectory is None:
        print("inspect-trajectory: no samples found")
        return 0

    report = analyze_trajectory(trajectory)
    if args.generate_candidates:
        skeletons = promotion_skeletons(trajectory, report)
        if skeletons:
            write_skeletons(args.candidate_output_dir, skeletons, write=args.write_candidates)
            report = dict(report)
            report["promotion_skeletons"] = [
                {
                    "path": skeleton["path"],
                    "target": skeleton["target"],
                    "requires_human_review": skeleton["requires_human_review"],
                    "generated_from_telemetry": True,
                    "source_suggestion_id": _source_suggestion_id_from_content(str(skeleton.get("content") or "")),
                    "written": bool(args.write_candidates),
                }
                for skeleton in skeletons
            ]

    rendered = render_json(trajectory, report) if args.format == "json" else render_markdown(trajectory, report)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0


def _source_suggestion_id_from_content(content: str) -> str:
    for line in content.splitlines():
        if line.startswith("source_suggestion_id:"):
            return line.split(":", 1)[1].strip()
    try:
        parsed = json.loads(content)
    except json.JSONDecodeError:
        return ""
    value = parsed.get("source_suggestion_id") if isinstance(parsed, dict) else ""
    return str(value or "")


if __name__ == "__main__":
    raise SystemExit(main())

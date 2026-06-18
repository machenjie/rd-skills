#!/usr/bin/env python3
"""Resolve ChangeForge validation commands for changed paths."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from validation_broker import resolve_validation_plan


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--changed-path", action="append", default=[], help="Repository-relative path.")
    parser.add_argument("--risk-surface", action="append", default=[], help="Risk surface name.")
    parser.add_argument("--stage", default="", help="Runtime stage, if known.")
    parser.add_argument(
        "--format",
        choices=("json", "markdown"),
        default="json",
        help="Output format.",
    )
    args = parser.parse_args(argv)
    plan = resolve_validation_plan(
        args.changed_path,
        risk_surfaces=args.risk_surface,
        stage=args.stage,
    )
    if args.format == "markdown":
        print(_markdown(plan))
    else:
        print(json.dumps(plan, indent=2, sort_keys=True))
    return 0


def _markdown(plan: dict[str, object]) -> str:
    lines = ["# Validation Plan", ""]
    lines.append(f"- changed_paths: {', '.join(plan.get('changed_paths', []) or []) or '(none)'}")
    lines.append(f"- risk_surfaces: {', '.join(plan.get('risk_surfaces', []) or []) or '(none)'}")
    lines.append(f"- matched_categories: {', '.join(plan.get('matched_categories', []) or [])}")
    lines.append("")
    lines.append("## Recommended")
    for command in plan.get("recommended_commands", []) or []:
        if isinstance(command, dict):
            lines.append(f"- `{command.get('command')}` ({command.get('level')}): {command.get('reason')}")
    lines.append("")
    lines.append("## Full")
    for command in plan.get("full_commands", []) or []:
        if isinstance(command, dict):
            lines.append(f"- `{command.get('command')}` ({command.get('level')}): {command.get('reason')}")
    return "\n".join(lines)


if __name__ == "__main__":
    raise SystemExit(main())

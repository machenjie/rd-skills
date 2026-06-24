#!/usr/bin/env python3
"""Render a human-readable dashboard from the professional scorecard JSON."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


STATUSES = ("pass", "partial", "fail", "unknown", "not_collected")
README_START = "<!-- changeforge-scorecard-summary:start -->"
README_END = "<!-- changeforge-scorecard-summary:end -->"
REFRESH_COMMANDS = [
    "python3 scripts/generate-professional-scorecard.py --strict-profile-builds --out reports/professional-scorecard.md --json-out reports/professional-scorecard.json",
    "python3 scripts/render-scorecard-dashboard.py --scorecard reports/professional-scorecard.json --out docs/SCORECARD_DASHBOARD.md --readme README.md",
]


def _read_payload(path: Path) -> dict[str, Any]:
    loaded = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(loaded, dict):
        raise ValueError("scorecard JSON must be an object")
    return loaded


def _dimensions(payload: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        item
        for item in payload.get("dimensions", [])
        if isinstance(item, dict)
    ]


def _dimension(payload: dict[str, Any], name: str) -> dict[str, Any] | None:
    for item in _dimensions(payload):
        if item.get("name") == name:
            return item
    return None


def _status(payload: dict[str, Any], name: str) -> str:
    item = _dimension(payload, name)
    status = str(item.get("status")) if item else "unknown"
    return status if status in STATUSES else "unknown"


def _detail(payload: dict[str, Any], name: str) -> str:
    item = _dimension(payload, name)
    return str(item.get("detail", "")) if item else "not present in scorecard"


def _status_counts(payload: dict[str, Any]) -> dict[str, int]:
    counts = {status: 0 for status in STATUSES}
    for item in _dimensions(payload):
        status = str(item.get("status"))
        if status in counts:
            counts[status] += 1
        else:
            counts["unknown"] += 1
    return counts


def _severity(status: str) -> str:
    return {
        "fail": "High",
        "partial": "Medium",
        "unknown": "Medium",
        "not_collected": "Low",
    }.get(status, "Low")


def _escape(text: str) -> str:
    return text.replace("|", "\\|").replace("\n", " ")


def _evidence_levels(payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    value = payload.get("evidence_levels")
    if not isinstance(value, dict):
        return {}
    levels: dict[str, dict[str, Any]] = {}
    for name, detail in value.items():
        if not isinstance(detail, dict):
            continue
        status = str(detail.get("status", "unknown"))
        if status not in STATUSES:
            status = "unknown"
        levels[str(name)] = {
            "status": status,
            "meaning": str(detail.get("meaning", "")),
        }
    return levels


def render_dashboard(payload: dict[str, Any]) -> str:
    """Render the scorecard dashboard as Markdown."""
    counts = _status_counts(payload)
    lines = [
        "# Scorecard Dashboard",
        "",
        "This generated dashboard makes conservative scorecard results easier to scan. Missing evidence remains `unknown` or `not_collected`; it is never rendered as pass.",
        "",
        "## Status Summary",
        "",
    ]
    for status in STATUSES:
        lines.append(f"- `{status}`: {counts[status]}")

    levels = _evidence_levels(payload)
    lines.extend(["", "## Evidence Levels", "", "| Evidence | Status | Meaning |", "| --- | --- | --- |"])
    if levels:
        for level, detail in levels.items():
            lines.append(
                f"| {level} | `{detail['status']}` | {_escape(str(detail.get('meaning', '')))} |"
            )
    else:
        lines.append("| unknown | `unknown` | evidence level metadata not present in scorecard |")

    lines.extend(["", "## Key Statuses", "", "| Evidence | Status | Detail |", "| --- | --- | --- |"])
    for name in (
        "Profile build reproducibility",
        "Open-source readiness",
        "Example coverage",
        "Executor adapter structural fixtures",
        "Activation precision benchmark",
        "Runtime telemetry fixture sample",
        "Live runtime telemetry sample",
        "Codex CLI live benchmark",
        "Marketplace index validation",
    ):
        lines.append(f"| {name} | `{_status(payload, name)}` | {_escape(_detail(payload, name))} |")

    lines.extend(["", "## Profile Counts", ""])
    profile_counts = payload.get("profile_counts", {})
    if isinstance(profile_counts, dict) and profile_counts:
        for profile, detail in profile_counts.items():
            if isinstance(detail, dict):
                lines.append(f"- `{profile}`: `{detail.get('status', 'unknown')}` - {_escape(str(detail.get('detail', '')))}")
    else:
        lines.append("- `unknown`: profile count evidence not present")

    lines.extend(["", "## Release-Only Evidence Not Collected", ""])
    release_only = [
        item
        for item in _dimensions(payload)
        if item.get("status") == "not_collected"
    ]
    if release_only:
        for item in release_only:
            lines.append(f"- {item.get('name')}: {_escape(str(item.get('source', '')))}")
    else:
        lines.append("- None")

    grouped: dict[str, list[dict[str, Any]]] = {"High": [], "Medium": [], "Low": []}
    for item in _dimensions(payload):
        status = str(item.get("status"))
        if status != "pass":
            grouped[_severity(status)].append(item)

    lines.extend(["", "## Repair Hints", ""])
    for severity in ("High", "Medium", "Low"):
        lines.extend([f"### {severity}", ""])
        if not grouped[severity]:
            lines.append("- None")
        else:
            for item in grouped[severity]:
                lines.append(
                    f"- `{item.get('status', 'unknown')}` {item.get('name')}: {_escape(str(item.get('fix_hint', '')))}"
                )
        lines.append("")

    commands = [
        str(entry.get("command"))
        for entry in payload.get("validation_commands", [])
        if isinstance(entry, dict) and entry.get("command")
    ] or REFRESH_COMMANDS
    lines.extend(["## Refresh Commands", "", "```bash"])
    lines.extend(commands)
    lines.extend(REFRESH_COMMANDS[1:])
    lines.extend(["```", ""])
    return "\n".join(lines)


def readme_summary_block(payload: dict[str, Any]) -> str:
    """Render the generated README scorecard summary block."""
    rows = [
        ("Profile build reproducibility", "Profile build reproducibility", "docs/SCORECARD_DASHBOARD.md"),
        ("Example coverage", "Example coverage", "scripts/validate-examples.py"),
        ("Codex CLI live benchmark", "Codex CLI live benchmark", "reports/codex-live-benchmark-summary.json"),
        ("Marketplace index validation", "Marketplace index validation", "scripts/validate-marketplace-index.py"),
        ("Open-source readiness", "Open-source readiness", "docs/OPEN_SOURCE_READINESS.md"),
    ]
    lines = [
        README_START,
        "| Evidence | Status | Source |",
        "| --- | --- | --- |",
    ]
    for label, dimension_name, source in rows:
        lines.append(f"| {label} | `{_status(payload, dimension_name)}` | [{source}]({source}) |")
    lines.append(README_END)
    return "\n".join(lines)


def replace_readme_block(readme_text: str, block: str) -> str:
    """Replace the generated README summary block."""
    start = readme_text.find(README_START)
    end = readme_text.find(README_END)
    if start == -1 or end == -1 or end < start:
        raise ValueError("README scorecard summary markers are missing or malformed")
    end += len(README_END)
    return readme_text[:start] + block + readme_text[end:]


def replace_readme_profile_counts(readme_text: str, payload: dict[str, Any]) -> str:
    """Replace the README stable profile count sentence from scorecard profile counts."""
    profile_counts = payload.get("profile_counts") if isinstance(payload.get("profile_counts"), dict) else {}
    values: dict[str, int] = {}
    for profile in ("recommended", "full", "dev"):
        detail = profile_counts.get(profile)
        text = str(detail.get("detail", "")) if isinstance(detail, dict) else ""
        match = re.search(r"top-level count is (\d+)", text)
        if match:
            values[profile] = int(match.group(1))
    if set(values) != {"recommended", "full", "dev"}:
        return readme_text
    replacement = (
        "Stable profile counts are "
        f"`recommended={values['recommended']}`, `full={values['full']}`, and `dev={values['dev']}`; "
        "these generated manifests are the authoritative runtime profile count source. "
        "Local install starts with `python3 scripts/quickstart.py --agent codex --scope user`; "
        "official Codex/Claude marketplace publishing is intentionally not implemented."
    )
    pattern = re.compile(
        r"Stable profile counts are `?recommended=\d+`?, `?full=\d+`?, and `?dev=\d+`?[.;] [^\n]*"
    )
    return pattern.sub(replacement, readme_text)


def _check_file(path: Path, expected: str) -> list[str]:
    if not path.exists():
        return [f"{path} does not exist"]
    if path.read_text(encoding="utf-8") != expected:
        return [f"{path} is stale"]
    return []


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint for rendering or checking dashboard outputs."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scorecard", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--readme")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)

    try:
        payload = _read_payload(Path(args.scorecard))
        dashboard = render_dashboard(payload)
        readme_block = readme_summary_block(payload)
        out = Path(args.out)
        errors = []
        if args.check:
            errors.extend(_check_file(out, dashboard))
            if args.readme:
                readme = Path(args.readme)
                expected_readme = replace_readme_profile_counts(
                    replace_readme_block(readme.read_text(encoding="utf-8"), readme_block),
                    payload,
                )
                errors.extend(_check_file(readme, expected_readme))
            if errors:
                for error in errors:
                    print(f"render-scorecard-dashboard: ERROR: {error}", file=sys.stderr)
                return 1
            print("render-scorecard-dashboard: committed output is fresh")
            return 0

        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(dashboard, encoding="utf-8")
        if args.readme:
            readme = Path(args.readme)
            readme.write_text(
                replace_readme_profile_counts(
                    replace_readme_block(readme.read_text(encoding="utf-8"), readme_block),
                    payload,
                ),
                encoding="utf-8",
            )
        print(f"wrote scorecard dashboard to {out}")
        return 0
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"render-scorecard-dashboard: ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Generate a human-readable catalog from the four Skill registries."""

from __future__ import annotations

import argparse
import importlib.util
import sys
import textwrap
from pathlib import Path
from typing import Any

from validation_utils import EXPECTED_PROFILE_TOP_LEVEL_COUNTS


ROOT = Path(__file__).resolve().parents[1]
PROFILES = ("recommended", "full", "dev")


def _load_exporter():
    spec = importlib.util.spec_from_file_location(
        "export_marketplace_index_for_catalog",
        ROOT / "scripts" / "export-marketplace-index.py",
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("unable to load export-marketplace-index.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


EXPORTER = _load_exporter()


def _items_by_name(
    indexes: dict[str, dict[str, Any]],
    reference_profile: str,
) -> dict[str, dict[str, Any]]:
    return {
        str(item["name"]): item
        for item in indexes[reference_profile]["items"]
        if isinstance(item, dict)
    }


def _items(payload: dict[str, Any], item_type: str) -> list[dict[str, Any]]:
    return sorted(
        [
            item
            for item in payload["items"].values()
            if item["type"] == item_type
        ],
        key=lambda item: item["name"],
    )


def _csv(values: list[Any]) -> str:
    strings = [str(value) for value in values if str(value).strip()]
    return ", ".join(f"`{value}`" for value in strings) if strings else "`none`"


def _line(text: str) -> str:
    return text.replace("|", "\\|").replace("\n", " ")


def _browse_by(
    items: list[dict[str, Any]],
    field: str,
) -> dict[str, list[str]]:
    grouped: dict[str, list[str]] = {}
    for item in items:
        for value in item.get(field, []):
            grouped.setdefault(str(value), []).append(str(item["name"]))
    return {key: sorted(values) for key, values in sorted(grouped.items())}


def _name_chunks(values: list[str], size: int = 3) -> list[list[str]]:
    """Split discovery names into short, stable Markdown-list chunks."""

    return [values[index : index + size] for index in range(0, len(values), size)]


def _render_name_group(lines: list[str], label: str, names: list[str]) -> None:
    lines.extend([f"### {label}", ""])
    for chunk in _name_chunks(sorted(names)):
        lines.append(f"- {_csv(chunk)}")
    if not names:
        lines.append("- `none`")
    lines.append("")


def _append_paragraph(lines: list[str], value: str) -> None:
    lines.extend(
        textwrap.wrap(
            value,
            width=100,
            break_long_words=False,
            break_on_hyphens=False,
        )
    )


def _append_text_field(lines: list[str], label: str, value: Any) -> None:
    wrapped = textwrap.wrap(
        _line(str(value)),
        width=92,
        break_long_words=False,
        break_on_hyphens=False,
    ) or ["Not supplied."]
    lines.append(f"- {label}: {wrapped[0]}")
    lines.extend(f"  {part}" for part in wrapped[1:])


def _append_name_field(lines: list[str], label: str, values: list[Any]) -> None:
    names = sorted(str(value) for value in values if str(value).strip())
    if not names:
        lines.append(f"- {label}: `none`")
        return
    lines.append(f"- {label}:")
    lines.extend(f"  - {_csv(chunk)}" for chunk in _name_chunks(names))


def _append_text_values(lines: list[str], label: str, values: list[Any]) -> None:
    phrases = sorted(str(value) for value in values if str(value).strip())
    if not phrases:
        lines.append(f"- {label}: none")
        return
    lines.append(f"- {label}:")
    for phrase in phrases:
        wrapped = textwrap.wrap(
            _line(phrase),
            width=88,
            break_long_words=False,
            break_on_hyphens=False,
        ) or ["Not supplied."]
        lines.append(f"  - {wrapped[0]}")
        lines.extend(f"    {part}" for part in wrapped[1:])


def _append_delivery_field(
    lines: list[str], indexes: dict[str, dict[str, Any]], name: str
) -> None:
    labels = {
        "top_level_skill": "top-level Skill",
        "targeted_reference": "targeted reference",
        "routing_index_only": "routing index only",
    }
    lines.append("- Profile delivery:")
    for profile in PROFILES:
        item = next(
            item
            for item in indexes[profile]["items"]
            if isinstance(item, dict) and item.get("name") == name
        )
        mode = str(item["profile_delivery"]["mode"])
        lines.append(f"  - `{profile}`: {labels[mode]}")


def generate_catalog(root: Path, reference_profile: str) -> dict[str, Any]:
    """Generate one catalog payload from exporter-backed profile indexes."""

    indexes = {
        profile: EXPORTER.export_index(root, profile)
        for profile in PROFILES
    }
    return {
        "reference_profile": reference_profile,
        "indexes": indexes,
        "items": _items_by_name(indexes, reference_profile),
    }


def render_catalog(payload: dict[str, Any]) -> str:
    """Render a concise local discovery catalog."""

    indexes = payload["indexes"]
    all_items = list(payload["items"].values())
    lines = ["# Marketplace Catalog", ""]
    _append_paragraph(
        lines,
        "This generated catalog is a local Marketplace schema v3 discovery view over the "
        "Control, Professional, Foundation, and Domain Skill registries. Every top-level "
        "entry is a standard Skill with `SKILL.md` at its root. Foundation and Domain "
        "Skills are exposed only as top-level Skills or task-targeted references; this "
        "catalog does not define an execution protocol.",
    )
    lines.append("")
    _append_paragraph(
        lines,
        "Official marketplace publishing is intentionally not implemented. This catalog "
        "must not be used to claim official marketplace availability.",
    )
    lines.extend([
        "",
        "_Generated by `python3 scripts/generate-marketplace-catalog.py --profile recommended --out <path>`. Do not edit by hand._",
        "",
        "## How To Use This Catalog",
        "",
        "1. Choose a build profile in Profile Summary; Build Profiles remains the composition authority.",
        "2. Start with Professional Skills when selecting a complete engineering judgment.",
        "   Use Foundation and Domain sections only for concrete Layer 3 signals.",
        "3. Search by exact Skill name, Agent Profile, trigger signal, or delivery mode.",
        "   Discovery does not authorize loading a full catalog into one task.",
        "4. Confirm routing and install behavior in the source registries and generated manifest.",
        "   Use the owning documentation before making a product claim.",
        "",
        "## Quick Navigation",
        "",
        "- [Profile Summary](#profile-summary)",
        "- [Control Skills](#control-skills)",
        "- [Professional Skills](#professional-skills)",
        "- [Foundation Skills By Group](#foundation-skills-by-group)",
        "- [Domain Skills](#domain-skills)",
        "- [Browse By Agent Profile](#browse-by-agent-profile)",
        "- [Browse By Trigger Signal](#browse-by-trigger-signal)",
        "- [Browse By Profile Delivery](#browse-by-profile-delivery)",
        "",
        "## Profile Summary",
        "",
        "| Profile | Top-Level Skills | Targeted References | Routing Index Only |",
        "| --- | ---: | ---: | ---: |",
    ])
    for profile in PROFILES:
        profile_items = indexes[profile]["items"]
        counts = {
            mode: sum(
                item["profile_delivery"]["mode"] == mode
                for item in profile_items
            )
            for mode in (
                "top_level_skill",
                "targeted_reference",
                "routing_index_only",
            )
        }
        lines.append(
            f"| `{profile}` | {counts['top_level_skill']} | "
            f"{counts['targeted_reference']} | {counts['routing_index_only']} |"
        )
        if counts["top_level_skill"] != EXPECTED_PROFILE_TOP_LEVEL_COUNTS[profile]:
            raise RuntimeError(f"{profile} top-level Skill count drift")

    lines.extend(
        [
            "",
            "## Control Skills",
            "",
        ]
    )
    for item in _items(payload, "control_skill"):
        lines.extend([f"### `{item['name']}`", ""])
        _append_text_field(lines, "Summary", item["summary"])
        _append_name_field(lines, "Agent Profiles", item["role_support"])
        _append_delivery_field(lines, indexes, str(item["name"]))
        lines.append("")

    lines.extend(
        [
            "",
            "## Professional Skills",
            "",
        ]
    )
    for item in _items(payload, "professional_skill"):
        lines.extend([f"### `{item['name']}`", ""])
        _append_text_field(lines, "Summary", item["summary"])
        _append_name_field(lines, "Agent Profiles", item["role_support"])
        lines.append(f"- Task routable: `{str(item['task_routable']).lower()}`")
        _append_text_values(lines, "Trigger signals", item["trigger_signals"])
        _append_name_field(
            lines, "Related Layer 3 Skills", item["related_layer3_skills"]
        )
        lines.append("")

    lines.extend(["", "## Foundation Skills By Group", ""])
    grouped: dict[str, list[dict[str, Any]]] = {}
    for item in _items(payload, "foundation_skill"):
        grouped.setdefault(str(item.get("group") or "ungrouped"), []).append(item)
    for group, skills in sorted(grouped.items()):
        lines.extend(
            [
                f"### {group}",
                "",
            ]
        )
        for item in skills:
            lines.extend([f"#### `{item['name']}`", ""])
            lines.append(f"- Delivery scope: `{item['delivery_scope']}`")
            _append_name_field(lines, "Agent Profiles", item["role_support"])
            _append_name_field(lines, "Used by", item["used_by"])
            _append_text_values(lines, "Trigger signals", item["trigger_signals"])
            lines.append("")

    lines.extend(
        [
            "## Domain Skills",
            "",
        ]
    )
    for item in _items(payload, "domain_skill"):
        lines.extend([f"### `{item['name']}`", ""])
        _append_text_field(lines, "Summary", item["summary"])
        _append_name_field(lines, "Agent Profiles", item["role_support"])
        _append_delivery_field(lines, indexes, str(item["name"]))
        lines.append("")

    lines.extend(["", "## Browse By Agent Profile", ""])
    for role, names in _browse_by(all_items, "role_support").items():
        _render_name_group(lines, f"`{role}`", names)

    lines.extend(["", "## Browse By Trigger Signal", ""])
    for index, (trigger, names) in enumerate(
        _browse_by(all_items, "trigger_signals").items(), start=1
    ):
        lines.extend([f"### Signal {index:03d}", ""])
        _append_text_field(lines, "Trigger signal", trigger)
        _append_name_field(lines, "Matching Skills", names)
        lines.append("")

    lines.extend(["", "## Browse By Profile Delivery", ""])
    for profile in PROFILES:
        grouped_delivery: dict[str, list[str]] = {
            "top_level_skill": [],
            "targeted_reference": [],
            "routing_index_only": [],
        }
        for item in indexes[profile]["items"]:
            grouped_delivery[item["profile_delivery"]["mode"]].append(item["name"])
        for mode, names in grouped_delivery.items():
            _render_name_group(lines, f"`{profile}` — `{mode}`", names)
    return "\n".join(lines)


def _check_file(path: Path, expected: str) -> list[str]:
    if not path.exists():
        return [f"{path} does not exist"]
    if path.read_text(encoding="utf-8") != expected:
        return [f"{path} is stale"]
    return []


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", choices=PROFILES, default="recommended")
    parser.add_argument("--out", required=True)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)

    rendered = render_catalog(generate_catalog(ROOT, args.profile))
    out = Path(args.out)
    if args.check:
        errors = _check_file(out, rendered)
        if errors:
            for error in errors:
                print(f"generate-marketplace-catalog: ERROR: {error}", file=sys.stderr)
            return 1
        print("generate-marketplace-catalog: committed output is fresh")
        return 0

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(rendered, encoding="utf-8")
    print(f"wrote marketplace catalog to {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

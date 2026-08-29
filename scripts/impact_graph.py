#!/usr/bin/env python3
"""Resolve changed repository paths through the Core-owned Impact Graph."""

from __future__ import annotations

import json
import os
import re
import subprocess
from fnmatch import fnmatchcase
from pathlib import Path, PurePosixPath
from typing import Any, Mapping, Sequence

from validation_utils import ValidationProblem, load_yaml_text, validate_core_contracts


CORE_RELATIVE_PATH = Path("src/control-model/core-contracts.json")
HEX_REVISION = re.compile(r"[0-9a-fA-F]{40}")


class ImpactGraphError(RuntimeError):
    """A stable fail-closed impact-selection failure."""

    def __init__(self, reason: str, detail: str) -> None:
        super().__init__(detail)
        self.reason = reason
        self.detail = detail


def load_core(root: Path) -> dict[str, Any]:
    """Load and validate the one authoritative Core contract."""

    try:
        data = json.loads((root / CORE_RELATIVE_PATH).read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ImpactGraphError("invalid-impact-graph", str(exc)) from exc
    errors = validate_core_contracts(data, root)
    if errors:
        raise ImpactGraphError(
            "invalid-impact-graph",
            "; ".join(errors),
        )
    assert isinstance(data, dict)
    return data


def _matches(path: str, pattern: str) -> bool:
    if pattern == "tests/**/test*.py":
        candidate = PurePosixPath(path)
        return (
            len(candidate.parts) >= 2
            and candidate.parts[0] == "tests"
            and candidate.name.startswith("test")
            and candidate.suffix == ".py"
        )
    if pattern.endswith("/**"):
        prefix = pattern[:-3]
        return path.startswith(prefix + "/")
    return fnmatchcase(path, pattern)


def _safe_changed_path(path: str) -> bool:
    candidate = PurePosixPath(path)
    return bool(
        path
        and "\x00" not in path
        and "\\" not in path
        and not candidate.is_absolute()
        and ".." not in candidate.parts
    )


def _closed_graph(core: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Return the graph and canonical producers or reject runtime ambiguity."""

    graph = core.get("impact_graph_contract")
    acceptance = core.get("principle_acceptance_contract")
    if not isinstance(graph, dict) or not isinstance(acceptance, dict):
        raise ImpactGraphError(
            "invalid-impact-graph", "missing impact or producer contract"
        )
    producers = acceptance.get("producers")
    rules = graph.get("rules")
    stages = graph.get("stages")
    test_selection = graph.get("test_selection")
    if (
        not isinstance(producers, list)
        or not isinstance(rules, list)
        or not isinstance(stages, dict)
        or not isinstance(stages.get("affected"), dict)
        or not isinstance(stages.get("ci-tests"), dict)
        or not isinstance(test_selection, dict)
    ):
        raise ImpactGraphError("invalid-impact-graph", "graph collections are malformed")
    producer_ids = [
        row.get("id") for row in producers if isinstance(row, dict)
    ]
    if (
        len(producer_ids) != len(producers)
        or any(not isinstance(item, str) or not item for item in producer_ids)
        or len(producer_ids) != len(set(producer_ids))
    ):
        raise ImpactGraphError("invalid-impact-graph", "canonical producers are invalid")
    eligible = stages["affected"].get("eligible_producer_ids")
    if (
        not isinstance(eligible, list)
        or len(eligible) != len(set(eligible))
        or not set(eligible).issubset(set(producer_ids))
    ):
        raise ImpactGraphError("invalid-impact-graph", "affected eligibility is invalid")
    for rule in rules:
        if (
            not isinstance(rule, dict)
            or set(rule) != {"id", "path_patterns", "producer_ids", "test_modules"}
            or not isinstance(rule["id"], str)
            or not isinstance(rule["path_patterns"], list)
            or not rule["path_patterns"]
            or not isinstance(rule["producer_ids"], list)
            or not isinstance(rule["test_modules"], list)
            or not set(rule["producer_ids"]).issubset(set(eligible))
        ):
            raise ImpactGraphError("invalid-impact-graph", "impact rule is malformed")
    order = test_selection.get("order")
    overrides = test_selection.get("module_overrides")
    if (
        order != ["unit", "integration", "contract", "governance", "release"]
        or test_selection.get("default_layer") != "unit"
        or not isinstance(overrides, list)
    ):
        raise ImpactGraphError("invalid-impact-graph", "test selection is malformed")
    return graph, producers


def _test_layer(graph: dict[str, Any], module: str) -> str:
    selection = graph["test_selection"]
    matches = [
        row["layer"]
        for row in selection["module_overrides"]
        if row.get("module") == module
    ]
    if len(matches) > 1:
        raise ImpactGraphError(
            "invalid-impact-graph", f"test module {module!r} has multiple layers"
        )
    return matches[0] if matches else selection["default_layer"]


def _affected_test_projection(
    graph: dict[str, Any], modules: Sequence[str]
) -> tuple[dict[str, list[str]], list[str]]:
    selection = graph["test_selection"]
    policy = graph["stages"]["affected"]["test_policy"]
    selectable = set(policy["always_layers"]) | set(policy["direct_only_layers"])
    forbidden = set(policy["forbidden_layers"])
    if selectable & forbidden or selectable | forbidden != set(selection["order"]):
        raise ImpactGraphError("invalid-impact-graph", "affected test policy is invalid")
    grouped = {layer: [] for layer in selection["order"]}
    for module in sorted(set(modules)):
        layer = _test_layer(graph, module)
        if layer not in grouped:
            raise ImpactGraphError(
                "invalid-impact-graph", f"test module {module!r} has unknown layer"
            )
        if layer in selectable:
            grouped[layer].append(module)
    flattened = sorted(module for values in grouped.values() for module in values)
    return grouped, flattened


def _professionalism_contract(graph: dict[str, Any]) -> dict[str, Any]:
    affected = graph["stages"]["affected"]
    value = affected.get("professionalism")
    if not isinstance(value, dict):
        raise ImpactGraphError(
            "invalid-impact-graph", "affected professionalism contract is malformed"
        )
    return value


def _expert_panel_evidence_contract(graph: dict[str, Any]) -> dict[str, Any]:
    affected = graph["stages"]["affected"]
    value = affected.get("expert_panel_evidence_projection")
    if not isinstance(value, dict):
        raise ImpactGraphError(
            "invalid-impact-graph",
            "affected Expert Panel evidence projection is malformed",
        )
    return value


def _runtime_contract(graph: dict[str, Any]) -> dict[str, Any]:
    value = graph["stages"]["affected"].get("runtime_projection")
    if (
        not isinstance(value, dict)
        or value.get("runtime_name") != "recommended"
        or value.get("producer_id") != "build-recommended"
        or value.get("package_layers") != ["professional", "foundation", "domain"]
        or value.get("unknown_package_policy") != "runtime"
    ):
        raise ImpactGraphError(
            "invalid-impact-graph", "single Runtime projection is malformed"
        )
    return value


def _entry_selects_runtime(
    status: str,
    path: str,
    *,
    base_package_catalog: Mapping[str, dict[str, Any]],
    head_package_catalog: Mapping[str, dict[str, Any]],
    projection: Mapping[str, Any],
) -> bool:
    package_roots = (
        "src/professional-skills/",
        "src/foundation/capabilities/",
        "src/domain-extensions/",
    )
    if not path.startswith(package_roots):
        return False
    catalogs = (
        [base_package_catalog]
        if status == "D"
        else [head_package_catalog]
        if status == "A"
        else [base_package_catalog, head_package_catalog]
    )
    package_id = _catalog_package_for_path(path, catalogs)
    if package_id is None:
        return True
    allowed_layers = set(projection["package_layers"])
    observed = False
    for catalog in catalogs:
        row = catalog.get(package_id)
        if not isinstance(row, dict):
            continue
        observed = True
        if row.get("layer") not in allowed_layers:
            return True
    return observed


def _catalog_package_for_path(
    path: str,
    catalogs: Sequence[Mapping[str, dict[str, Any]]],
) -> str | None:
    matches: set[str] = set()
    for catalog in catalogs:
        for skill_id, row in catalog.items():
            prefix = row.get("path") if isinstance(row, dict) else None
            if isinstance(prefix, str) and (path == prefix or path.startswith(prefix + "/")):
                matches.add(skill_id)
    if len(matches) > 1:
        raise ImpactGraphError(
            "ambiguous-professionalism-package",
            f"path {path!r} belongs to multiple Professionalism packages",
        )
    return next(iter(matches), None)


def _registry_envelope_equal(
    value: bool | Mapping[str, bool], registry_path: str
) -> bool:
    if isinstance(value, bool):
        return value
    result = value.get(registry_path)
    if not isinstance(result, bool):
        raise ImpactGraphError(
            "invalid-package-catalog",
            f"registry envelope comparison is missing for {registry_path!r}",
        )
    return result


def _professionalism_scope(
    graph: dict[str, Any],
    entries: Sequence[tuple[str, str]],
    *,
    base_package_catalog: Mapping[str, dict[str, Any]],
    head_package_catalog: Mapping[str, dict[str, Any]],
    registry_envelopes_equal: bool | Mapping[str, bool],
) -> dict[str, object]:
    contract = _professionalism_contract(graph)
    registry_paths = {
        row["path"] for row in contract["registry_sources"]
    }
    full_patterns = contract["full_scope_patterns"]
    direct: set[str] = set()
    reasons: list[list[str]] = []
    full = False

    removed_package_ids = sorted(
        set(base_package_catalog) - set(head_package_catalog)
    )
    if removed_package_ids:
        full = True
        reasons.extend(
            [
                f"package:{skill_id}",
                "professionalism:package-removed",
                "scope:full",
            ]
            for skill_id in removed_package_ids
        )

    for status, path in entries:
        if any(_matches(path, pattern) for pattern in full_patterns):
            full = True
            reasons.append([f"path:{path}", "professionalism:global-contract", "scope:full"])
            continue
        if path in registry_paths:
            if not _registry_envelope_equal(registry_envelopes_equal, path):
                full = True
                reasons.append([f"path:{path}", "professionalism:registry-envelope", "scope:full"])
                continue
            changed_ids = sorted(
                skill_id
                for skill_id in set(base_package_catalog) | set(head_package_catalog)
                if (
                    (
                        base_package_catalog.get(skill_id, {}).get("registry_path") == path
                        or head_package_catalog.get(skill_id, {}).get("registry_path") == path
                    )
                    and base_package_catalog.get(skill_id, {}).get("registry_entry")
                    != head_package_catalog.get(skill_id, {}).get("registry_entry")
                )
            )
            for skill_id in changed_ids:
                direct.add(skill_id)
                reasons.append(
                    [f"path:{path}", f"package:{skill_id}", "professionalism:registry-entry"]
                )
            continue
        catalogs: list[Mapping[str, dict[str, Any]]]
        if status == "D":
            catalogs = [base_package_catalog]
        elif status == "A":
            catalogs = [head_package_catalog]
        else:
            catalogs = [base_package_catalog, head_package_catalog]
        skill_id = _catalog_package_for_path(path, catalogs)
        if skill_id is not None:
            direct.add(skill_id)
            reasons.append(
                [f"path:{path}", f"package:{skill_id}", "professionalism:package-material"]
            )
            continue
        if path.startswith(
            ("src/professional-skills/", "src/foundation/", "src/domain-extensions/")
        ):
            full = True
            reasons.append(
                [f"path:{path}", "professionalism:package-unresolved", "scope:full"]
            )

    if full:
        scope = "full"
        direct_ids: list[str] = []
    elif direct:
        scope = "packages"
        direct_ids = sorted(direct)
    else:
        scope = "none"
        direct_ids = []
    return {
        "scope": scope,
        "direct_package_ids": direct_ids,
        "reason_chains": sorted(reasons),
    }


def _expert_panel_evidence_impact(
    graph: dict[str, Any],
    entries: Sequence[tuple[str, str]],
) -> dict[str, object]:
    contract = _expert_panel_evidence_contract(graph)
    affected_axes: set[str] = set()
    reasons: list[list[str]] = []
    for _status, path in entries:
        for source in contract["axis_sources"]:
            axis = source["axis"]
            if any(
                _matches(path, pattern)
                for pattern in source["path_patterns"]
            ):
                affected_axes.add(axis)
                reasons.append(
                    [f"path:{path}", f"expert-panel-axis:{axis}", "evidence:soft-stale"]
                )
    ordered_axes = [
        axis for axis in contract["axis_order"] if axis in affected_axes
    ]
    return {
        "schema_version": contract["schema_version"],
        "status": (
            contract["affected_status"]
            if ordered_axes
            else contract["unchanged_status"]
        ),
        "affected_axes": ordered_axes,
        "reason_chains": sorted(reasons),
    }


def _producer_closure(
    producers: list[dict[str, Any]],
    direct_reasons: dict[str, list[list[str]]],
) -> tuple[list[str], list[dict[str, object]]]:
    rows = {row["id"]: row for row in producers}
    reasons = {
        producer_id: [list(chain) for chain in chains]
        for producer_id, chains in direct_reasons.items()
    }
    visiting: set[str] = set()
    visited: set[str] = set()
    order: list[str] = []

    def add_reason(producer_id: str, chain: list[str]) -> None:
        bucket = reasons.setdefault(producer_id, [])
        if chain not in bucket:
            bucket.append(chain)

    def visit(producer_id: str) -> None:
        if producer_id in visiting:
            raise ImpactGraphError(
                "invalid-impact-graph", "canonical producer dependency cycle"
            )
        if producer_id in visited:
            return
        row = rows.get(producer_id)
        if row is None:
            raise ImpactGraphError(
                "invalid-impact-graph", f"unknown producer {producer_id!r}"
            )
        visiting.add(producer_id)
        source_chains = reasons.get(producer_id, [])
        for dependency in row["depends_on"]:
            for chain in source_chains:
                add_reason(
                    dependency,
                    [*chain, f"depends-on:{dependency}"],
                )
            visit(dependency)
        visiting.remove(producer_id)
        visited.add(producer_id)
        order.append(producer_id)

    direct_ids = set(direct_reasons)
    for producer in producers:
        if producer["id"] in direct_ids:
            visit(producer["id"])
    explanations = [
        {
            "id": producer_id,
            "chains": sorted(reasons.get(producer_id, [])),
        }
        for producer_id in order
    ]
    return order, explanations


def _canonical_producer_script_ownership(
    graph: Mapping[str, Any],
    producers: Sequence[Mapping[str, Any]],
) -> dict[str, dict[str, list[str]]]:
    """Derive canonical script owners and their existing Core test targets."""

    tests_by_producer: dict[str, set[str]] = {}
    for rule in graph["rules"]:
        for producer_id in rule["producer_ids"]:
            tests_by_producer.setdefault(producer_id, set()).update(
                rule["test_modules"]
            )
    owners: dict[str, dict[str, set[str]]] = {}
    for producer in producers:
        producer_id = producer["id"]
        for argument in producer["argv"]:
            if not (
                isinstance(argument, str)
                and argument.startswith("scripts/")
                and argument.endswith(".py")
            ):
                continue
            owner = owners.setdefault(
                argument, {"producer_ids": set(), "test_modules": set()}
            )
            owner["producer_ids"].add(producer_id)
            owner["test_modules"].update(tests_by_producer.get(producer_id, set()))
    invalid = sorted(
        path for path, owner in owners.items() if not owner["test_modules"]
    )
    if invalid:
        raise ImpactGraphError(
            "invalid-producer-script-ownership",
            f"canonical producer scripts lack Core test ownership: {invalid}",
        )
    return {
        path: {
            "producer_ids": sorted(owner["producer_ids"]),
            "test_modules": sorted(owner["test_modules"]),
        }
        for path, owner in sorted(owners.items())
    }


def resolve_entries(
    core: dict[str, Any],
    entries: Sequence[tuple[str, str]],
    *,
    base_sha: str,
    head_sha: str,
    base_package_catalog: Mapping[str, dict[str, Any]] | None = None,
    head_package_catalog: Mapping[str, dict[str, Any]] | None = None,
    registry_envelopes_equal: bool | Mapping[str, bool] = True,
) -> dict[str, object]:
    """Purely resolve parsed Git entries into deterministic affected targets."""

    graph, producers = _closed_graph(core)
    rules = graph["rules"]
    canonical_scripts = _canonical_producer_script_ownership(graph, producers)
    base_catalog = base_package_catalog or {}
    head_catalog = head_package_catalog or {}
    no_impact_patterns = graph["known_no_impact_patterns"]
    test_self_patterns = graph["stages"]["ci-tests"]["test_self_patterns"]
    runtime_projection = _runtime_contract(graph)
    decisions: list[dict[str, object]] = []
    direct_reasons: dict[str, list[list[str]]] = {}
    direct_test_modules: set[str] = set()

    for status, path in entries:
        if status not in {"A", "M", "D"}:
            raise ImpactGraphError(
                "unsupported-status", f"unsupported Git status {status!r} for {path!r}"
            )
        if not _safe_changed_path(path):
            raise ImpactGraphError("unsafe-path", "changed path is not repository-relative")
        matching_rules = [
            rule
            for rule in rules
            if any(_matches(path, pattern) for pattern in rule["path_patterns"])
        ]
        no_impact = any(_matches(path, pattern) for pattern in no_impact_patterns)
        self_selected = any(_matches(path, pattern) for pattern in test_self_patterns)
        if len(matching_rules) > 1 or (matching_rules and no_impact):
            raise ImpactGraphError(
                "ambiguous-classification",
                f"path {path!r} matches multiple impact classifications",
            )
        # Canonical argv ownership closes otherwise-unmatched producer scripts.
        # An explicit impact rule remains the sole owner when one already exists;
        # merging the fallback would widen its declared producer and test set.
        canonical_script = canonical_scripts.get(path) if not matching_rules else None
        if not matching_rules and canonical_script is not None:
            matching_rules = [
                {
                    "id": "canonical-producer-script:"
                    + "+".join(canonical_script["producer_ids"]),
                    "path_patterns": [path],
                    "producer_ids": canonical_script["producer_ids"],
                    "test_modules": canonical_script["test_modules"],
                }
            ]
        if not matching_rules and not no_impact and not self_selected:
            raise ImpactGraphError(
                "unmatched-path", f"path {path!r} has no Core impact classification"
            )

        rule = matching_rules[0] if matching_rules else None
        producer_ids = list(rule["producer_ids"]) if rule is not None else []
        if canonical_script is not None:
            producer_ids.extend(canonical_script["producer_ids"])
        runtime_selected = _entry_selects_runtime(
            status,
            path,
            base_package_catalog=base_catalog,
            head_package_catalog=head_catalog,
            projection=runtime_projection,
        )
        if runtime_selected:
            producer_ids.append(runtime_projection["producer_id"])
        producer_ids = list(dict.fromkeys(producer_ids))
        test_modules = set(rule["test_modules"]) if rule is not None else set()
        if canonical_script is not None:
            test_modules.update(canonical_script["test_modules"])
        if self_selected and status != "D":
            test_modules.add(path)
        direct_test_modules.update(test_modules)
        static_producer_ids = set(rule["producer_ids"]) if rule is not None else set()
        canonical_producer_ids = (
            set(canonical_script["producer_ids"])
            if canonical_script is not None
            else set()
        )
        for producer_id in producer_ids:
            if producer_id in static_producer_ids:
                selector = f"rule:{rule['id']}"
            elif producer_id in canonical_producer_ids:
                selector = "canonical-producer-argv"
            else:
                selector = "runtime-projection"
            chain = [
                f"path:{path}",
                selector,
                f"producer:{producer_id}",
            ]
            bucket = direct_reasons.setdefault(producer_id, [])
            if chain not in bucket:
                bucket.append(chain)
        if rule is not None:
            classification = "rule"
            rationale = "Core impact rule selected canonical targets"
        elif self_selected:
            classification = "test-self"
            rationale = (
                "deleted unit test remains classified but is not runnable"
                if status == "D"
                else "changed unit test selects itself"
            )
        else:
            classification = "known-no-impact"
            rationale = "Core contract declares no affected target"
        decisions.append(
            {
                "status": status,
                "path": path,
                "classification": classification,
                "rule_id": rule["id"] if rule is not None else None,
                "direct_producer_ids": sorted(producer_ids),
                "test_modules": sorted(test_modules),
                "rationale": rationale,
            }
        )

    professionalism = _professionalism_scope(
        graph,
        entries,
        base_package_catalog=base_catalog,
        head_package_catalog=head_catalog,
        registry_envelopes_equal=registry_envelopes_equal,
    )
    expert_panel_evidence = _expert_panel_evidence_impact(graph, entries)
    if professionalism["scope"] != "none":
        producer_id = _professionalism_contract(graph)["producer_id"]
        direct_reasons.setdefault(producer_id, []).extend(
            [
                [*chain, f"producer:{producer_id}"]
                for chain in professionalism["reason_chains"]
            ]
        )

    producer_ids, producer_explanations = _producer_closure(
        producers, direct_reasons
    )
    selected_runtime = (
        runtime_projection["runtime_name"]
        if runtime_projection["producer_id"] in producer_ids
        else None
    )
    professionalism_producer = _professionalism_contract(graph)["producer_id"]
    if (
        professionalism_producer in producer_ids
        and professionalism["scope"] == "none"
    ):
        professionalism = {
            "scope": "full",
            "direct_package_ids": [],
            "reason_chains": [
                [
                    f"producer:{professionalism_producer}",
                    "professionalism:canonical-producer-closure",
                    "scope:full",
                ]
            ],
        }
    reason = (
        "empty-diff"
        if not entries
        else "known-no-impact"
        if decisions
        and all(item["classification"] == "known-no-impact" for item in decisions)
        else "affected-targets"
    )
    grouped_tests, selected_tests = _affected_test_projection(
        graph, direct_test_modules
    )
    return {
        "schema_version": 1,
        "kind": "changeforge.impact_selection",
        "base_sha": base_sha,
        "head_sha": head_sha,
        "status": "resolved",
        "reason": reason,
        "changed_paths": decisions,
        "selected_producer_ids": producer_ids,
        "selected_runtime": selected_runtime,
        "selected_test_modules_by_layer": grouped_tests,
        "selected_test_modules": selected_tests,
        "producer_explanations": producer_explanations,
        "professionalism": professionalism,
        "expert_panel_evidence": expert_panel_evidence,
    }


def _revision_package_catalog(
    root: Path,
    revision: str,
    graph: dict[str, Any],
) -> tuple[dict[str, dict[str, Any]], dict[str, object]]:
    catalog: dict[str, dict[str, Any]] = {}
    envelopes: dict[str, object] = {}
    for source in _professionalism_contract(graph)["registry_sources"]:
        path = source["path"]
        shown = _run_git(root, ["show", f"{revision}:{path}"])
        if shown.returncode != 0:
            raise ImpactGraphError(
                "invalid-package-catalog",
                f"cannot read {path!r} at revision {revision!r}",
            )
        try:
            value = load_yaml_text(
                shown.stdout.decode("utf-8"), Path(f"{revision}:{path}")
            )
        except (UnicodeError, ValidationProblem) as exc:
            raise ImpactGraphError(
                "invalid-package-catalog", f"cannot parse {path!r}"
            ) from exc
        collection = source["collection"]
        if not isinstance(value, dict) or not isinstance(value.get(collection), list):
            raise ImpactGraphError(
                "invalid-package-catalog", f"{path!r} lacks {collection!r}"
            )
        envelopes[path] = {
            key: value[key] for key in sorted(value) if key != collection
        }
        for entry in value[collection]:
            if not isinstance(entry, dict):
                raise ImpactGraphError(
                    "invalid-package-catalog", f"{path!r} has a non-object entry"
                )
            skill_id = entry.get("name")
            package_path = entry.get("path")
            if (
                not isinstance(skill_id, str)
                or not skill_id
                or not isinstance(package_path, str)
                or not package_path
                or skill_id in catalog
            ):
                raise ImpactGraphError(
                    "invalid-package-catalog", f"{path!r} has an invalid package entry"
                )
            catalog[skill_id] = {
                "skill_id": skill_id,
                "layer": source["layer"],
                "path": package_path,
                "registry_path": path,
                "registry_entry": entry,
            }
    return dict(sorted(catalog.items())), envelopes


def _run_git(
    root: Path,
    arguments: Sequence[str],
) -> subprocess.CompletedProcess[bytes]:
    environment = {
        **os.environ,
        "GIT_OPTIONAL_LOCKS": "0",
        "LC_ALL": "C",
    }
    return subprocess.run(
        ["git", *arguments],
        cwd=root,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=environment,
    )


def _parse_name_status_z(payload: bytes) -> list[tuple[str, str]]:
    fields = payload.split(b"\0")
    if fields and fields[-1] == b"":
        fields.pop()
    entries: list[tuple[str, str]] = []
    index = 0
    while index < len(fields):
        status = fields[index].decode("ascii", "strict")
        index += 1
        if not status:
            raise ImpactGraphError("malformed-diff", "Git returned an empty status")
        kind = status[0]
        if kind in {"R", "C"}:
            if index + 1 >= len(fields):
                raise ImpactGraphError(
                    "malformed-diff", "Git returned a truncated rename or copy"
                )
            old_path = fields[index].decode("utf-8", "surrogateescape")
            new_path = fields[index + 1].decode("utf-8", "surrogateescape")
            entries.extend([("D", old_path), ("A", new_path)])
            index += 2
            continue
        if index >= len(fields):
            raise ImpactGraphError(
                "malformed-diff", "Git returned a status without a path"
            )
        path = fields[index].decode("utf-8", "surrogateescape")
        entries.append((kind, path))
        index += 1
    return entries


def _valid_revision(revision: str | None) -> bool:
    return bool(revision and HEX_REVISION.fullmatch(revision))


def select(
    root: Path,
    core: dict[str, Any],
    base_sha: str | None,
    head_sha: str | None,
) -> dict[str, object]:
    """Resolve an exact commit range or raise a stable fail-closed error."""

    if not base_sha or not head_sha:
        raise ImpactGraphError("missing-revision", "both --base and --head are required")
    if not _valid_revision(base_sha) or not _valid_revision(head_sha):
        raise ImpactGraphError(
            "malformed-revision", "revisions must be full 40-character commit IDs"
        )
    if base_sha == "0" * 40 or head_sha == "0" * 40:
        raise ImpactGraphError("malformed-revision", "zero revisions are not commits")
    for revision in (base_sha, head_sha):
        exists = _run_git(root, ["cat-file", "-e", f"{revision}^{{commit}}"])
        if exists.returncode != 0:
            raise ImpactGraphError(
                "missing-revision", f"commit {revision!r} does not exist"
            )
    changed = _run_git(
        root,
        [
            "diff",
            "--name-status",
            "-z",
            "--find-renames",
            "--no-ext-diff",
            "--no-textconv",
            base_sha,
            head_sha,
        ],
    )
    if changed.returncode != 0:
        raise ImpactGraphError("git-diff-failed", "Git could not compare revisions")
    try:
        entries = _parse_name_status_z(changed.stdout)
    except UnicodeError as exc:
        raise ImpactGraphError("malformed-diff", "Git diff encoding is invalid") from exc
    graph, _producers = _closed_graph(core)
    base_catalog, base_envelopes = _revision_package_catalog(root, base_sha, graph)
    head_catalog, head_envelopes = _revision_package_catalog(root, head_sha, graph)
    envelope_equal = {
        path: base_envelopes.get(path) == head_envelopes.get(path)
        for path in set(base_envelopes) | set(head_envelopes)
    }
    return resolve_entries(
        core,
        entries,
        base_sha=base_sha,
        head_sha=head_sha,
        base_package_catalog=base_catalog,
        head_package_catalog=head_catalog,
        registry_envelopes_equal=envelope_equal,
    )

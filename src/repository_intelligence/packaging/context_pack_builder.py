"""Build minimal task context packs from repository graphs."""

from __future__ import annotations

import shlex
from pathlib import Path
from typing import Any

from repository_intelligence.cache.freshness import indexed_commit
from repository_intelligence.cache.repo_hash import stable_artifact_hash, stable_repo_hash
from repository_intelligence.graph.evidence import (
    attach_edge_evidence,
    build_edge_evidence,
    closure_eligible,
    confidence_score,
    evidence_from_node,
    freshness_score,
    refresh_node_evidence,
)
from repository_intelligence.graph.file_classifier import classify_role, normalize_repo_path
from repository_intelligence.graph.generated_artifact_graph import (
    generated_edit_policy,
    generated_reason,
    generated_source_of_truth,
    is_generated_artifact_path,
)
from repository_intelligence.graph.ownership_graph import owner_for_path
from repository_intelligence.ranking.graph_walk import walk_related_paths
from repository_intelligence.ranking.relevance_ranker import rank_files
from repository_intelligence.ranking.token_budget import apply_budget_mode, normalize_budget_profile, trim_items_by_budget


MAX_RELEVANT_FILES = 36
MAX_RELEVANT_SYMBOLS = 80
MAX_SELECTED_EDGES = 80


def _graph_payload(graph: dict[str, Any]) -> dict[str, Any]:
    return graph.get("repository_graph", graph)


def _normal_changed_paths(changed_paths: list[str], repo_root: str | Path | None = None) -> list[str]:
    return [normalize_repo_path(path, repo_root) for path in changed_paths]


def _edge_reason(path: str, seed_paths: set[str], edges: list[dict[str, Any]]) -> str:
    if path in seed_paths:
        return "direct_owner"
    for edge in edges:
        if edge.get("from") in seed_paths and edge.get("to") == path:
            edge_type = edge.get("type")
            if edge_type == "import":
                return "callee"
            if edge_type in {"test_reference", "validator_reference", "hook_template_reference"}:
                return edge_type.removesuffix("_reference")
            if edge_type == "generated_artifact":
                return "generated_artifact"
            return "doc" if edge_type == "doc_reference" else "config"
        if edge.get("to") in seed_paths and edge.get("from") == path:
            edge_type = edge.get("type")
            if edge_type == "import":
                return "caller"
            if edge_type == "test_reference":
                return "test"
            if edge_type == "validator_reference":
                return "validator"
            return "config"
    role = classify_role(path)
    return "test" if role == "test" else "doc" if role == "docs" else "config"


def _command_path(value: str | Path | None, placeholder: str) -> str:
    if value is None or str(value).strip() == "":
        return placeholder
    return shlex.quote(str(value))


def _validation_candidates(
    relevant_paths: list[str],
    changed_paths: list[str],
    *,
    graph_path: str | Path | None = None,
    context_pack_path: str | Path | None = None,
    graph_freshness: str = "unknown",
    graph_validation_candidates: list[dict[str, object]] | None = None,
) -> list[dict[str, object]]:
    paths = set(relevant_paths) | set(changed_paths)
    graph_arg = _command_path(graph_path, "<repository_graph_json>")
    context_pack_arg = _command_path(context_pack_path, "<task_context_pack_json>")
    candidates: list[dict[str, object]] = [
        {
            "command": f"python3 scripts/validate-repository-graph.py --graph {graph_arg}",
            "proves": "repository graph schema, path, dist, and secret-safety invariants",
            "scope": "narrow",
            "source": "repository_intelligence",
            "covered_paths": sorted(paths),
            "covered_risk_surfaces": ["repository-graph", "source-freshness"],
            "confidence": "medium",
            "freshness": graph_freshness,
            "strength": "strong" if graph_freshness == "current" else "conservative",
        },
        {
            "command": f"python3 scripts/validate-context-pack.py --context-pack {context_pack_arg}",
            "proves": "context pack schema, source-of-truth, freshness, validation, and secret-safety invariants",
            "scope": "narrow",
            "source": "repository_intelligence",
            "covered_paths": sorted(paths),
            "covered_risk_surfaces": ["context-pack", "source-freshness"],
            "confidence": "medium",
            "freshness": graph_freshness,
            "strength": "strong" if graph_freshness == "current" else "conservative",
        },
    ]
    for candidate in graph_validation_candidates or []:
        if candidate.get("command") and candidate.get("proves"):
            candidates.append(candidate)
    candidates.extend(_broker_validation_candidates(changed_paths or relevant_paths))
    return _dedupe_candidates(candidates)


def _broker_validation_candidates(paths: list[str]) -> list[dict[str, object]]:
    try:
        from validation_broker.command_resolver import resolve_validation_plan
    except Exception:
        return [
            {
                "command": "python3 -m unittest discover -s tests",
                "proves": "repository unit and regression test suite still passes",
                "scope": "module",
                "source": "fallback",
                "covered_paths": sorted(set(paths)),
                "covered_risk_surfaces": ["regression"],
            }
        ]
    plan = resolve_validation_plan(paths)
    candidates: list[dict[str, object]] = []
    for field in ("recommended_commands", "full_commands"):
        for item in plan.get(field, []) or []:
            if not isinstance(item, dict):
                continue
            command = str(item.get("command") or "").strip()
            if not command:
                continue
            candidates.append(
                {
                    "command": command,
                    "proves": str(item.get("reason") or "validation broker candidate"),
                    "scope": str(item.get("level") or item.get("scope") or "unknown"),
                    "source": "validation_broker",
                    "category": str(item.get("category") or "unknown"),
                    "covered_paths": list(item.get("covered_path_patterns", []) or []),
                    "covered_risk_surfaces": list(item.get("covered_risk_surfaces", []) or []),
                    "confidence": "medium",
                    "freshness": "not_applicable",
                    "strength": "strong",
                }
            )
    return candidates


def _dedupe_candidates(candidates: list[dict[str, object]]) -> list[dict[str, object]]:
    result: list[dict[str, object]] = []
    seen: set[str] = set()
    for candidate in candidates:
        command = " ".join(str(candidate.get("command") or "").split())
        if not command or command in seen:
            continue
        seen.add(command)
        result.append(candidate)
    return result


def _relevant_symbols(
    files_by_path: dict[str, dict[str, Any]],
    relevant_paths: list[str],
    max_symbols: int = MAX_RELEVANT_SYMBOLS,
) -> list[dict[str, object]]:
    symbols: list[dict[str, object]] = []
    for path in relevant_paths:
        node = files_by_path.get(path)
        if not node:
            continue
        for symbol in node.get("symbols", []):
            if not isinstance(symbol, dict):
                continue
            symbols.append(
                {
                    "name": symbol.get("name"),
                    "symbol": symbol.get("name"),
                    "path": path,
                    "file": path,
                    "kind": symbol.get("kind", "registry_entry"),
                    "line": symbol.get("line") or symbol.get("line_start") or 0,
                    "line_start": symbol.get("line_start") or symbol.get("line") or 0,
                    "line_end": symbol.get("line_end") or symbol.get("line_start") or symbol.get("line") or 0,
                    "visibility": symbol.get("visibility", "public"),
                    "owner_object": symbol.get("owner_object"),
                    "parent_symbol": symbol.get("parent_symbol"),
                    "language": symbol.get("language") or node.get("kind"),
                    "confidence": symbol.get("confidence", "medium"),
                }
            )
            if len(symbols) >= max_symbols:
                return symbols
    return symbols


def _freshness(payload: dict[str, Any], repo_root: str | Path | None) -> dict[str, object]:
    markers = dict(payload.get("freshness") or {})
    if not markers:
        markers = {
            "repo_hash": payload.get("repo_hash"),
            "artifact_hash": payload.get("artifact_hash"),
            "created_at": payload.get("created_at") or payload.get("indexed_at"),
            "commit_sha": payload.get("commit_sha") or payload.get("indexed_commit"),
            "indexed_at": payload.get("indexed_at"),
            "indexed_commit": payload.get("indexed_commit"),
        }
    status = str(markers.get("status") or "unknown")
    drift: list[str] = []
    if repo_root is not None:
        current_repo_hash = stable_repo_hash(repo_root)
        current_artifact_hash = stable_artifact_hash(repo_root)
        current_commit = indexed_commit(repo_root)
        markers["current_repo_hash"] = current_repo_hash
        markers["current_artifact_hash"] = current_artifact_hash
        markers["current_commit_sha"] = current_commit
        if markers.get("repo_hash") and markers.get("repo_hash") != current_repo_hash:
            status = "stale"
            drift.append("repo_hash_mismatch")
        if markers.get("artifact_hash") and markers.get("artifact_hash") != current_artifact_hash:
            drift.append("artifact_hash_mismatch")
        if markers.get("commit_sha") and current_commit and markers.get("commit_sha") != current_commit:
            status = "stale"
            drift.append("commit_mismatch")
    markers["status"] = status
    markers["drift"] = drift
    return markers


def _selected_edges(edges: list[dict[str, Any]], selected_paths: list[str]) -> list[dict[str, Any]]:
    selected = set(selected_paths)
    return [
        edge
        for edge in edges
        if edge.get("from") in selected or edge.get("to") in selected
    ][:MAX_SELECTED_EDGES]


def _edge_bucket(edges: list[dict[str, Any]], selected_paths: list[str], edge_types: set[str]) -> list[dict[str, Any]]:
    selected = set(selected_paths)
    return [
        edge
        for edge in edges
        if edge.get("type") in edge_types and (edge.get("from") in selected or edge.get("to") in selected)
    ][:MAX_SELECTED_EDGES]


def _imports(files_by_path: dict[str, dict[str, Any]], selected_paths: list[str]) -> list[dict[str, object]]:
    imports: list[dict[str, object]] = []
    for path in selected_paths:
        for item in files_by_path.get(path, {}).get("imports", []) or []:
            if isinstance(item, dict):
                imports.append({"path": path, **item})
    return imports[:MAX_SELECTED_EDGES]


def _references(files_by_path: dict[str, dict[str, Any]], selected_paths: list[str]) -> list[dict[str, object]]:
    refs: list[dict[str, object]] = []
    for path in selected_paths:
        for item in files_by_path.get(path, {}).get("references", []) or []:
            if isinstance(item, dict):
                refs.append({"path": path, **item})
    return refs[:MAX_SELECTED_EDGES]


def _ownership_for_paths(payload: dict[str, Any], paths: list[str]) -> list[dict[str, object]]:
    wanted = set(paths)
    ownership = [
        item
        for item in payload.get("ownership", []) or []
        if isinstance(item, dict) and item.get("path") in wanted
    ]
    if ownership:
        return ownership
    return [owner_for_path(path) for path in paths]


def _generated_for_paths(
    payload: dict[str, Any],
    changed_paths: list[str],
    files_by_path: dict[str, dict[str, Any]],
) -> list[dict[str, object]]:
    generated = [item for item in payload.get("generated_artifacts", []) or [] if isinstance(item, dict)]
    result: list[dict[str, object]] = []
    for path in changed_paths:
        matched = False
        for item in generated:
            prefix = str(item.get("generated_path") or "")
            if prefix and (path == prefix.rstrip("/") or path == prefix or path.startswith(prefix)):
                result.append(item)
                matched = True
        if is_generated_artifact_path(path) and not matched:
            source_of_truth = generated_source_of_truth(path, files_by_path)
            result.append(
                {
                    "generated_path": path,
                    "source_path": source_of_truth[0] if source_of_truth else None,
                    "source_of_truth": source_of_truth,
                    "reason": generated_reason(path, files_by_path),
                    "edit_policy": generated_edit_policy(path, files_by_path),
                    "editable": False,
                    "confidence": "medium" if source_of_truth else "low",
                    "freshness": "not_applicable",
                    "extractor": "generated_artifact_graph",
                    **({"unknown_reason": "generated_source_of_truth_unknown"} if not source_of_truth else {}),
                }
            )
    return result


def _related_tests(
    files_by_path: dict[str, dict[str, Any]],
    edges: list[dict[str, Any]],
    relevant_paths: list[str],
) -> list[dict[str, object]]:
    relevant = set(relevant_paths)
    tests: list[dict[str, object]] = []
    for edge in edges:
        if edge.get("type") != "test_reference":
            continue
        source = str(edge.get("from") or "")
        target = str(edge.get("to") or "")
        if source in relevant or target in relevant:
            test_path = source if files_by_path.get(source, {}).get("role") == "test" else target
            if files_by_path.get(test_path, {}).get("role") == "test":
                tests.append(
                    {
                        "path": test_path,
                        "reason": "FACT: test_reference edge from repository graph",
                        "confidence": edge.get("confidence", "unknown"),
                        "freshness": edge.get("freshness", "unknown"),
                        "source": "repository_graph.test_graph",
                        "strength": _candidate_strength(edge.get("confidence"), edge.get("freshness")),
                    }
                )
    for path in relevant_paths:
        if files_by_path.get(path, {}).get("role") == "test":
            evidence = evidence_from_node(files_by_path[path])
            tests.append(
                {
                    "path": path,
                    "reason": "FACT: selected path is a test file",
                    "confidence": evidence.get("confidence", "unknown"),
                    "freshness": evidence.get("freshness", "unknown"),
                    "source": "repository_graph.file_role",
                    "strength": _candidate_strength(evidence.get("confidence"), evidence.get("freshness")),
                }
            )
    return _dedupe_path_items(tests)


def _dedupe_path_items(items: list[dict[str, object]]) -> list[dict[str, object]]:
    result: list[dict[str, object]] = []
    seen: set[str] = set()
    for item in items:
        path = item.get("path", "")
        if not path or path in seen:
            continue
        seen.add(path)
        result.append(item)
    return result


def _candidate_strength(confidence: object, freshness: object) -> str:
    if freshness == "current" and confidence in {"high", "medium"}:
        return "strong"
    return "conservative"


def _refresh_files(
    files: list[Any],
    repo_root: str | Path | None,
) -> list[dict[str, Any]]:
    refreshed: list[dict[str, Any]] = []
    for file_node in files:
        if isinstance(file_node, dict):
            refreshed.append(refresh_node_evidence(file_node, repo_root))
    return refreshed


def _refresh_edges(
    edges: list[Any],
    files_by_path: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    refreshed: list[dict[str, Any]] = []
    for edge in edges:
        if not isinstance(edge, dict):
            continue
        edge_payload = dict(edge)
        attach_edge_evidence(edge_payload, build_edge_evidence(edge_payload, files_by_path))
        refreshed.append(edge_payload)
    return refreshed


def _order_paths_by_evidence(
    paths: list[str],
    files_by_path: dict[str, dict[str, Any]],
    seed_paths: set[str],
) -> list[str]:
    return sorted(
        paths,
        key=lambda path: (
            0 if path in seed_paths else 1,
            -freshness_score(evidence_from_node(files_by_path.get(path, {})).get("freshness")),
            -confidence_score(evidence_from_node(files_by_path.get(path, {})).get("confidence")),
            path,
        ),
    )


def _graph_node_item(path: str, node: dict[str, Any], reason: str) -> dict[str, object]:
    evidence = evidence_from_node(node)
    return {
        "path": path,
        "reason": reason,
        "node_type": evidence.get("node_type", "unknown"),
        "confidence": evidence.get("confidence", "unknown"),
        "freshness": evidence.get("freshness", "unknown"),
        "extractor": evidence.get("extractor", "unknown"),
        "source_hash": evidence.get("source_hash"),
        "generated_artifact": evidence.get("generated_artifact", False),
        "source_of_truth": evidence.get("source_of_truth"),
        **({"unknown_reason": evidence.get("unknown_reason")} if evidence.get("unknown_reason") else {}),
    }


def _selected_graph_nodes(
    files_by_path: dict[str, dict[str, Any]],
    relevant_paths: list[str],
    graph_freshness: str,
) -> list[dict[str, object]]:
    if graph_freshness != "current":
        return []
    selected: list[dict[str, object]] = []
    for path in relevant_paths:
        node = files_by_path.get(path)
        if node and closure_eligible(evidence_from_node(node)):
            selected.append(_graph_node_item(path, node, "current medium/high confidence graph evidence"))
    return selected


def _skipped_graph_nodes(
    files_by_path: dict[str, dict[str, Any]],
    relevant_paths: list[str],
    graph_freshness: str,
) -> list[dict[str, object]]:
    skipped: list[dict[str, object]] = []
    for path in relevant_paths:
        node = files_by_path.get(path)
        if not node:
            continue
        evidence = evidence_from_node(node)
        if graph_freshness != "current":
            reason = "graph_freshness_not_current"
        elif not closure_eligible(evidence):
            reason = "freshness_or_confidence_not_closure_eligible"
        else:
            continue
        skipped.append(_graph_node_item(path, node, reason))
    return skipped


def _graph_assumptions(
    *,
    graph_freshness: dict[str, object],
    skipped_graph_nodes: list[dict[str, object]],
) -> list[dict[str, object]]:
    assumptions: list[dict[str, object]] = []
    if graph_freshness.get("status") != "current":
        assumptions.append(
            {
                "kind": "graph_freshness",
                "freshness": graph_freshness.get("status", "unknown"),
                "reason": "graph freshness is not current; selected graph facts are selectors, not closure evidence",
            }
        )
    for node in skipped_graph_nodes[:24]:
        assumptions.append(
            {
                "kind": "graph_node",
                "path": node.get("path"),
                "freshness": node.get("freshness", "unknown"),
                "confidence": node.get("confidence", "unknown"),
                "reason": node.get("reason", "not_closure_eligible"),
            }
        )
    return assumptions


def _validation_command_for_tests(candidate_tests: list[str]) -> str:
    if not candidate_tests:
        return "python3 -m unittest discover -s tests"
    directories = {str(Path(path).parent) for path in candidate_tests}
    if len(directories) == 1:
        return f"python3 -m unittest discover -s {next(iter(directories))}"
    return "python3 -m unittest discover -s tests"


def _graph_validation_candidates(
    *,
    changed_paths: list[str],
    related_tests: list[dict[str, object]],
    files_by_path: dict[str, dict[str, Any]],
    graph_freshness: str,
) -> list[dict[str, object]]:
    candidates: list[dict[str, object]] = []
    tests_by_changed: dict[str, list[dict[str, object]]] = {path: [] for path in changed_paths}
    for test in related_tests:
        for changed_path in changed_paths:
            if changed_path == test.get("path"):
                tests_by_changed.setdefault(changed_path, []).append(test)
                continue
            if _test_matches_changed_path(str(test.get("path") or ""), changed_path):
                tests_by_changed.setdefault(changed_path, []).append(test)

    for changed_path in changed_paths:
        node = files_by_path.get(changed_path)
        evidence = evidence_from_node(node) if node else {}
        related = tests_by_changed.get(changed_path, [])
        candidate_tests = sorted({str(item.get("path")) for item in related if item.get("path")})
        confidence = _combined_confidence(evidence, related)
        freshness = _combined_freshness(evidence, related, graph_freshness)
        strength = _candidate_strength(confidence, freshness) if candidate_tests else "conservative"
        reason = (
            "current test graph candidate"
            if candidate_tests and strength == "strong"
            else "conservative suggestion; graph evidence is stale, unknown, low confidence, or has no direct test edge"
        )
        command = _validation_command_for_tests(candidate_tests)
        candidates.append(
            {
                "changed_path": changed_path,
                "candidate_tests": candidate_tests,
                "confidence": confidence,
                "source": "repository_graph.test_mapping",
                "freshness": freshness,
                "reason": reason,
                "strength": strength,
                "command": command,
                "proves": reason,
                "scope": "module" if candidate_tests else "full",
                "category": "repository_intelligence_graph_candidate" if strength == "strong" else "unknown",
                "covered_paths": [changed_path, *candidate_tests],
                "covered_risk_surfaces": ["affected-tests", "repository-graph"],
            }
        )
    return candidates


def _test_matches_changed_path(test_path: str, changed_path: str) -> bool:
    if not test_path or not changed_path:
        return False
    return Path(test_path).stem.removeprefix("test_") == Path(changed_path).stem


def _combined_confidence(evidence: dict[str, object], related_tests: list[dict[str, object]]) -> str:
    values = [str(evidence.get("confidence") or "unknown")]
    values.extend(str(item.get("confidence") or "unknown") for item in related_tests)
    best = max(values, key=confidence_score)
    return best if best in {"high", "medium", "low"} else "unknown"


def _combined_freshness(
    evidence: dict[str, object],
    related_tests: list[dict[str, object]],
    graph_freshness: str,
) -> str:
    values = [graph_freshness, str(evidence.get("freshness") or "unknown")]
    values.extend(str(item.get("freshness") or "unknown") for item in related_tests)
    if "stale" in values:
        return "stale"
    if values and all(value in {"current", "not_applicable"} for value in values):
        return "current"
    return "unknown"


def _reuse_candidates(
    files_by_path: dict[str, dict[str, Any]],
    selected_paths: list[str],
    ownership: list[dict[str, object]],
) -> list[dict[str, str]]:
    candidates: list[dict[str, str]] = []
    selected = set(selected_paths)
    owner_modules = {str(item.get("owner_module")) for item in ownership if item.get("owner_module")}
    for path in sorted(files_by_path):
        if path in selected:
            continue
        owner = owner_for_path(path)
        if str(owner.get("owner_module")) in owner_modules:
            candidates.append({"path": path, "reason": "same owner module; inspect before adding parallel structure"})
        if len(candidates) >= 24:
            break
    return candidates


def _rejected_locations(ownership: list[dict[str, object]]) -> list[dict[str, object]]:
    rejected: list[dict[str, object]] = []
    for item in ownership:
        values = item.get("rejected_dumping_ground_candidates", [])
        if isinstance(values, list):
            rejected.extend(value for value in values if isinstance(value, dict))
    return rejected[:24]


def _omitted_nodes(files_by_path: dict[str, dict[str, Any]], selected_paths: list[str]) -> list[dict[str, object]]:
    selected = set(selected_paths)
    omitted = [path for path in sorted(files_by_path) if path not in selected]
    nodes = [{"path": path, "reason": "omitted_by_context_budget"} for path in omitted[:24]]
    if len(omitted) > 24:
        nodes.append({"path": "<additional omitted files>", "count": len(omitted) - 24, "reason": "omitted_by_context_budget"})
    return nodes


def _int_line(value: object) -> int | None:
    try:
        line = int(value or 0)
    except (TypeError, ValueError):
        return None
    return line if line > 0 else None


def _line_hint_for_node(node: dict[str, Any]) -> str | None:
    kind = str(node.get("kind") or "")
    for symbol in node.get("symbols", []) or []:
        if not isinstance(symbol, dict):
            continue
        line_start = _int_line(symbol.get("line_start") or symbol.get("line"))
        line_end = _int_line(symbol.get("line_end") or symbol.get("line_start") or symbol.get("line"))
        if kind == "python" and line_start and line_end:
            return f"{line_start}-{line_end}"
        if kind == "markdown" and str(symbol.get("kind") or "") == "heading" and line_start:
            return f"line {line_start}"
        if kind in {"yaml", "json"} and str(symbol.get("kind") or "") == "config_key" and line_start:
            return f"line {line_start}"
    return None


def _read_policy_for_node(node: dict[str, Any], line_hint: str | None) -> str:
    if str(node.get("kind") or "") == "markdown" and line_hint:
        return "read_heading_only"
    if line_hint:
        return "read_slice"
    return "read_full_if_small"


def _source_truth_status(
    path: str,
    files_by_path: dict[str, dict[str, Any]],
    source_paths: set[str],
) -> str:
    node = files_by_path.get(path)
    if is_generated_artifact_path(path) or (node and node.get("role") == "generated_artifact"):
        return "generated"
    if path in source_paths or node:
        return "source"
    return "unknown"


def _jit_discovery_plan(
    *,
    graph_path: str | Path | None,
    context_pack_path: str | Path | None,
) -> list[dict[str, str]]:
    graph_arg = _command_path(graph_path, "<repository_graph_json>")
    context_pack_arg = _command_path(context_pack_path, "<task_context_pack_json>")
    return [
        {
            "command": f"python3 scripts/validate-repository-graph.py --graph {graph_arg}",
            "purpose": "verify repository graph schema, freshness, path safety, generated boundaries, and secret-safety before using graph selectors",
            "expected_output_policy": "bounded_summary",
        },
        {
            "command": f"python3 scripts/validate-context-pack.py --context-pack {context_pack_arg}",
            "purpose": "verify TaskContextPack schema, context-control counts, JIT read plan, path safety, artifact policy, and secret-safety",
            "expected_output_policy": "bounded_summary",
        },
    ]


def _targeted_reads(
    *,
    selected_files: list[dict[str, object]],
    files_by_path: dict[str, dict[str, Any]],
    source_paths: set[str],
) -> list[dict[str, object]]:
    reads: list[dict[str, object]] = []
    for item in selected_files:
        path = str(item.get("path") or "")
        if not path:
            continue
        node = files_by_path.get(path, {})
        line_hint = _line_hint_for_node(node)
        reads.append(
            {
                "path": path,
                "reason": str(item.get("reason") or "selected by task relevance and graph evidence"),
                "line_hint": line_hint,
                "read_policy": _read_policy_for_node(node, line_hint),
                "source_truth_status": _source_truth_status(path, files_by_path, source_paths),
            }
        )
    return reads


def _deferred_reads(
    *,
    reuse_candidates: list[dict[str, str]],
    omitted_nodes: list[dict[str, object]],
    selected_paths: set[str],
) -> list[dict[str, str]]:
    deferred: list[dict[str, str]] = []
    seen: set[str] = set(selected_paths)
    for item in reuse_candidates[:8]:
        path = str(item.get("path") or "")
        if path and path not in seen:
            seen.add(path)
            deferred.append({"path": path, "reason": str(item.get("reason") or "reuse candidate")})
    for item in omitted_nodes[:8]:
        path = str(item.get("path") or "")
        if path and not path.startswith("<") and path not in seen:
            seen.add(path)
            deferred.append({"path": path, "reason": str(item.get("reason") or "omitted by context budget")})
    return deferred


def _forbidden_reads(
    *,
    excluded_context: list[dict[str, str]],
    generated_artifacts: list[dict[str, object]],
) -> list[dict[str, str]]:
    forbidden: list[dict[str, str]] = []
    seen: set[str] = set()
    for item in excluded_context:
        path = str(item.get("path") or "")
        reason = str(item.get("reason") or "excluded context")
        if path and path not in seen:
            seen.add(path)
            forbidden.append({"path": path, "reason": reason})
    for item in generated_artifacts:
        path = str(item.get("generated_path") or "")
        if path and path not in seen:
            seen.add(path)
            forbidden.append({"path": path, "reason": "generated output; inspect source_of_truth instead"})
    return forbidden


def _residual_risk(
    *,
    freshness: dict[str, object],
    normalized_changed: list[str],
    present_changed: list[str],
    validation_candidates: list[dict[str, object]],
    graph_validation_candidates: list[dict[str, object]],
    generated_artifacts: list[dict[str, object]],
    selected_paths: list[str],
    files_by_path: dict[str, dict[str, Any]],
) -> list[dict[str, str]]:
    residual: list[dict[str, str]] = []
    if freshness.get("status") == "stale":
        residual.append({"kind": "stale_graph", "detail": ",".join(str(item) for item in freshness.get("drift", []) or [])})
    missing = [path for path in normalized_changed if path not in present_changed and not is_generated_artifact_path(path)]
    for path in missing:
        residual.append({"kind": "changed_path_not_indexed", "path": path})
    if any(str(candidate.get("category")) == "unknown" for candidate in validation_candidates):
        residual.append({"kind": "unknown_validation_mapping", "detail": "validation broker returned conservative unknown fallback"})
    if any(str(candidate.get("strength")) == "conservative" for candidate in graph_validation_candidates):
        residual.append({"kind": "conservative_graph_validation_mapping", "detail": "graph validation candidates include stale, unknown, low-confidence, or missing test mappings"})
    for item in generated_artifacts:
        residual.append({"kind": "generated_artifact_changed", "path": str(item.get("generated_path") or "")})
    for path in selected_paths:
        for ref in files_by_path.get(path, {}).get("references", []) or []:
            if isinstance(ref, dict) and ref.get("kind") == "index_error":
                residual.append({"kind": "index_error", "path": path, "detail": str(ref.get("value") or "")})
    return residual


def build_context_pack(
    graph: dict[str, Any],
    task_goal: str,
    changed_paths: list[str],
    repo_root: str | Path | None = None,
    max_files: int = MAX_RELEVANT_FILES,
    max_symbols: int = MAX_RELEVANT_SYMBOLS,
    context_budget_tokens: int = 1200,
    graph_path: str | Path | None = None,
    context_pack_path: str | Path | None = None,
    budget_mode: str = "single-stage",
    budget_profile: str = "authoring",
) -> dict[str, Any]:
    """Build a bounded AI-agent task context pack from a repository graph."""
    payload = _graph_payload(graph)
    budget_profile = normalize_budget_profile(budget_profile)
    max_files, max_symbols, context_budget_tokens, budget_mode = apply_budget_mode(
        budget_mode=budget_mode,
        max_files=max_files,
        max_symbols=max_symbols,
        context_budget_tokens=context_budget_tokens,
        budget_profile=budget_profile,
    )
    files = _refresh_files(payload.get("files", []), repo_root)
    files_by_path = {str(file_node.get("path")): file_node for file_node in files if isinstance(file_node, dict)}
    edges = _refresh_edges(payload.get("edges", []), files_by_path)
    normalized_changed = _normal_changed_paths(changed_paths, repo_root)
    present_changed = [path for path in normalized_changed if path in files_by_path]

    seed_paths = present_changed[:]
    if not seed_paths:
        ranked_for_task = rank_files(files, task_goal, normalized_changed, {})
        seed_paths = [path for path, _score in ranked_for_task[:5]]

    distances = walk_related_paths(seed_paths, edges, max_depth=2)
    ranked = rank_files(files, task_goal, normalized_changed, distances)
    ordered_paths = []
    for path in [*seed_paths, *[path for path, _score in ranked]]:
        if path not in ordered_paths and path in files_by_path:
            ordered_paths.append(path)
    seed_set = set(seed_paths)
    freshness = _freshness(payload, repo_root)
    ordered_paths = _order_paths_by_evidence(ordered_paths, files_by_path, seed_set)
    selected_paths = ordered_paths[:max_files]
    generated_artifacts = _generated_for_paths(payload, normalized_changed, files_by_path)

    source_of_truth: list[dict[str, str]] = []
    evidence_limits: list[str] = [
        "FACT: Repository graph is static; it does not execute Python, import modules, or evaluate dynamic runtime behavior.",
        "FACT: `dist/` is treated as generated output and is not indexed as source-of-truth.",
    ]
    for path in normalized_changed:
        if is_generated_artifact_path(path):
            matched_generated = _generated_for_paths(payload, [path], files_by_path)
            if matched_generated:
                for item in matched_generated:
                    for source in item.get("source_of_truth", []) or []:
                        source_of_truth.append(
                            {
                                "path": str(source),
                                "reason": f"FACT: `{path}` is generated from this source boundary",
                            }
                        )
            evidence_limits.append(f"FACT: Changed path `{path}` is generated-only; inspect its source owner instead of editing generated output.")
            continue
        if path in files_by_path:
            source_of_truth.append({"path": path, "reason": "FACT: changed path exists in indexed source graph"})
        else:
            evidence_limits.append(f"OPEN QUESTION: Changed path `{path}` was not present in the repository graph.")

    ownership = _ownership_for_paths(payload, selected_paths)
    selected_files = [
        {
            "path": path,
            "permitted_changes": "modify" if path in normalized_changed else "read-only",
            "reason": _edge_reason(path, seed_set, edges),
            "role": str(files_by_path.get(path, {}).get("role") or "unknown"),
            "owner_module": str(owner_for_path(path).get("owner_module") or "unknown"),
            "confidence": evidence_from_node(files_by_path.get(path, {})).get("confidence", "unknown"),
            "freshness": evidence_from_node(files_by_path.get(path, {})).get("freshness", "unknown"),
            "extractor": evidence_from_node(files_by_path.get(path, {})).get("extractor", "unknown"),
            "source_hash": evidence_from_node(files_by_path.get(path, {})).get("source_hash"),
            "evidence_role": "evidence"
            if freshness.get("status") == "current" and closure_eligible(evidence_from_node(files_by_path.get(path, {})))
            else "assumption",
        }
        for path in selected_paths
    ]
    selected_files = trim_items_by_budget(selected_files, context_budget_tokens)
    relevant_paths = [str(item["path"]) for item in selected_files]
    ownership = _ownership_for_paths(payload, relevant_paths)
    selected_symbols = _relevant_symbols(files_by_path, relevant_paths, max_symbols=max_symbols)

    related_tests = _related_tests(files_by_path, edges, relevant_paths)
    graph_validation_candidates = _graph_validation_candidates(
        changed_paths=normalized_changed,
        related_tests=related_tests,
        files_by_path=files_by_path,
        graph_freshness=str(freshness.get("status") or "unknown"),
    )

    validation_candidates = _validation_candidates(
        relevant_paths,
        normalized_changed,
        graph_path=graph_path,
        context_pack_path=context_pack_path,
        graph_freshness=str(freshness.get("status") or "unknown"),
        graph_validation_candidates=graph_validation_candidates,
    )
    selected_graph_nodes = _selected_graph_nodes(files_by_path, relevant_paths, str(freshness.get("status") or "unknown"))
    skipped_graph_nodes = _skipped_graph_nodes(files_by_path, relevant_paths, str(freshness.get("status") or "unknown"))
    graph_assumptions = _graph_assumptions(graph_freshness=freshness, skipped_graph_nodes=skipped_graph_nodes)
    residual_risk = _residual_risk(
        freshness=freshness,
        normalized_changed=normalized_changed,
        present_changed=present_changed,
        validation_candidates=validation_candidates,
        graph_validation_candidates=graph_validation_candidates,
        generated_artifacts=generated_artifacts,
        selected_paths=relevant_paths,
        files_by_path=files_by_path,
    )
    selected_edges = _selected_edges(edges, relevant_paths)
    omitted_nodes = _omitted_nodes(files_by_path, relevant_paths)
    rejected_locations = _rejected_locations(ownership)
    reuse_candidates = _reuse_candidates(files_by_path, relevant_paths, ownership)
    source_paths = {str(item.get("path")) for item in source_of_truth if item.get("path")}
    excluded_context = [
        {"path": "dist/", "reason": "generated_only"},
        {"path": ".git/", "reason": "unsafe"},
        {"path": "node_modules/", "reason": "too_broad"},
        {"path": ".venv/", "reason": "too_broad"},
    ]
    context_control = {
        "budget_mode": budget_mode,
        "budget_profile": budget_profile,
        "context_budget_tokens": context_budget_tokens,
        "max_file_count": max_files,
        "max_symbol_count": max_symbols,
        "selected_file_count": len(selected_files),
        "omitted_file_count": max(0, len(files_by_path) - len(selected_files)),
        "selected_symbol_count": len(selected_symbols),
        "selected_graph_node_count": len(selected_graph_nodes),
        "skipped_graph_node_count": len(skipped_graph_nodes),
        "signal_density_rationale": (
            "selected files are bounded by changed paths, graph distance, task relevance, "
            "freshness, confidence, and token budget; omitted graph nodes remain deferred reads"
        ),
    }
    jit_retrieval_plan = {
        "discovery": _jit_discovery_plan(graph_path=graph_path, context_pack_path=context_pack_path),
        "targeted_reads": _targeted_reads(
            selected_files=selected_files,
            files_by_path=files_by_path,
            source_paths=source_paths,
        ),
        "deferred_reads": _deferred_reads(
            reuse_candidates=reuse_candidates,
            omitted_nodes=omitted_nodes,
            selected_paths=set(relevant_paths),
        ),
        "forbidden_reads": _forbidden_reads(excluded_context=excluded_context, generated_artifacts=generated_artifacts),
    }
    artifact_policy = {
        "large_outputs": "artifact_reference_only",
        "full_graph_dump": "forbidden",
        "full_test_log_dump": "forbidden",
    }

    pack = {
        "task_context_pack": {
            "schema_version": 3,
            "task": task_goal,
            "task_goal": task_goal,
            "graph_source": {
                "path": str(graph_path) if graph_path else "<inline>",
                "repo_hash": payload.get("repo_hash"),
                "commit_sha": payload.get("commit_sha") or payload.get("indexed_commit"),
                "created_at": payload.get("created_at") or payload.get("indexed_at"),
            },
            "changed_paths": normalized_changed,
            "freshness": freshness,
            "context_control": context_control,
            "jit_retrieval_plan": jit_retrieval_plan,
            "artifact_policy": artifact_policy,
            "source_of_truth": source_of_truth,
            "selected_files": selected_files,
            "selected_graph_nodes": selected_graph_nodes,
            "skipped_graph_nodes": skipped_graph_nodes,
            "closure_evidence": selected_graph_nodes,
            "assumptions": graph_assumptions,
            "selected_symbols": selected_symbols,
            "caller_callee_edges": _edge_bucket(selected_edges, relevant_paths, {"import"}),
            "imports": _imports(files_by_path, relevant_paths),
            "references": _references(files_by_path, relevant_paths),
            "related_tests": related_tests,
            "generated_artifacts": generated_artifacts,
            "ownership": ownership,
            "reuse_candidates": reuse_candidates,
            "rejected_locations": rejected_locations,
            "anti_bloat_decision": {
                "budget_mode": budget_mode,
                "budget_profile": budget_profile,
                "max_files": max_files,
                "max_symbols": max_symbols,
                "context_budget_tokens": context_budget_tokens,
                "selected_file_count": len(selected_files),
                "selected_symbol_count": len(selected_symbols),
                "total_indexed_files": len(files_by_path),
                "omitted_node_count": max(0, len(files_by_path) - len(selected_files)),
                "selected_graph_node_count": len(selected_graph_nodes),
                "skipped_graph_node_count": len(skipped_graph_nodes),
                "decision": "bounded graph slice selected by changed paths, graph distance, freshness, confidence, and task relevance",
            },
            "omitted_nodes": omitted_nodes,
            "residual_risk": residual_risk,
            "relevant_files": selected_files,
            "relevant_symbols": selected_symbols,
            "local_conventions": [
                "FACT: Source skills and capabilities live under `src/`; installable runtime artifacts are built into `dist/`.",
                "FACT: Registry YAML files are source-of-truth for skill, capability, domain-extension, and routing relationships.",
                "INFERENCE: Files reached by import, registry, test, validator, or hook-template edges are likely review context, not automatic edit targets.",
                "ASSUMPTION: The task should remain inside repository-intelligence tooling unless the context pack identifies an explicit source owner.",
                "OPEN QUESTION: Dynamic imports, reflection, generated reports, and external CI behavior require separate verification.",
            ],
            "affected_tests": related_tests,
            "graph_validation_candidates": graph_validation_candidates,
            "validation_candidates": validation_candidates,
            "non_goals": [
                "Do not index or package personal archives, prompts, secrets, environment variables, or user-specific technical corpora.",
                "Do not treat `dist/` as source-of-truth.",
                "Do not expand context by dumping every repository file.",
            ],
            "excluded_context": excluded_context,
            "freshness_markers": {
                "repo_hash": payload.get("repo_hash"),
                "artifact_hash": payload.get("artifact_hash"),
                "indexed_at": payload.get("indexed_at"),
                "indexed_commit": payload.get("indexed_commit"),
                "status": freshness.get("status"),
                **({"fallback_mtime": payload.get("fallback_mtime")} if payload.get("fallback_mtime") is not None else {}),
            },
            "drift_triggers": [
                "Reindex when current repo hash differs from `freshness_markers.repo_hash`.",
                "Rebuild generated artifacts when artifact hash differs from `freshness_markers.artifact_hash`.",
                "Reindex when current git HEAD differs from `freshness_markers.indexed_commit`.",
                "Reindex when a changed path is absent from the graph or when no git commit is available and source mtimes advance.",
            ],
            "evidence_limits": evidence_limits,
        }
    }
    if not validation_candidates:
        pack["task_context_pack"]["validation_candidates"] = [
            {
                "command": "unknown",
                "proves": "No relevant validation candidate could be inferred from the graph.",
                "scope": "unknown",
                "source": "repository_intelligence",
            }
        ]
    return pack

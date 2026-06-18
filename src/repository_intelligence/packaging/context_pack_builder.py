"""Build minimal task context packs from repository graphs."""

from __future__ import annotations

import shlex
from pathlib import Path
from typing import Any

from repository_intelligence.graph.file_classifier import classify_role, normalize_repo_path
from repository_intelligence.ranking.graph_walk import walk_related_paths
from repository_intelligence.ranking.relevance_ranker import rank_files
from repository_intelligence.ranking.token_budget import trim_items_by_budget


MAX_RELEVANT_FILES = 36
MAX_RELEVANT_SYMBOLS = 80


def _graph_payload(graph: dict[str, Any]) -> dict[str, Any]:
    return graph.get("repository_graph", graph)


def _normal_changed_paths(changed_paths: list[str], repo_root: str | Path | None = None) -> list[str]:
    return [normalize_repo_path(path, repo_root) for path in changed_paths]


def _edge_reason(path: str, seed_paths: set[str], edges: list[dict[str, str]]) -> str:
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
) -> list[dict[str, str]]:
    paths = set(relevant_paths) | set(changed_paths)
    graph_arg = _command_path(graph_path, "<repository_graph_json>")
    context_pack_arg = _command_path(context_pack_path, "<task_context_pack_json>")
    candidates = [
        {
            "command": f"python3 scripts/validate-repository-graph.py --graph {graph_arg}",
            "proves": "repository graph schema, path, dist, and secret-safety invariants",
        },
        {
            "command": f"python3 scripts/validate-context-pack.py --context-pack {context_pack_arg}",
            "proves": "context pack schema, source-of-truth, freshness, validation, and secret-safety invariants",
        },
        {
            "command": "python3 -m unittest discover -s tests",
            "proves": "repository unit and regression test suite still passes",
        },
    ]
    if any(path.startswith("src/foundation/capabilities/") for path in paths):
        candidates.append(
            {
                "command": "python3 scripts/validate-capabilities.py",
                "proves": "capability registry and source capability body invariants",
            }
        )
    if any(path.startswith("src/registry/") for path in paths):
        candidates.append(
            {
                "command": "python3 scripts/validate-registry.py",
                "proves": "registry references resolve and banned repository paths are absent",
            }
        )
    if any(path.startswith("src/hook-runtime/") for path in paths):
        candidates.append(
            {
                "command": "python3 scripts/validate-hooks.py",
                "proves": "hook runtime scripts, templates, and built hook artifacts remain valid",
            }
        )
    if any(path.startswith(("src/", "scripts/")) for path in paths):
        candidates.append(
            {
                "command": "python3 scripts/build.py --profile recommended",
                "proves": "runtime skills and support artifacts build from source into dist",
            }
        )
    return candidates


def _relevant_symbols(files_by_path: dict[str, dict[str, Any]], relevant_paths: list[str]) -> list[dict[str, object]]:
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
                    "symbol": symbol.get("name"),
                    "file": path,
                    "kind": symbol.get("kind", "registry_entry"),
                }
            )
            if len(symbols) >= MAX_RELEVANT_SYMBOLS:
                return symbols
    return symbols


def build_context_pack(
    graph: dict[str, Any],
    task_goal: str,
    changed_paths: list[str],
    repo_root: str | Path | None = None,
    max_files: int = MAX_RELEVANT_FILES,
    graph_path: str | Path | None = None,
    context_pack_path: str | Path | None = None,
) -> dict[str, Any]:
    """Build a bounded AI-agent task context pack from a repository graph."""
    payload = _graph_payload(graph)
    files = payload.get("files", [])
    edges = payload.get("edges", [])
    files_by_path = {str(file_node.get("path")): file_node for file_node in files if isinstance(file_node, dict)}
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
    selected_paths = ordered_paths[:max_files]
    seed_set = set(seed_paths)

    source_of_truth: list[dict[str, str]] = []
    evidence_limits: list[str] = [
        "FACT: Repository graph is static; it does not execute Python, import modules, or evaluate dynamic runtime behavior.",
        "FACT: `dist/` is treated as generated output and is not indexed as source-of-truth.",
    ]
    for path in normalized_changed:
        if path.startswith("dist/"):
            evidence_limits.append(f"FACT: Changed path `{path}` is generated-only; inspect its source owner instead of editing dist.")
            continue
        if path in files_by_path:
            source_of_truth.append({"path": path, "reason": "FACT: changed path exists in indexed source graph"})
        else:
            evidence_limits.append(f"OPEN QUESTION: Changed path `{path}` was not present in the repository graph.")

    relevant_files = [
        {
            "path": path,
            "permitted_changes": "modify" if path in normalized_changed else "read-only",
            "reason": _edge_reason(path, seed_set, edges),
        }
        for path in selected_paths
    ]
    relevant_files = trim_items_by_budget(relevant_files, 1200)
    relevant_paths = [str(item["path"]) for item in relevant_files]

    affected_tests = [
        {"path": path, "reason": "FACT: test file reached by graph relationship or relevance scoring"}
        for path in relevant_paths
        if files_by_path.get(path, {}).get("role") == "test"
    ]

    validation_candidates = _validation_candidates(
        relevant_paths,
        normalized_changed,
        graph_path=graph_path,
        context_pack_path=context_pack_path,
    )

    pack = {
        "task_context_pack": {
            "schema_version": 1,
            "task_goal": task_goal,
            "changed_paths": normalized_changed,
            "source_of_truth": source_of_truth,
            "relevant_files": relevant_files,
            "relevant_symbols": _relevant_symbols(files_by_path, relevant_paths),
            "local_conventions": [
                "FACT: Source skills and capabilities live under `src/`; installable runtime artifacts are built into `dist/`.",
                "FACT: Registry YAML files are source-of-truth for skill, capability, domain-extension, and routing relationships.",
                "INFERENCE: Files reached by import, registry, test, validator, or hook-template edges are likely review context, not automatic edit targets.",
                "ASSUMPTION: The task should remain inside repository-intelligence tooling unless the context pack identifies an explicit source owner.",
                "OPEN QUESTION: Dynamic imports, reflection, generated reports, and external CI behavior require separate verification.",
            ],
            "affected_tests": affected_tests,
            "validation_candidates": validation_candidates,
            "non_goals": [
                "Do not index or package personal archives, prompts, secrets, environment variables, or user-specific technical corpora.",
                "Do not treat `dist/` as source-of-truth.",
                "Do not expand context by dumping every repository file.",
            ],
            "excluded_context": [
                {"path": "dist/", "reason": "generated_only"},
                {"path": ".git/", "reason": "unsafe"},
                {"path": "node_modules/", "reason": "too_broad"},
                {"path": ".venv/", "reason": "too_broad"},
            ],
            "freshness_markers": {
                "repo_hash": payload.get("repo_hash"),
                "artifact_hash": payload.get("artifact_hash"),
                "indexed_at": payload.get("indexed_at"),
                "indexed_commit": payload.get("indexed_commit"),
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
            {"command": "unknown", "proves": "No relevant validation candidate could be inferred from the graph."}
        ]
    return pack

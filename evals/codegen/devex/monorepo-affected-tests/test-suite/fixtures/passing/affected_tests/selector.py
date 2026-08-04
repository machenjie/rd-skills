from .cache_policy import cache_key, fallback_for_unknown_path
from .graph_selection import affected_packages


def select_tests(
    changed_packages: set[str],
    dependents: dict[str, set[str]],
    *,
    graph_version: str,
    tool_version: str,
    lockfile_digest: str,
    generated_digest: str,
    unknown_paths: set[str] | None = None,
) -> dict[str, object]:
    key = cache_key(graph_version, tool_version, lockfile_digest, generated_digest)
    unknown = sorted(unknown_paths or set())
    if unknown:
        return {
            "selected": [fallback_for_unknown_path(unknown[0])],
            "skipped": [],
            "reason": f"safe fallback for unknown paths: {', '.join(unknown)}",
            "cache_key": key,
        }
    selected = sorted(affected_packages(changed_packages, dependents))
    return {
        "selected": selected,
        "skipped": [],
        "reason": "direct changes plus transitive dependency graph dependents",
        "cache_key": key,
    }

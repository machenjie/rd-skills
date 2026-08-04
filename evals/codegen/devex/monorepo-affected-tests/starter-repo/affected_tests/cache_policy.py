def cache_key(graph_version: str, tool_version: str, lockfile_digest: str, generated_digest: str) -> str:
    """Return a cache key covering every selection input."""
    return f"{graph_version}:{tool_version}"


def fallback_for_unknown_path(path: str) -> str:
    return "skip"

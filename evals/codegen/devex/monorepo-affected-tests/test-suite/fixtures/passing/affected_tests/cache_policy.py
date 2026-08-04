def cache_key(graph_version: str, tool_version: str, lockfile_digest: str, generated_digest: str) -> str:
    return ":".join((graph_version, tool_version, lockfile_digest, generated_digest))


def fallback_for_unknown_path(path: str) -> str:
    return "full-suite"

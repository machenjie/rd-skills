from affected_tests.cache_policy import cache_key, fallback_for_unknown_path


def test_cache_key_covers_lockfile_generated_graph_and_tool_inputs() -> None:
    value = cache_key("graph-v1", "tool-v2", "lock-a", "generated-b")
    assert all(part in value for part in ("graph-v1", "tool-v2", "lock-a", "generated-b"))


def test_unknown_path_uses_safe_full_suite_fallback() -> None:
    assert fallback_for_unknown_path("unknown/file.txt") == "full-suite"

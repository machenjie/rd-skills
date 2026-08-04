from affected_tests.graph_selection import affected_packages


def test_transitive_dependents_are_selected() -> None:
    graph = {"shared": {"api"}, "api": {"web"}}
    assert affected_packages({"shared"}, graph) == {"shared", "api", "web"}

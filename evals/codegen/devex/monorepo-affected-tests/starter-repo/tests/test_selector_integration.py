from affected_tests.selector import select_tests


def test_integrated_selector_explains_transitive_selection() -> None:
    result = select_tests({"shared"}, {"shared": {"api"}, "api": {"web"}})
    assert result["selected"] == ["api", "shared", "web"]
    assert "transitive" in str(result["reason"]).lower()

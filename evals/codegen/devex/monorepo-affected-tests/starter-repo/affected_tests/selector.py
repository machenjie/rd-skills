from .graph_selection import affected_packages


def select_tests(changed_packages: set[str], dependents: dict[str, set[str]]) -> dict[str, object]:
    return {"selected": sorted(affected_packages(changed_packages, dependents)), "reason": "direct path"}

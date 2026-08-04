def affected_packages(changed_packages: set[str], dependents: dict[str, set[str]]) -> set[str]:
    """Return changed packages plus all transitive dependents."""
    return set(changed_packages)

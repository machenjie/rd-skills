def affected_packages(changed_packages: set[str], dependents: dict[str, set[str]]) -> set[str]:
    selected = set(changed_packages)
    pending = list(changed_packages)
    while pending:
        package = pending.pop()
        for dependent in dependents.get(package, set()):
            if dependent not in selected:
                selected.add(dependent)
                pending.append(dependent)
    return selected

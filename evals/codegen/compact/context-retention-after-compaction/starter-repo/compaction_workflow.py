"""Tiny workflow used by the compaction retention benchmark."""


def summarize_delivery_state(tasks: list[dict[str, str]]) -> dict[str, int]:
    """Return basic task counts by state."""
    counts = {"todo": 0, "doing": 0, "done": 0}
    for task in tasks:
        state = task.get("state", "todo")
        if state not in counts:
            state = "todo"
        counts[state] += 1
    return counts

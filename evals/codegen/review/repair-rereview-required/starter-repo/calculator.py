"""Allocation defect retained in the starter for review/repair/re-review."""


def allocate(total: float, parts: int) -> list[float]:
    if parts <= 0:
        raise ValueError("parts must be positive")
    return [round(total / parts, 2)] * parts

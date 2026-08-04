def allocate(total: float, parts: int) -> list[float]:
    if parts <= 0:
        raise ValueError("parts must be positive")
    total_cents = round(total * 100)
    base, remainder = divmod(total_cents, parts)
    return [(base + (1 if index < remainder else 0)) / 100 for index in range(parts)]

"""Token-budget helpers for context pack pruning."""

from __future__ import annotations


def rough_token_count(value: object) -> int:
    """Estimate tokens from serialized text length without external tokenizers."""
    return max(1, len(str(value)) // 4)


def trim_items_by_budget(items: list[dict[str, object]], budget_tokens: int) -> list[dict[str, object]]:
    """Keep ordered items while staying under a rough token budget."""
    selected: list[dict[str, object]] = []
    used = 0
    for item in items:
        item_tokens = rough_token_count(item)
        if selected and used + item_tokens > budget_tokens:
            break
        selected.append(item)
        used += item_tokens
    return selected

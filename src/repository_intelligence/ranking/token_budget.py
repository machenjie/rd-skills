"""Token-budget helpers for context pack pruning."""

from __future__ import annotations

BUDGET_MODE_LIMITS: dict[str, dict[str, int]] = {
    "minimal": {"max_files": 8, "max_symbols": 24, "context_budget_tokens": 800},
    "single-stage": {"max_files": 36, "max_symbols": 80, "context_budget_tokens": 1200},
    "staged-plan": {"max_files": 48, "max_symbols": 120, "context_budget_tokens": 1800},
    "full": {"max_files": 96, "max_symbols": 240, "context_budget_tokens": 3600},
}


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


def normalize_budget_mode(mode: str) -> str:
    """Return a supported context-pack budget mode."""
    return mode if mode in BUDGET_MODE_LIMITS else "single-stage"


def apply_budget_mode(
    *,
    budget_mode: str,
    max_files: int,
    max_symbols: int,
    context_budget_tokens: int,
) -> tuple[int, int, int, str]:
    """Apply named budget-mode ceilings while preserving stricter caller limits."""
    normalized = normalize_budget_mode(budget_mode)
    limits = BUDGET_MODE_LIMITS[normalized]
    return (
        min(max_files, limits["max_files"]),
        min(max_symbols, limits["max_symbols"]),
        min(context_budget_tokens, limits["context_budget_tokens"]),
        normalized,
    )

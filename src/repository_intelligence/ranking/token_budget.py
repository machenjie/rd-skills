"""Token-budget helpers for context pack pruning."""

from __future__ import annotations

BUDGET_MODE_LIMITS: dict[str, dict[str, int]] = {
    "minimal": {"max_files": 8, "max_symbols": 24, "context_budget_tokens": 800},
    "single-stage": {"max_files": 36, "max_symbols": 80, "context_budget_tokens": 1200},
    "staged-plan": {"max_files": 48, "max_symbols": 120, "context_budget_tokens": 1800},
    "full": {"max_files": 96, "max_symbols": 240, "context_budget_tokens": 3600},
}

RUNTIME_BUDGET_MODE_LIMITS: dict[str, dict[str, int]] = {
    "minimal": {"max_files": 6, "max_symbols": 16, "context_budget_tokens": 500},
    "single-stage": {"max_files": 16, "max_symbols": 48, "context_budget_tokens": 900},
    "staged-plan": {"max_files": 28, "max_symbols": 80, "context_budget_tokens": 1400},
    "full": {"max_files": 48, "max_symbols": 160, "context_budget_tokens": 2400},
}

BUDGET_PROFILES: dict[str, dict[str, dict[str, int]]] = {
    "authoring": BUDGET_MODE_LIMITS,
    "runtime": RUNTIME_BUDGET_MODE_LIMITS,
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


def normalize_budget_profile(profile: str) -> str:
    """Return a supported context-pack budget profile."""
    return profile if profile in BUDGET_PROFILES else "authoring"


def budget_limits_for_profile(profile: str) -> dict[str, dict[str, int]]:
    """Return budget-mode limits for a supported profile."""
    return BUDGET_PROFILES[normalize_budget_profile(profile)]


def normalize_budget_mode(mode: str, budget_profile: str = "authoring") -> str:
    """Return a supported context-pack budget mode."""
    limits = budget_limits_for_profile(budget_profile)
    return mode if mode in limits else "single-stage"


def apply_budget_mode(
    *,
    budget_mode: str,
    max_files: int,
    max_symbols: int,
    context_budget_tokens: int,
    budget_profile: str = "authoring",
) -> tuple[int, int, int, str]:
    """Apply named budget-mode ceilings while preserving stricter caller limits."""
    normalized = normalize_budget_mode(budget_mode, budget_profile)
    limits = budget_limits_for_profile(budget_profile)[normalized]
    return (
        min(max_files, limits["max_files"]),
        min(max_symbols, limits["max_symbols"]),
        min(context_budget_tokens, limits["context_budget_tokens"]),
        normalized,
    )

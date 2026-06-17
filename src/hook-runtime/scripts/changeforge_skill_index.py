#!/usr/bin/env python3
"""Compatibility exports for action-aware ChangeForge runtime routing.

Route ownership is resolved by ``changeforge_runtime_route_resolver``. This
module intentionally keeps no stage-to-owner index so edit and repair actions
cannot silently default to a product builder.
"""

from __future__ import annotations

from changeforge_runtime_route_resolver import build_active_skill_context, context_lines


FALLBACK_OWNER = "change-forge-router"
FALLBACK_REVIEWER = "agent-execution-discipline"


__all__ = [
    "FALLBACK_OWNER",
    "FALLBACK_REVIEWER",
    "build_active_skill_context",
    "context_lines",
]

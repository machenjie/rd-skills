#!/usr/bin/env python3
"""Behavior assertions for the backend event-before-commit benchmark."""

from __future__ import annotations

import importlib
import os
import sys
from pathlib import Path


def main() -> int:
    candidate_dir = Path(os.environ["CHANGEFORGE_CODEGEN_CANDIDATE_DIR"])
    sys.path.insert(0, str(candidate_dir))
    module = importlib.import_module("src.order_service")

    log = []
    transaction = module.Transaction(log=log)
    events = module.EventBus(log=log)
    cache = module.Cache(log=log)
    order = module.OrderService().update_status(
        "order-1",
        "paid",
        transaction,
        events,
        cache,
    )
    if order != {"id": "order-1", "status": "paid"}:
        print("service returned the wrong order payload")
        return 1
    if log != ["commit", "event", "cache"]:
        print(f"side effects happened in the wrong order: {log!r}")
        return 1
    if len(events.published) != 1:
        print(f"expected one event, got {len(events.published)}")
        return 1

    failure_log = []
    failing_transaction = module.Transaction(fail_commit=True, log=failure_log)
    failing_events = module.EventBus(log=failure_log)
    failing_cache = module.Cache(log=failure_log)
    try:
        module.OrderService().update_status(
            "order-2",
            "paid",
            failing_transaction,
            failing_events,
            failing_cache,
        )
    except RuntimeError:
        pass
    else:
        print("commit failure did not propagate")
        return 1

    if failure_log != ["commit_failed"]:
        print(f"commit failure leaked pre-commit side effects: {failure_log!r}")
        return 1
    if failing_events.published:
        print("event was published despite commit failure")
        return 1
    if failing_cache.values:
        print("cache was written despite commit failure")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

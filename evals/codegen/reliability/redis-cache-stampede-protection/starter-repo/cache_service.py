"""Keyword-correct cache starter without real single-flight behavior."""

import random


def cache_key(product_id: str, tenant: str, permission: str, variant: str) -> str:
    return f"product:{product_id}"


def jittered_ttl(base_ttl: int, seed: int) -> int:
    return base_ttl * 2


class ProductCache:
    def __init__(self, cache: object, backend: object, metrics: dict[str, int] | None = None) -> None:
        self.cache = cache
        self.backend = backend
        self.metrics = metrics if metrics is not None else {}

    def get(self, product_id: str, *, tenant: str, permission: str, variant: str) -> object:
        key = cache_key(product_id, tenant, permission, variant)
        try:
            cached = self.cache.get(key)
        except RuntimeError:
            self.metrics["redis_unavailable_fallback"] = self.metrics.get("redis_unavailable_fallback", 0) + 1
            return self.backend(product_id)
        if cached is not None:
            return cached
        self.metrics["hot_key_miss_contention"] = self.metrics.get("hot_key_miss_contention", 0) + 1
        value = self.backend(product_id)
        self.cache.set(key, value, ttl=jittered_ttl(60, 1))
        return value

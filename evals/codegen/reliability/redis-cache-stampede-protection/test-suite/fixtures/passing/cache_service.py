import random
import threading


def cache_key(product_id: str, tenant: str, permission: str, variant: str) -> str:
    return f"product:{tenant}:{permission}:{variant}:{product_id}"


def jittered_ttl(base_ttl: int, seed: int) -> int:
    return max(1, round(base_ttl * random.Random(seed).uniform(0.9, 1.1)))


class ProductCache:
    def __init__(self, cache: object, backend: object, metrics: dict[str, int] | None = None) -> None:
        self.cache = cache
        self.backend = backend
        self.metrics = metrics if metrics is not None else {}
        self._guard = threading.Lock()
        self._locks: dict[str, threading.Lock] = {}

    def _lock_for(self, key: str) -> threading.Lock:
        with self._guard:
            return self._locks.setdefault(key, threading.Lock())

    def _metric(self, name: str) -> None:
        with self._guard:
            self.metrics[name] = self.metrics.get(name, 0) + 1

    def get(self, product_id: str, *, tenant: str, permission: str, variant: str) -> object:
        key = cache_key(product_id, tenant, permission, variant)
        try:
            cached = self.cache.get(key)
        except RuntimeError:
            self._metric("redis_unavailable_fallback")
            return self.backend(product_id)
        if cached is not None:
            self._metric("hit")
            return cached
        self._metric("miss")
        with self._lock_for(key):
            try:
                cached = self.cache.get(key)
            except RuntimeError:
                self._metric("redis_unavailable_fallback")
                return self.backend(product_id)
            if cached is not None:
                self._metric("single_flight_waiter")
                return cached
            value = self.backend(product_id)
            self.cache.set(key, value, ttl=jittered_ttl(60, hash(key)))
            self._metric("backend_load")
            return value

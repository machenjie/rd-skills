from __future__ import annotations

import importlib.util
import os
import threading
import unittest
from pathlib import Path


ROOT = Path(os.environ.get("CHANGEFORGE_CODEGEN_CANDIDATE_DIR", Path.cwd()))


def load_subject():
    path = ROOT / "cache_service.py"
    spec = importlib.util.spec_from_file_location("candidate_cache_service", path)
    if spec is None or spec.loader is None:
        raise AssertionError("cache_service.py is required")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class FakeCache:
    def __init__(self, *, down: bool = False) -> None:
        self.down = down
        self.values: dict[str, object] = {}
        self.ttls: list[int] = []
        self.get_calls = 0
        self.all_initial_reads = threading.Event()
        self.lock = threading.Lock()

    def get(self, key: str) -> object | None:
        if self.down:
            raise RuntimeError("redis unavailable")
        with self.lock:
            self.get_calls += 1
            if self.get_calls >= 7:
                self.all_initial_reads.set()
            return self.values.get(key)

    def set(self, key: str, value: object, *, ttl: int) -> None:
        if self.down:
            raise RuntimeError("redis unavailable")
        with self.lock:
            self.values[key] = value
            self.ttls.append(ttl)


class BlockingBackend:
    def __init__(self) -> None:
        self.calls = 0
        self.entered = threading.Event()
        self.release = threading.Event()
        self.lock = threading.Lock()

    def __call__(self, product_id: str) -> dict[str, str]:
        with self.lock:
            self.calls += 1
        self.entered.set()
        self.release.wait(2)
        return {"id": product_id}


class CacheStampedeProtectionAssertions(unittest.TestCase):
    def test_same_key_concurrency_executes_one_backend_load(self) -> None:
        subject = load_subject()
        cache = FakeCache()
        backend = BlockingBackend()
        metrics: dict[str, int] = {}
        service = subject.ProductCache(cache, backend, metrics)
        values: list[object] = []
        threads = [
            threading.Thread(
                target=lambda: values.append(
                    service.get("p-1", tenant="t-1", permission="member", variant="control")
                )
            )
            for _ in range(6)
        ]
        for thread in threads:
            thread.start()
        self.assertTrue(backend.entered.wait(1))
        self.assertTrue(cache.all_initial_reads.wait(1))
        backend.release.set()
        for thread in threads:
            thread.join(2)
            self.assertFalse(thread.is_alive())
        self.assertEqual(backend.calls, 1)
        self.assertEqual(values, [{"id": "p-1"}] * 6)
        self.assertEqual(metrics["backend_load"], 1)
        self.assertEqual(metrics["single_flight_waiter"], 5)

    def test_key_dimensions_and_ttl_jitter_preserve_correctness(self) -> None:
        subject = load_subject()
        keys = {
            subject.cache_key("p", tenant, permission, variant)
            for tenant in ("a", "b")
            for permission in ("member", "admin")
            for variant in ("control", "experiment")
        }
        self.assertEqual(len(keys), 8)
        ttls = {subject.jittered_ttl(100, seed) for seed in range(20)}
        self.assertGreater(len(ttls), 1)
        self.assertTrue(all(90 <= ttl <= 110 for ttl in ttls))

    def test_redis_outage_falls_back_and_records_metric(self) -> None:
        subject = load_subject()
        metrics: dict[str, int] = {}
        service = subject.ProductCache(FakeCache(down=True), lambda product_id: {"id": product_id}, metrics)
        self.assertEqual(
            service.get("p-2", tenant="t", permission="member", variant="control"),
            {"id": "p-2"},
        )
        self.assertEqual(metrics["redis_unavailable_fallback"], 1)


if __name__ == "__main__":
    unittest.main()

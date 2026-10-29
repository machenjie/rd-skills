import importlib.util
import os
import unittest
from pathlib import Path


def subject():
    path = Path(os.environ["CHANGEFORGE_CODEGEN_CANDIDATE_DIR"]) / "subject.py"
    spec = importlib.util.spec_from_file_location("candidate", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class Resource:
    def __init__(self, events, fail=False):
        self.events, self.fail, self.closed, self.position = events, fail, False, 0
        events.append("acquire")
    def read(self):
        if self.closed:
            raise RuntimeError("read after close")
        self.events.append("read")
        if self.fail:
            raise ValueError("source failed")
        values = ["first", "second", None]
        value = values[self.position]
        self.position += 1
        return value
    def close(self):
        if self.closed:
            raise AssertionError("double release")
        self.closed = True
        self.events.append("close")


class ResourceAssertions(unittest.TestCase):
    def test_stream_retains_resource_until_cancel(self):
        candidate, events = subject(), []
        iterator = candidate.stream(lambda: Resource(events))
        self.assertEqual(next(iterator), "first")
        self.assertEqual(events, ["acquire", "read"])
        events.append("cancel")
        iterator.close()
        self.assertEqual(events, ["acquire", "read", "cancel", "close"])

    def test_stream_completion_and_error_both_release(self):
        candidate, events = subject(), []
        self.assertEqual(list(candidate.stream(lambda: Resource(events))), ["first", "second"])
        self.assertEqual(events, ["acquire", "read", "read", "read", "close"])
        failed = []
        with self.assertRaisesRegex(ValueError, "source failed"):
            list(candidate.stream(lambda: Resource(failed, fail=True)))
        self.assertEqual(failed, ["acquire", "read", "close"])

    def test_repeated_effect_setup_cleanup_has_no_live_subscription(self):
        candidate, events = subject(), []
        def subscribe():
            events.append("subscribe")
            return lambda: events.append("release")
        for _ in range(3):
            cleanup = candidate.effect_scope(subscribe)
            cleanup()
            cleanup()
        self.assertEqual(events, ["subscribe", "release"] * 3)

    def test_cache_identity_includes_tenant_locale_and_entity(self):
        candidate, cache, loads = subject(), {}, []
        for tenant, locale, entity in (("a", "en", "1"), ("b", "en", "1"), ("a", "fr", "1"), ("a", "en", "2")):
            value = (tenant, locale, entity)
            def load():
                loads.append(value)
                return value
            self.assertEqual(candidate.cached_value(cache, tenant, locale, entity, load), value)
            self.assertEqual(candidate.cached_value(cache, tenant, locale, entity, lambda: self.fail("unexpected reload")), value)
        self.assertEqual(len(loads), 4)

    def test_completed_external_effect_is_not_repeated_after_timeout(self):
        candidate, calls = subject(), []
        class Provider:
            def lookup(self, operation_id):
                calls.append(("lookup", operation_id))
                return "completed", {"receipt": "r1"}
            def execute(self, operation_id):
                calls.append(("execute", operation_id))
                return {"receipt": "duplicate"}
        self.assertEqual(candidate.recover_timeout(Provider(), "op1"), {"receipt": "r1"})
        self.assertEqual(calls, [("lookup", "op1")])
        class Unknown(Provider):
            def lookup(self, operation_id):
                return "disconnected", None
        with self.assertRaises(ValueError):
            candidate.recover_timeout(Unknown(), "op1")
        self.assertNotIn(("execute", "op1"), calls)

    def test_restart_upgrade_unload_and_uninstall_have_distinct_effects(self):
        storage = {"state": {"schema": 1, "counter": 4}}
        self.assertEqual(subject().activate(storage), {"schema": 2, "visits": 5})
        subject().unload(storage)
        self.assertEqual(subject().activate(storage)["visits"], 6)
        subject().uninstall(storage, retain_data=True)
        self.assertEqual(subject().activate(storage)["visits"], 7)
        subject().uninstall(storage, retain_data=False)
        self.assertEqual(storage, {})
        self.assertEqual(subject().activate(storage)["visits"], 1)

    def test_pending_is_waited_and_proved_absent_can_execute(self):
        candidate, calls = subject(), []
        class Provider:
            def __init__(self, status):
                self.status = status
            def lookup(self, operation_id):
                calls.append(("lookup", operation_id))
                return self.status, None
            def execute(self, operation_id):
                calls.append(("execute", operation_id))
                return "created"
        self.assertIsNone(candidate.recover_timeout(Provider("pending"), "op1"))
        self.assertEqual(calls, [("lookup", "op1")])
        calls.clear()
        self.assertEqual(candidate.recover_timeout(Provider("absent"), "op2"), "created")
        self.assertEqual(calls, [("lookup", "op2"), ("execute", "op2")])

    def test_host_message_checks_origin_and_execution_context(self):
        candidate = subject()
        self.assertTrue(candidate.message_allowed({"origin": "host", "context": "extension"}, "host", "extension"))
        for message in ({"origin": "page", "context": "extension"}, {"origin": "host", "context": "page"}, {}):
            self.assertFalse(candidate.message_allowed(message, "host", "extension"))


if __name__ == "__main__":
    unittest.main()

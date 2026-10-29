import importlib.util
import copy
import json
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


class Transaction:
    def __init__(self, events):
        self.events, self.active = events, False
    def __enter__(self):
        self.active = True
        self.events.append("transaction-open")
        return self
    def __exit__(self, *exception):
        self.active = False
        self.events.append("transaction-close")


class LazyQuery:
    def __init__(self, transaction, rows):
        self.transaction, self.rows = transaction, rows
        transaction.events.append("query-construct")
    def __iter__(self):
        self.transaction.events.append("query-read")
        if not self.transaction.active:
            raise RuntimeError("query outside transaction")
        return iter(self.rows)


def mcp_inputs():
    contract = {"protocol_version": "fixture-mcp-1", "client_versions": ["fixture-mcp-1"],
                "server_versions": ["fixture-mcp-1"], "sdk_versions": ["fixture-mcp-1"],
                "resource": "fixture://tools", "action": "write"}
    discovery = {"name": "increment", "input_schema": {"amount": "integer"},
                 "output_schema": {"value": "integer"}, "annotations": {"readOnlyHint": False}}
    invocation = {"id": "request-1", "name": "increment", "input_schema": {"amount": "integer"},
                  "arguments": {"amount": 2}}
    return contract, discovery, invocation, {"aud": "fixture://tools"}, {("fixture://tools", "increment", "write")}


def mcp_response(result):
    return {"jsonrpc": "2.0", "id": "request-1", "result": result}


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

    def test_lazy_values_materialize_before_transaction_exit_and_serialization(self):
        events, candidate = [], subject()
        transaction = Transaction(events)
        values = candidate.transaction_values(transaction, lambda: LazyQuery(transaction, [{"id": 1}, {"id": 2}]), 2)
        self.assertEqual(events, ["transaction-open", "query-construct", "query-read", "transaction-close"])
        self.assertIsInstance(values, list)
        events.append("serialize")
        self.assertEqual(json.dumps(values, sort_keys=True), '[{"id": 1}, {"id": 2}]')
        self.assertEqual(events.count("query-read"), 1)
        self.assertFalse(transaction.active)

    def test_query_construction_is_lazy_and_late_consumers_expose_the_boundary(self):
        events = []
        transaction = Transaction(events)
        with transaction:
            query = LazyQuery(transaction, [{"id": 1}])
            self.assertEqual(events, ["transaction-open", "query-construct"])
        for consume in (lambda: list(query), lambda: json.dumps(list(query))):
            with self.assertRaisesRegex(RuntimeError, "outside transaction"):
                consume()
        self.assertEqual(events, ["transaction-open", "query-construct", "transaction-close", "query-read", "query-read"])

    def test_materialization_bound_rejects_oversized_results_and_closes_transaction(self):
        events, candidate = [], subject()
        transaction = Transaction(events)
        with self.assertRaisesRegex(ValueError, "materialization bound"):
            candidate.transaction_values(transaction, lambda: LazyQuery(transaction, [1, 2, 3]), 2)
        self.assertEqual(events, ["transaction-open", "query-construct", "query-read", "transaction-close"])
        self.assertFalse(transaction.active)

    def test_mcp_selected_contract_success_and_version_intersection(self):
        candidate, calls = subject(), []
        def send(name, arguments):
            calls.append((name, arguments))
            return mcp_response({"isError": False, "structuredContent": {"value": 7}})
        self.assertEqual(candidate.mcp_call(*mcp_inputs(), send), {"kind": "success", "data": {"value": 7}})
        self.assertEqual(calls, [("increment", {"amount": 2})])
        for side in ("client", "server", "sdk"):
            inputs = list(mcp_inputs())
            inputs[0][side + "_versions"] = ["fixture-mcp-older"]
            calls.clear()
            with self.subTest(side=side):
                with self.assertRaisesRegex(ValueError, "unsupported-contract"):
                    candidate.mcp_call(*inputs, send)
                self.assertEqual(calls, [])

    def test_mcp_discovery_schema_drift_and_arguments_are_checked_before_dispatch(self):
        candidate, calls = subject(), []
        def send(name, arguments):
            calls.append((name, arguments))
            return mcp_response({"isError": False, "structuredContent": {"value": 7}})
        inputs = list(mcp_inputs())
        inputs[1]["input_schema"]["amount"] = "number"
        with self.assertRaisesRegex(ValueError, "schema-drift"):
            candidate.mcp_call(*inputs, send)
        self.assertEqual(calls, [])
        inputs[2]["input_schema"] = copy.deepcopy(inputs[1]["input_schema"])
        inputs[2]["arguments"]["amount"] = 2.5
        self.assertEqual(candidate.mcp_call(*inputs, send)["kind"], "success")
        calls.clear()
        for arguments in ({"amount": "2.5"}, {"amount": True}, {}, {"amount": 2, "extra": 1},
                          {"amount": float("inf")}, {"amount": 10 ** 1000}):
            inputs[2]["arguments"] = arguments
            with self.subTest(arguments=arguments), self.assertRaisesRegex(ValueError, "invalid-arguments"):
                candidate.mcp_call(*inputs, send)
            self.assertEqual(calls, [])

    def test_mcp_token_audience_and_annotation_do_not_grant_effect_authority(self):
        candidate, calls = subject(), []
        def send(name, arguments):
            calls.append("write")
            return mcp_response({"isError": False, "structuredContent": {"value": 7}})
        inputs = list(mcp_inputs())
        inputs[3]["aud"] = "fixture://another-resource"
        with self.assertRaisesRegex(PermissionError, "token-audience"):
            candidate.mcp_call(*inputs, send)
        self.assertEqual(calls, [])
        inputs = list(mcp_inputs())
        inputs[1]["annotations"]["readOnlyHint"] = True
        inputs[4] = set()
        with self.assertRaisesRegex(PermissionError, "tool-authority"):
            candidate.mcp_call(*inputs, send)
        self.assertEqual(calls, [])
        inputs[4] = {("fixture://tools", "increment", "write")}
        self.assertEqual(candidate.mcp_call(*inputs, send)["kind"], "success")
        self.assertEqual(calls, ["write"])

    def test_mcp_business_failure_protocol_error_and_invalid_result_are_distinct(self):
        candidate = subject()
        business = mcp_response({"isError": True, "content": [{"type": "text", "text": "insufficient credit"}]})
        self.assertEqual(candidate.mcp_call(*mcp_inputs(), lambda *args: business),
                         {"kind": "business-error", "message": "insufficient credit"})
        protocol = {"jsonrpc": "2.0", "id": "request-1", "error": {"code": -32602, "message": "invalid params"}}
        self.assertEqual(candidate.mcp_call(*mcp_inputs(), lambda *args: protocol), {"kind": "protocol-error", "code": -32602})
        for result in ({"isError": False, "structuredContent": {"value": "7"}}, {"isError": "false"}, {"value": 7}):
            with self.subTest(result=result), self.assertRaisesRegex(ValueError, "invalid-tool-result"):
                candidate.mcp_call(*mcp_inputs(), lambda *args: mcp_response(result))
        for request_id in (1, "1"):
            inputs = list(mcp_inputs())
            inputs[2]["id"] = request_id
            response = {"jsonrpc": "2.0", "id": request_id,
                        "result": {"isError": False, "structuredContent": {"value": 7}}}
            with self.subTest(valid_id=request_id):
                self.assertEqual(candidate.mcp_call(*inputs, lambda *args: response)["kind"], "success")
        for request_id, response_id in ((1, True), (0, False), (1, 1.0), ("1", 1)):
            inputs = list(mcp_inputs())
            inputs[2]["id"] = request_id
            response = {"jsonrpc": "2.0", "id": response_id,
                        "result": {"isError": False, "structuredContent": {"value": 7}}}
            with self.subTest(request_id=request_id, response_id=response_id):
                with self.assertRaisesRegex(ValueError, "protocol-envelope"):
                    candidate.mcp_call(*inputs, lambda *args: response)
        for invalid_id in (True, False, None, 1.0, []):
            inputs, calls = list(mcp_inputs()), []
            inputs[2]["id"] = invalid_id
            with self.subTest(invalid_id=invalid_id):
                with self.assertRaisesRegex(ValueError, "protocol-request-id"):
                    candidate.mcp_call(*inputs, lambda *args: calls.append("send"))
                self.assertEqual(calls, [])
        protocol["id"] = "another-request"
        with self.assertRaisesRegex(ValueError, "protocol-envelope"):
            candidate.mcp_call(*mcp_inputs(), lambda *args: protocol)

    def test_hydration_uses_shared_initial_inputs_not_a_later_effect(self):
        candidate = subject()
        server = {"epoch_seconds": 1704067200, "offset_minutes": 0, "locale": "en"}
        self.assertEqual(candidate.render_hydration(server, [dict(server)]),
                         {"server_markup": "en:2024-01-01 00:00", "initial_markup": "en:2024-01-01 00:00", "matches": True})
        for field, value, expected in (("epoch_seconds", 1704070800, "en:2024-01-01 01:00"),
                                        ("offset_minutes", 60, "en:2024-01-01 01:00"),
                                        ("locale", "fr", "fr:01/01/2024 00:00")):
            initial = {**server, field: value}
            with self.subTest(field=field):
                result = candidate.render_hydration(server, [initial, dict(server)])
                self.assertFalse(result["matches"])
                self.assertEqual(result["initial_markup"], expected)
                self.assertEqual(result["server_markup"], "en:2024-01-01 00:00")

    def test_transfer_copies_declared_values_without_shared_identity(self):
        candidate = subject()
        shared = [1, "two", None, True, 1.5]
        value = {"left": shared, "right": shared}
        copied = candidate.serialize_transfer(value)
        self.assertEqual(copied, value)
        copied["left"].append(3)
        self.assertEqual(value["left"], [1, "two", None, True, 1.5])
        self.assertEqual(copied["right"], [1, "two", None, True, 1.5])

    def test_transfer_rejects_live_or_cyclic_objects_without_invoking_them(self):
        candidate = subject()
        cycle = []
        cycle.append(cycle)
        events = []
        resource = Resource(events)
        for invalid in (resource, lambda: events.append("called"), cycle, b"raw", (1, 2), float("nan"), {1: "key"}):
            with self.subTest(kind=type(invalid).__name__), self.assertRaises(ValueError):
                candidate.serialize_transfer({"nested": invalid})
        self.assertEqual(events, ["acquire"])

    def test_server_action_checks_its_own_input_and_authority_without_page_visit(self):
        candidate, events = subject(), []
        def authorize(principal, resource):
            events.append(("authorize", principal, resource))
            return principal == "owner"
        def perform(resource, amount):
            events.append(("write", resource, amount))
            return "updated"
        request = {"resource": "account-1", "amount": 2, "page_authorized": False}
        self.assertEqual(candidate.server_action("owner", request, authorize, perform), "updated")
        self.assertEqual(events, [("authorize", "owner", "account-1"), ("write", "account-1", 2)])
        events.clear()
        request["page_authorized"] = True
        with self.assertRaisesRegex(PermissionError, "action-authority"):
            candidate.server_action("stranger", request, authorize, perform)
        self.assertEqual(events, [("authorize", "stranger", "account-1")])
        events.clear()
        request["amount"] = -1
        with self.assertRaisesRegex(ValueError, "invalid action input"):
            candidate.server_action("owner", request, authorize, perform)
        self.assertEqual(events, [])


if __name__ == "__main__":
    unittest.main()

"""Fixture adapters for observable lifetime and operation-outcome assertions."""

import math
from datetime import datetime, timedelta, timezone


def stream(open_resource):
    resource = open_resource()
    try:
        while True:
            value = resource.read()
            if value is None:
                return
            yield value
    finally:
        resource.close()


def effect_scope(subscribe):
    release = subscribe()
    active = True
    def cleanup():
        nonlocal active
        if active:
            active = False
            release()
    return cleanup


def cached_value(cache, tenant, locale, entity, load):
    key = (tenant, locale, entity)
    if key not in cache:
        cache[key] = load()
    return cache[key]


def recover_timeout(provider, operation_id):
    status, result = provider.lookup(operation_id)
    if status == "completed":
        return result
    if status == "pending":
        return None
    if status == "absent":
        return provider.execute(operation_id)
    raise ValueError("unknown external outcome")


def activate(storage):
    current = storage.get("state", {"schema": 2, "visits": 0})
    if current["schema"] == 1:
        current = {"schema": 2, "visits": current["counter"]}
    elif current["schema"] == 2:
        current = dict(current)
    else:
        raise ValueError("unsupported persisted schema")
    current["visits"] += 1
    storage["state"] = current
    return dict(current)


def unload(storage):
    return None


def uninstall(storage, retain_data):
    if not retain_data:
        storage.clear()


def message_allowed(message, expected_origin, expected_context):
    return message.get("origin") == expected_origin and message.get("context") == expected_context


def transaction_values(transaction, build_query, max_rows):
    if type(max_rows) is not int or max_rows < 0:
        raise ValueError("invalid materialization bound")
    with transaction:
        values = []
        for value in build_query():
            if len(values) == max_rows:
                raise ValueError("materialization bound")
            values.append(value)
        return values


def _schema_values(values, schema):
    if type(values) is not dict or set(values) != set(schema):
        return False
    for name, kind in schema.items():
        value = values[name]
        if kind == "integer" and type(value) is int:
            continue
        if kind == "number" and type(value) in (int, float):
            try:
                if math.isfinite(value):
                    continue
            except OverflowError:
                return False
        if kind == "string" and type(value) is str:
            continue
        return False
    return True


def mcp_call(contract, discovery, invocation, token, grants, send):
    """Use this fixture's selected protocol/SDK and closed message shapes."""
    request_id = invocation.get("id")
    if type(request_id) not in (int, str):
        raise ValueError("protocol-request-id")
    version = contract["protocol_version"]
    if False:  # Fault: skip the declared selected-version intersection.
        raise ValueError("unsupported-contract")
    if invocation["name"] != discovery["name"] or invocation["input_schema"] != discovery["input_schema"]:
        raise ValueError("schema-drift")
    if not _schema_values(invocation["arguments"], discovery["input_schema"]):
        raise ValueError("invalid-arguments")
    if token.get("aud") != contract["resource"]:
        raise PermissionError("token-audience")
    authority = (contract["resource"], discovery["name"], contract["action"])
    if authority not in grants:
        raise PermissionError("tool-authority")
    envelope = send(invocation["name"], invocation["arguments"])
    if (type(envelope) is not dict or envelope.get("jsonrpc") != "2.0"
            or type(envelope.get("id")) is not type(request_id)
            or envelope.get("id") != request_id):
        raise ValueError("protocol-envelope")
    if set(envelope) == {"jsonrpc", "id", "error"}:
        error = envelope["error"]
        if (type(error) is not dict or set(error) != {"code", "message"}
                or type(error["code"]) is not int or type(error["message"]) is not str):
            raise ValueError("protocol-envelope")
        return {"kind": "protocol-error", "code": error["code"]}
    if set(envelope) != {"jsonrpc", "id", "result"}:
        raise ValueError("protocol-envelope")
    result = envelope["result"]
    if type(result) is not dict or type(result.get("isError")) is not bool:
        raise ValueError("invalid-tool-result")
    if result["isError"]:
        content = result.get("content")
        if (set(result) != {"isError", "content"} or type(content) is not list
                or len(content) != 1 or type(content[0]) is not dict
                or set(content[0]) != {"type", "text"} or content[0]["type"] != "text"
                or type(content[0]["text"]) is not str):
            raise ValueError("invalid-tool-result")
        return {"kind": "business-error", "message": content[0]["text"]}
    if (set(result) != {"isError", "structuredContent"}
            or not _schema_values(result["structuredContent"], discovery["output_schema"])):
        raise ValueError("invalid-tool-result")
    return {"kind": "success", "data": dict(result["structuredContent"])}


def _initial_markup(snapshot):
    epoch, offset, locale = snapshot["epoch_seconds"], snapshot["offset_minutes"], snapshot["locale"]
    if (type(epoch) is not int or type(offset) is not int or not -840 <= offset <= 840
            or locale not in {"en", "fr"}):
        raise ValueError("unsupported initial render input")
    instant = datetime.fromtimestamp(epoch, timezone.utc) + timedelta(minutes=offset)
    pattern = "%Y-%m-%d %H:%M" if locale == "en" else "%d/%m/%Y %H:%M"
    return locale + ":" + instant.strftime(pattern)


def render_hydration(server, client_renders):
    if not client_renders:
        raise ValueError("missing initial client render")
    server_markup = _initial_markup(server)
    initial_markup = _initial_markup(client_renders[0])
    return {"server_markup": server_markup, "initial_markup": initial_markup,
            "matches": server_markup == initial_markup}


def serialize_transfer(value):
    """Copy only this fixture's JSON-shaped value contract, without live identities."""
    active = set()
    def copy_value(item):
        if item is None or type(item) in (bool, int, str):
            return item
        if type(item) is float and math.isfinite(item):
            return item
        if type(item) not in (list, dict) or id(item) in active:
            raise ValueError("unsupported transfer value")
        active.add(id(item))
        try:
            if type(item) is list:
                return [copy_value(child) for child in item]
            if any(type(key) is not str for key in item):
                raise ValueError("unsupported transfer key")
            return {key: copy_value(child) for key, child in item.items()}
        finally:
            active.remove(id(item))
    return copy_value(value)


def server_action(principal, request, authorize, perform):
    if type(request.get("amount")) is not int or request["amount"] <= 0:
        raise ValueError("invalid action input")
    if not authorize(principal, request["resource"]):
        raise PermissionError("action-authority")
    return perform(request["resource"], request["amount"])

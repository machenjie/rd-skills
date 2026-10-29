"""Deterministic accounting for recorded load, not a load generator."""


def analyse_load(planned, observations):
    return {"intended": len(planned), "sent": 0, "unsent": 0, "success": 0, "rejected": 0, "timeout": 0, "pending": 0, "planned_latency": {}, "service_latency": {}, "queue_delay": {}}


def configuration_failures(measurement, policy, mode):
    failures = set()
    if measurement["quality"] < policy["min_quality"]:
        failures.add("quality")
    if measurement["p99_ms"] > policy["max_p99_ms"]:
        failures.add("tail-latency")
    if measurement["unit_cost"] > policy["max_unit_cost"]:
        failures.add("cost")
    if mode == "hosted":
        if not {"input_tokens", "output_tokens", "quota", "billed_after_cancel"} <= set(measurement.get("hosted", {})):
            failures.add("hosted-evidence")
    elif mode == "self-hosted":
        details = measurement.get("self_hosted", {})
        if not {"prefill_ms", "decode_ms", "weights_bytes", "kv_bytes", "device_bytes"} <= set(details):
            failures.add("self-hosted-evidence")
        elif details["weights_bytes"] + details["kv_bytes"] > details["device_bytes"]:
            failures.add("device-memory")
    else:
        raise ValueError("unknown deployment mode")
    return failures

"""Fixture adapters for observable lifetime and operation-outcome assertions."""


def stream(open_resource):
    return iter(())


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

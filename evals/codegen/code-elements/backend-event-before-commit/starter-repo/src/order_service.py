class Transaction:
    def __init__(self, fail_commit=False, log=None):
        self.fail_commit = fail_commit
        self.log = log if log is not None else []
        self.committed = False

    def commit(self):
        if self.fail_commit:
            self.log.append("commit_failed")
            raise RuntimeError("commit failed")
        self.committed = True
        self.log.append("commit")


class EventBus:
    def __init__(self, log=None):
        self.log = log if log is not None else []
        self.published = []

    def publish(self, event):
        self.log.append("event")
        self.published.append(event)


class Cache:
    def __init__(self, log=None):
        self.log = log if log is not None else []
        self.values = {}

    def set(self, key, value):
        self.log.append("cache")
        self.values[key] = value


class OrderService:
    def update_status(self, order_id, status, transaction, events, cache):
        order = {"id": order_id, "status": status}
        events.publish({"type": "OrderUpdated", "order": dict(order)})
        cache.set(order_id, dict(order))
        transaction.commit()
        return order

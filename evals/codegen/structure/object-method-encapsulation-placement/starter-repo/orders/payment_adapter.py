class PaymentAdapter:
    def __init__(self, *, fail: bool = False) -> None:
        self.fail = fail
        self.refunded: list[str] = []

    def refund(self, order_id: str) -> None:
        if self.fail:
            raise RuntimeError("payment failure")
        self.refunded.append(order_id)

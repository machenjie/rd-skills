from dataclasses import dataclass


@dataclass
class Order:
    order_id: str
    created_at_minute: int
    status: str = "pending"
    paid: bool = True
    refund_hold: bool = False

    def cancellation_decision(self, now_minute: int) -> str:
        if self.status != "pending":
            return "denied"
        if now_minute - self.created_at_minute > 30:
            return "expired"
        if self.refund_hold:
            return "refund-hold"
        return "allowed"

"""Keyword-correct but wrongly placed cancellation implementation."""

from dataclasses import dataclass

from .payment_adapter import PaymentAdapter


@dataclass
class Order:
    order_id: str
    created_at_minute: int
    status: str = "pending"
    paid: bool = True
    refund_hold: bool = False

    def cancellation_decision(self, now_minute: int) -> str:
        """Pure decision: allowed, denied, expired, or refund-hold."""
        return "allowed"

    def cancel_with_provider(self, adapter: PaymentAdapter, now_minute: int) -> str:
        adapter.refund(self.order_id)
        self.status = "cancelled"
        return "cancelled"

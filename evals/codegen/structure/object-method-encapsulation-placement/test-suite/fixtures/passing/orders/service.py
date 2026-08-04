from .order import Order
from .payment_adapter import PaymentAdapter


def _requires_refund(order: Order) -> bool:
    return order.paid


class OrderCancellationService:
    def cancel(self, order: Order, *, now_minute: int, payments: PaymentAdapter) -> str:
        decision = order.cancellation_decision(now_minute)
        if decision != "allowed":
            return decision
        if _requires_refund(order):
            payments.refund(order.order_id)
        order.status = "cancelled"
        return "cancelled"

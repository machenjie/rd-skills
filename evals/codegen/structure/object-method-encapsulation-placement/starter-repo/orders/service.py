from .order import Order
from .payment_adapter import PaymentAdapter


class OrderCancellationService:
    def cancel(self, order: Order, *, now_minute: int, payments: PaymentAdapter) -> str:
        return order.cancel_with_provider(payments, now_minute)

def calculate_total(subtotal: int, preferred_customer: bool) -> int:
    discount = 10 if preferred_customer and subtotal >= 100 else 0
    return subtotal - discount

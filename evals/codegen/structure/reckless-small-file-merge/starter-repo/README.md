# Starter Repo

## Stack

Python service/use-case code with pytest-style tests and small boundary files.

## Initial State

`OrderCancellationService` coordinates cancellation behavior. The directory has
four small files: `payment_gateway_client.py`, `cancellation_window.py`,
`cancellation_policy.py`, and `cancellation_private_helper.py`. Only the private
helper is boundary-free and used by one owner. The adapter/client owns external
side effects, the value object owns an invariant, and the policy owns public
behavior tests.

## Files

- `orders/cancellation_service.py`
- `orders/payment_gateway_client.py`
- `orders/cancellation_window.py`
- `orders/cancellation_policy.py`
- `orders/cancellation_private_helper.py`
- `tests/orders/test_cancellation_service.py`
- `tests/orders/test_cancellation_policy.py`
- `tests/orders/test_cancellation_window.py`

## Constraints

The benchmark expects a behavior-preserving small-file merge decision. The
helper may merge into the service. Adapter/client, value object, and policy
files must remain separate unless a real boundary analysis proves otherwise,
which this scenario does not provide.

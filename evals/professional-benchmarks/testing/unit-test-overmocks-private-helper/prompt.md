Review this test proposal:

An AI adds a unit test for `OrderService.cancelOrder()`, but the test mocks
`_calculateRefundWindow()` and asserts that the private helper was called. It
does not assert the observable cancellation result, denied state, emitted event,
or refund outcome. The fixture is placed in `tests/shared/utils` even though it
is order-domain specific.

Decide whether this is acceptable unit coverage and state the evidence required.

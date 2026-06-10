Review this Python test plan:

An async FastAPI handler calls a blocking third-party SDK inside the event loop.
The change adds a normal unit test that mocks the SDK response, but there is no
async test harness, timeout/cancellation evidence, event-loop blocking check, or
runtime boundary validation.

Decide the language/runtime test strategy and evidence required.

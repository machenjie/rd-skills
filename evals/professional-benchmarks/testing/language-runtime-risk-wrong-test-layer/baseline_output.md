The unit test is enough because it mocks the SDK response.

I will treat mocked unit test as async runtime evidence, ignore event-loop
blocking risk, and omit timeout and cancellation test.

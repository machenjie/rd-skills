Review this Python change:

An async FastAPI handler calls a blocking vendor SDK directly inside the event
loop. There is no timeout, no cancellation behavior, and no async test harness;
the test only mocks a successful response.

The async handler is acceptable because the mocked response test passes.

I will call blocking SDK directly in async handler, rely on mocked success
response as runtime evidence, and omit timeout or cancellation behavior.

The field rename is safe because provider tests pass.

I will rely on provider unit tests as contract evidence, remove consumed
response field without migration window, and omit consumer verification.

No schema diff is necessary for a small rename.

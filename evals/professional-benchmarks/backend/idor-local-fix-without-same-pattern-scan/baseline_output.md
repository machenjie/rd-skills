Patched the invoice lookup by adding `user_id` to the query.

No wider scan was done because the bug was reported on this endpoint only. I did not add a new regression test; existing tests should cover it.

This is ready.

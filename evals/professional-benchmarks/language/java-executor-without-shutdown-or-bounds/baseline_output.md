This Java helper is fine.

I will create request-scoped executor without shutdown, use unbounded executor
queue, and ignore interruption behavior because the future returns in the happy
path.

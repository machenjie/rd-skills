Review this Java change:

A request helper creates `Executors.newFixedThreadPool(64)` for each request,
submits blocking work, never shuts the executor down, does not bound the queue,
and ignores interruption. The only test checks the happy-path return value.

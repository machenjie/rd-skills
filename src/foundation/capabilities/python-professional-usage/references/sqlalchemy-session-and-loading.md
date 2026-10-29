# SQLAlchemy Session and Loading

**Reference type:** targeted
**Load when:** SQLAlchemy loading, session state, expiration, flushing, or detached access affects current behavior.
**Do not load when:** The edit has no SQLAlchemy session or ORM-loading decision.
**Required by:** analysis-agent, task-agent, review-agent
**Required output:** boundary-decision, validation-plan, proof-limit

## Session Decisions

- Bind the SQLAlchemy version, synchronous or asynchronous API, session configuration, and database isolation.
- Assign a session to the intended unit of work. Sharing a session across concurrent work requires semantics the session does not supply automatically.
- Distinguish object identity from loaded data and transaction freshness. The identity map is not an unconditional query-result cache.
- Trace attribute access that can issue SQL. Lazy relationships and expired fields can turn serialization into database work.
- Check `expire_on_commit` before using objects after commit. SQLAlchemy 2.0 defaults to expiration, so retained objects can require another load.
- Distinguish expiration from detachment. Closing a session can leave an object unable to load attributes it still references.
- Choose eager loading or explicit value transfer for consumers that outlive the session. Disabling expiration alone does not load missing relationships.
- Treat `flush()` as database synchronization inside a transaction, not commit. A later rollback can invalidate the apparent write result.
- After a failed flush, restore the session through the documented rollback or disposal path before reuse.
- Bind bulk DML synchronization and event behavior to the exact API. Equal row counts leave per-instance unit-of-work behavior unproved.
- In asynchronous use, make database I/O boundaries explicit. Implicit attribute loading may fail outside a supported awaited context.
- Recheck state after `expire()` or `refresh()` against isolation and pending local changes. Refresh is not a substitute for a consistency contract.

## Distinguishing Checks

| Scenario | Observable check |
| --- | --- |
| Commit, then serialize an expired object | The test observes any reload and its transaction |
| Close the session before traversing an unloaded relationship | The consumer cannot silently depend on hidden I/O |
| Trigger a constraint failure during flush, then reuse the session | Recovery occurs before another valid unit of work |
| Compare ORM instance changes with bulk DML | Events, loaded state, and stored rows match the required contract |
| Run concurrent tasks against intended session boundaries | One task cannot consume another task's pending unit of work |

Return the loading plan, session lifetime, flush recovery, and backend-specific proof limits.

## Version Sources

- SQLAlchemy 2.0 examples: [Session basics](https://docs.sqlalchemy.org/en/20/orm/session_basics.html).
- Recheck the project's API and configuration before transferring these examples to another major version.

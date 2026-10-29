# Django ORM Evaluation and Transactions

**Reference type:** targeted
**Load when:** Django query evaluation, caching, bulk operations, or transaction boundaries affect data behavior.
**Do not load when:** The change has no Django ORM evaluation or transaction-lifetime decision.
**Required by:** analysis-agent, task-agent, review-agent
**Required output:** boundary-decision, validation-plan, proof-limit

## Evaluation Decisions

- Locate SQL execution separately from `QuerySet` construction. Iteration, serialization, templates, and related-object access can defer execution.
- Distinguish one evaluated QuerySet's cache from a new QuerySet or related-manager query. Repeated-looking access can execute different SQL.
- Check the selected `iterator()` behavior against the target Django version. Do not infer ordinary QuerySet caching or prefetch behavior.
- Place evaluation inside the intended transaction when its snapshot, locks, or consistency are required. Returning a lazy object can move evaluation outside it.
- Inspect the actual `atomic()` nesting and database isolation. A Python block does not add guarantees absent from the database.
- Treat `ATOMIC_REQUESTS` as wrapping the view. Template rendering and streaming-body execution can occur outside that transaction.
- Materialize the data needed beyond the boundary within its resource budget. An unbounded in-memory collection can replace one lifetime failure with another.
- Inspect implicit template callable access and serializer relationships. They can trigger hidden queries after the apparent read completed.
- Bind bulk behavior to the exact ORM operation. `update()` bypasses model `save()`; signal behavior differs across update and deletion APIs.
- Verify affected rows, constraints, and concurrent outcomes against the actual database backend. A mock QuerySet does not establish those semantics.
- Keep external effects tied to the required commit outcome. A rollback of database work does not undo an already sent message.

## Distinguishing Checks

| Scenario | Observable check |
| --- | --- |
| Build a QuerySet inside `atomic()`, evaluate after exit | SQL timing exposes the transaction actually used |
| Materialize the required values before exit | The later consumer does not issue the deferred query |
| Render a template or stream a response after the view returns | Hidden ORM access and database errors remain visible |
| Repeat ordinary iteration, then use a new query or iterator | Query counts reflect the intended cache behavior |
| Replace per-instance writes with bulk update | Required validation, hooks, and row outcomes are preserved or explicitly replaced |

Return the evaluation timeline, database assumptions, bulk-operation differences, and untested consumer paths.

## Version Sources

- Django 5.2 examples: [query optimization](https://docs.djangoproject.com/en/5.2/topics/db/optimization/), [transaction boundaries](https://docs.djangoproject.com/en/5.2/topics/db/transactions/), and [QuerySet APIs](https://docs.djangoproject.com/en/5.2/ref/models/querysets/).
- Recheck iterator, prefetch, and bulk semantics when the project's Django version differs.

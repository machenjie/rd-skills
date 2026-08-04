# Release Recovery Decision Patterns

Use these patterns only with a current accepted `version-compatibility` decision. They compare release-specific exposure and recovery mechanisms within its semantic bounds.

## Changed-Surface Recovery

| Surface | Accepted compatibility input | Release recovery choices to evaluate |
| --- | --- | --- |
| Application artifact | which revision and runtime inputs coexist with current state | redeploy, route away, disable path, or forward repair |
| Configuration or secret | which versions old and new code can parse and how propagation occurs | restore version, safe default, restart/reload, or bridge formats |
| Schema or durable data | which readers/writers remain compatible and what state is irreversible | leave additive state, compensate, restore, reconcile, or forward migrate |
| Job, queue, or cache | what remains in flight, retained, duplicated, stale, or partially applied | pause, fence, drain, replay, invalidate, reconcile, or resume |
| Route, flag, or exposure | who is exposed and how quickly a control change takes effect | reduce exposure, disable, restore route, or isolate affected scope |
| External provider | which provider-side actions persist beyond local code/config | reverse through provider, compensate, dual-run, or escalate to owner |
| Cluster or infrastructure | which desired/effective resources and stateful effects change | restore prior state, route around, repair drift, or forward reconcile |

## Decision Pattern

- Bind the changed surfaces and target environment to one release identity before exposure or recovery.
- Verify the accepted compatibility decision is fresh for that identity and its changed surfaces.
- Consume its allowed and forbidden old/new combinations, migration mechanism, retirement conditions, and rollback readability.
- Select exposure and observation from consequence, current telemetry, reversibility, policy, and authority, with the admissible breadth rationale recorded.
- Choose rollback when prior state remains compatible and observable.
- Choose forward repair, compensation, restore, or reconciliation when reversal would deepen damage.
- Preserve artifacts and compatibility paths until the exposure, retained-work, and recovery windows that need them close.
- Route missing, stale, or unresolved semantic compatibility to `version-compatibility`.
- Route pipeline enforcement to `ci-cd`, cluster runtime to `kubernetes-gateway`, image construction to `containerization`, and data-change execution to `data-migration-design`.

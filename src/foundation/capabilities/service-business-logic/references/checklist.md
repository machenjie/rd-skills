# Service Orchestration Checklist

- Name actor, intent, accepted input, terminal results, owning service boundary, and excluded responsibilities.
- Establish authorization scope before sensitive retrieval or document the non-disclosing scoped lookup.
- Identify the domain authority and reject duplicate invariant, transition, or calculation branches in orchestration.
- Map commit owner, participating repositories, durable handoff, rollback, and crash windows.
- Order events and external effects against commit; define timeout, cancellation, unknown outcome, replay, compensation, and terminal ownership.
- Preserve typed permission, absence, conflict, partial, timeout, duplicate, cancellation, dependency, and terminal outcomes.
- For queries, record visibility, consistency source, bounds, ordering, and intentional effects.
- Tie changed sequence and failure claims to current callers, ports, transaction/effect tests, and explicit proof limits.
- Route transport, domain, persistence, model mapping, full effect tracing, and specialized consistency decisions to their owners.

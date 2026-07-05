# Domain Impact Evidence Patterns

Use this reference when domain impact closure depends on source-backed facts, owner acknowledgement, or tests proving business semantics. Load only the evidence rows matching the changed domain surface.

## Evidence Map
- **Entity, value object, or aggregate change:** capture owning bounded context, system of record, invariant owner, persistence/API/event surfaces, and source-backed evidence for identity and lifecycle semantics.
- **Business rule or invariant change:** prove allowed and denied cases, enforcement boundary, bypass-path scan, historical invalid-state risk, cleanup obligation, and owner review or source citation.
- **State machine change:** prove transition table delta, forbidden transitions, side effects, compensation, regression tests, and event or audit output.
- **Domain event change:** prove producer, consumer list, event schema diff, version/upcaster plan, replay risk, migration owner, and contract test or schema validator output.
- **Cross-context ownership change:** prove context map, relationship pattern, ACL or translation boundary, writer scan, dependency direction, and team acknowledgement.
- **Business Semantic Pack claim:** mark each vocabulary, object, rule, workflow, or signal claim as FACT only when backed by current source, owner review, user source, or validation evidence.

## Evidence Rules
- Every accepted evidence item names source path or owner review, validation command or report artifact when available, freshness, and the exact domain claim it proves.
- Every evidence item also states what it does not prove: downstream consumer behavior, historical data cleanliness, replay safety, compliance interpretation, or future owner acceptance.
- Graph and memory are selectors only; they can choose files, events, or owners to inspect, but they cannot prove a domain fact without current source, owner review, user source, or validation.
- Do not close domain work when rule authority is split, event consumers are unknown, or forbidden transitions lack evidence; route to the owner gate instead.

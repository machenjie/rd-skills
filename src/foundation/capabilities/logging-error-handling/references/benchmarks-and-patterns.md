# Logging And Error Handling Benchmarks And Patterns

Use when the logging/error mechanism remains unresolved; skip when current policy selects it.

## Root-Relocated Error And Diagnostic Rules

- **Define error ownership and external meaning.** Preserve causal context across layers while translating only at owned boundaries; distinguish user, domain, dependency, transient, permanent, cancellation, and unexpected outcomes relevant to caller action.
- **Log an owned diagnostic event, not arbitrary data.** Name audience, decision enabled, event point, stable identity, outcome, and retention need before selecting fields or severity.
- **Preserve correlation across attempts and effects.** Carry request, operation, trace, job, message, tenant-safe, and real or effective actor identity needed to reconstruct a causal path without confusing retries with distinct business operations.
- **Classify terminal outcome accurately.** Avoid reporting handled intermediate retries, expected denial, cancellation, or fallback as terminal errors, and avoid hiding exhausted or partially applied work behind informational success.
- **Minimize sensitive and unbounded content.** Exclude secrets and raw bodies by default, transform personal or regulated fields according to current policy, and bound message, stack, collection, key, and payload expansion.
- **Control volume and cardinality at the source.** Derive event rate, level, sampling, aggregation, dynamic labels, and hot-path detail from current diagnostic need, cost, and incident consequence.
- **Separate diagnostics from audit records.** Identify the security-relevant outcome, accepted audit dependency, unresolved semantics, integrity, retention, access, sink, or durability, named specialist handoff, and gap without claiming protected-record closure.
- Log the same exception at each layer, producing duplicate noise without additional ownership or action.
- Store raw requests, tokens, personal data, stack detail, or dynamic high-cardinality values because they might help later.
- Treat a fallback or retry as success while the original failure, final disposition, or lost effect cannot be reconstructed.

## Comparison And Proof Limits

Expected outcomes use stable remediation and consequence level; unexpected failures keep safe cause, opaque results and retry/correlation. Allowlist fields, propagate context, bound labels and use stable codes. Final-edit fixtures prove named paths, not production sinks/traffic, uninspected adapters, retry policy or protected audit closure; route these to owners.


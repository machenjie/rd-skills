# Development Process Checklist

- Select mode: compact trace, process-evidence repair, logging-sensitive trace, or coverage/reporting audit.
- State PDD problem, impact, acceptance, constraints, non-goals, risk surfaces, and validation signal.
- State DDD terms, ownership, invariants, side-effect boundaries, and existing code owner.
- State SDD modules/files, public API, data flow, error contract, failure modes, logging decision, design decision points, no-choice rationale when empty, assumption policy, observability, compatibility, and rollback/recovery.
- Map TDD acceptance, invariants, public API, failure modes, logging/security, and validation commands.
- Mark each phase `present`, `inferred`, `degraded`, `missing`, or `not_applicable` with an evidence source.
- Keep inferred case metadata separate from present trace evidence.
- Reject generic process facts that could fit any case.
- Separate registered coverage from dry-run, promoted, and actual live-run coverage.
- Record validation command, exit code or not-run status, freshness, what it proves, and what it does not prove.
- Name residual risk, skipped boundaries, and next gate.
- Keep the trace compact; load detailed phase contracts or output gates only when needed.

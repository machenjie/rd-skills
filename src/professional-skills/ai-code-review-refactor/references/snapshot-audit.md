# Snapshot Audit

- Bind the audit to a fixed commit or clearly identified code snapshot.
- State paths, modules, audit questions, depth, and available evidence.
- Inspect actual source and the callers, state transitions, or contracts needed to establish a reachable failure.
- Record each finding's trigger, mechanism, consequence, path, and supporting evidence.
- Separate concrete defects from unresolved hypotheses and optional improvements.
- Track inspected and uninspected scope; sampling cannot support a whole-repository assurance claim.
- Report a bounded no-finding result when no candidate survives source verification.
- Keep the audit read-only and return repairs to the implementation owner.
- Explain a module without audit judgments when explanation is the requested outcome.

A snapshot requires no invented diff. Reproduction or tests may strengthen a finding, but failed setup alone does not establish a product defect.

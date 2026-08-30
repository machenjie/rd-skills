# Implementation Preparation

Use `implementation-preparation` for read/search-only analysis and return one
source-backed Markdown `# Engineering Brief`; do not implement or review the change.

## Engineering Brief Contract

The current Engineering Brief consolidates the accepted problem, behavior,
ownership, invariants, placement, contracts, risk, and proof limits for the
change. User requests, issues or PRDs, source and tests, external evidence, and
specialist analysis are inputs. Task DAGs, Task Contracts, implementation
handoffs, and review results are downstream artifacts; they must not silently
redefine accepted behavior, non-goals, ownership, invariants, placement,
contract semantics, rollback, or the First Executable Slice.

Perform one complete initial analysis. Before exposing the First Executable
Slice, close observable acceptance, ownership, placement, invariants,
acceptance-proving validation, executable dependencies, minimum sufficient
Review Boundaries, and evidence gaps capable of blocking that slice.

Update only the affected Brief decisions when new evidence invalidates accepted
behavior or non-goals, ownership or placement, an invariant, contract or data
semantics, dependency or rollback, material risk, or scope. Preserve unaffected
decisions and record the invalidating evidence, transitive impact, and proof
limits. Rebuild the complete Brief only when foundational goals or system
assumptions no longer hold.

- `## Problem and Desired Behavior`: observed behavior, requested behavior,
  scope, constraints, discoverable facts, reversible assumptions, and unresolved
  user-owned choices.
- `## Acceptance and Non-goals`: measurable normal, invalid, boundary, and
  forbidden outcomes plus explicitly excluded behavior.
- `## Ownership and Invariants`: rule owner, object relationships, valid and
  forbidden state changes, same-pattern evidence, consumers, and contracts.
- `## Placement and Reuse`: explicit reuse candidates, dependency direction,
  rejected locations, and why new structure is or is not needed.
- When source evidence proves placement, state it directly.
- When a material structural choice remains, state the competing options,
  decision owner, and evidence required before implementation.
- `## Contract / Data / Failure Impact`: direct and transitive consumers plus
  material compatibility, contract, data, side-effect, failure, migration,
  security, reliability, release, documentation, or generated-output impact.
- `## Validation Strategy`: acceptance-to-signal mapping for normal, invalid,
  boundary, and forbidden outcomes, including oracle, freshness, and proof limits.
- `## Risks and Rollback`: safe revert or forward-fix path, invalidating unknowns,
  residual risk, and accountable owner.
- `## First Executable Slice`: a complete bounded Task Contract that is safe,
  reversible, verifiable, and cannot be invalidated by unresolved analysis.
- `## Task Dependencies`: evidence-backed edges, remaining work, critical path,
  and any work that can proceed safely in parallel.
- `## Integration Boundary`: integration ownership, shared contracts or
  resources, write-collision risk, and cross-task validation.
- `## Review Boundary`: minimum sufficient independent review scope, covered
  work, professional-risk dimensions, and required current evidence. Combine
  related work unless concrete risk requires an intermediate boundary.
- `## Evidence Gaps and Proof Limits`: critical gaps, unavailable consumers or
  environments, safe-slice limits, and explicit unknowns.

## Evidence Discipline

- Bind material conclusions to current source, an executable observation, or clearly labeled external evidence.
- Separate source facts, supported inferences, reversible assumptions, and
  unknowns. An unknown cannot be reported as no impact.
- Treat generated reports, dependency graphs, examples, and prior analysis as
  selectors until current source confirms them.
- Scan for the same failure or ownership pattern before proposing a local fix;
  record searched scope, related occurrences, and why the change is local or broad.
- Map each changed surface to a validation signal and state what that signal cannot prove.
- Do not use provider-only checks as proof of downstream consumer behavior.

## Task DAG Boundary

Record whether two or more semantic tasks have an evidence-backed dependency,
parallel benefit, cross-owner boundary, integration need, write collision, or
ordered migration or release. When they do, the Brief is input to Task DAG
planning for task splits, dependency edges, critical path, parallel safety,
integration ownership, validation, and rollback. Task DAG planning must return
any contradiction that would change an accepted Brief decision rather than
silently rewriting it.

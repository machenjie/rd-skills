# High-Risk Design Review Checklist

Use for a high-risk Engineering Brief whose decisions affect multiple
downstream tasks.

- Problem and acceptance are observable and internally consistent.
- Ownership and invariants match current source evidence.
- Placement and reuse preserve dependency direction.
- Public contract, data, failure, compatibility, and rollback effects are
  explicit.
- The First Executable Slice is safe, verifiable, and reversible.
- Task dependencies and workspace requirements prevent conflicting writes.
- Review and validation boundaries cover the integrated result.
- User-owned destructive, privileged, production, or irreversible decisions
  remain with the user.

Return findings and residual risk; do not turn this review into a mandatory
multi-phase process.

## Professional Decision Rules

- Test the brief as four connected dimensions: problem and acceptance; ownership and invariants; placement, contract, and failure design; acceptance-to-validation mapping.
- Require decisions only when they change downstream work, risk, rollback, or user-visible behavior.
- Confirm the First Executable Slice remains safe, verifiable, and reversible.
- Reject dependency cycles, conflicting writes, unowned shared contracts, and rollback claims without an executable path.

## High-Value Gotchas

- More artifacts do not improve accuracy when they repeat the same facts.
- A complete-looking brief can still name the wrong owner or omit version skew and failure behavior.
- Review breadth must remain proportional to the concrete risk.

## Execution Checklist

1. Verify source evidence and acceptance.
2. Check owner, invariants, reuse, and rejected placements.
3. Check public contract, data, failure, compatibility, and rollback effects.
4. Check dependencies, workspace requirements, integration, review, and validation boundaries.

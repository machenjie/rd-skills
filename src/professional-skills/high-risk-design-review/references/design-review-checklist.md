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

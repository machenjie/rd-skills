# AI Review Output And Gates

Load only for an exhaustive implementation or repair-diff review needing the full finding, decision, blocked, or re-review contract.

## Do Not Load

Skip when the compact root is sufficient. An unavailable actual diff blocks implementation review. This Reference owns implementation-diff review judgment; specialized domain decisions remain outside its authority.

## Output Contract

Return in this order:

1. **Findings:** list Critical/High/Medium/Low findings first; give path/line or symbol, reachable failure, evidence, impact, severity, required outcome, and non-implementing correction direction. State explicitly when none exist.
2. **Review decision:** assess specification before quality; choose `Approved`, `Returned for remediation`, or evidence-blocked `Blocked`; number remediation and bound approval/exclusions.
3. **Reviewed scope:** name actual diff, inspected changed files/source/tests, unreviewed reachable boundaries, and implementer/reviewer separation.
4. **Source-to-impact evidence:** connect each finding to acceptance/invariant through current diff, source, tests, contracts, validation, or authoritative metadata; separate fact, assumption, and unverified behavior.
5. **Behavior preservation:** for repair/refactor, state invariant/observable preservation, proof and changed-code coverage, intentional delta, and warranted same-pattern/reuse/placement scope.
6. **Repair and re-review:** map blocking findings to repair and re-review stage; close only against latest repair diff plus fresh validation.
7. **Evidence limits and next action:** record each run and result, stale/skipped/unavailable checks, proof limits, residual risk, and next owner/action.

## Quality Gate

1. Report findings only from current evidence of an acceptance gap or reachable impact; otherwise record an evidence limit or missing proof.
2. Calibrate severity by credible impact, reachability, scope, reversibility, and release risk; style alone is non-blocking.
3. For possibly invented/version-sensitive API or contract use, require sufficient version-bound search, typecheck, build, or authoritative metadata.
4. When repair/refactor may change behavior, require bounded characterization, regression, contract, or semantic-diff evidence and name uncovered paths.
5. When recurrence evidence is credible, bind required same-pattern scope and exclusions to its mechanism.
6. Blocking findings require repair, fresh relevant validation, and independent re-review of the latest diff.
7. When assigned expertise or evidence is insufficient, hand off the triggered owner and proof; never load a gate by default.
8. Bound approval to inspected diff/files/contracts/paths; list partial scope and exclude unsupported production-safety or broad-equivalence claims.

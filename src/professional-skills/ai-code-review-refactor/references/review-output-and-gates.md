# AI Review Output And Gates

Load only for an L5 implementation or repair-diff review that needs the full finding, approval, blocked, or repair/re-review contract.

## Do Not Load

Do not load when the root output contract or compact checklist is sufficient. An inaccessible actual diff blocks implementation review; it does not permit review from a changed-file summary. This reference governs AI-review judgment; named Layer 3 Skills own specialized architecture, security, contract, test, and implementation decisions.

## Output Contract

Return these sections in order:

1. **Findings:** Put Critical, High, Medium, and Low findings first.
   - For each finding, give its path and line or symbol, reachable failure scenario, and source evidence.
   - State user or system impact and severity rationale.
   - State the required outcome and a correction direction without implementing it.
   - If no findings exist, say so explicitly.
2. **Review decision:**
   - Record specification compliance before code quality, then `Approved`, `Returned for remediation`, or `Blocked`.
   - Use `Blocked` only for unavailable required evidence or unverifiable scope, naming the missing evidence, unverified scope, and unblock condition.
   - Number remediation actions and state exactly what an approval covers and excludes.
3. **Reviewed scope:** Name the actual diff, every changed file inspected, relevant source and tests read, and any changed or reachable boundary left unreviewed. Record implementer/reviewer separation.
4. **Source-to-impact evidence:** Tie current evidence to the affected acceptance criterion or reachable impact path.
   - Use the diff, source, tests, contracts, validation, or authoritative dependency metadata.
   - Link each finding through the applicable call, state, contract, or affected invariant.
   - Distinguish facts from assumptions and unverified behavior.
5. **Behavior preservation:** For a refactor or repair, state which affected invariants and observable behavior remain unchanged.
   - Name the proof, changed-code-to-test coverage, and any intentional delta.
   - Report same-pattern scope, result, and exclusions only when the failure mechanism credibly recurs.
   - Summarize reuse or placement only when that decision was triggered and assigned.
6. **Repair and re-review:** Map each blocking finding to its required repair.
   - Identify the stage that must be re-reviewed.
   - Close the finding only against the latest repair diff plus fresh validation.
7. **Evidence limits and next action:** Record each validation or command actually run with its outcome, plus stale, skipped, or unavailable checks. The same evidence states its proof limits, residual risk, and recommended next owner and action.

## Quality Gate

1. Report a finding only when current diff, source, test, contract, validation, or authoritative dependency evidence supports an acceptance gap or reachable source-to-impact path. Otherwise, record the uncertainty as an evidence limit or request the missing proof.
2. Calibrate severity from credible impact, reachability, affected scope, reversibility, and acceptance or release risk; do not promote style preference into a blocking defect.
3. When generated code depends on an API, symbol, dependency, or contract that may be invented or version-sensitive, require proof against the declared version. Repository search, typecheck, build output, or authoritative package metadata are candidate mechanisms; cite why the selected evidence is sufficient.
4. When a refactor or repair may alter observable behavior, require bounded equivalence evidence.

Select characterization, regression, contract, or semantic-diff checks from the affected behavior. Identify uncovered paths explicitly.

5. When the failure mechanism provides a credible recurrence signal, require a same-pattern search scope tied to that mechanism and explain exclusions. Sibling implementations, call sites, or analogous contracts form evidence when warranted; an isolated finding without recurrence evidence does not trigger the scan.
6. When a finding blocks approval, require repair and fresh relevant validation.
   - Require independent re-review of the latest diff at the stage that raised the finding.
   - Do not accept implementer assurance or an earlier passing result as closure.
7. When specialized risk exceeds assigned skills or evidence, return a handoff naming the triggered owner and required proof.
   - Examples include sensitive-data, public-contract, schema, cross-boundary, and performance-sensitive impact.
   - Name a gate or Layer 3 Skill only when selected from the actual risk.
   - Do not load one by default.
8. Define approval by the inspected diff, files, contracts, and exercised paths.
   - When evidence is partial, list uninspected behavior.
   - Exclude production-safety and broad-equivalence claims that the evidence does not support.

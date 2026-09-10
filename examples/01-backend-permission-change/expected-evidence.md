# Expected Evidence

- inspect: route, controller, service, repository, permission policy, existing invoice tests, API error format, and adjacent download endpoints.
- validation evidence: allowed-admin, denied-non-admin, and denied-cross-organization tests; the targeted backend command and actual result after the final edit; API contract compatibility check.
- independent review: the assigned security reviewer inspects the actual tenant boundary and its tests, identifies any reachable bypass, and states what the inspection does not prove.
- ordinary defect repair: if Review finds a missed denied path, the original backend Task first reproduces the failure, verifies the cause, and scans for the same invoice-lookup pattern; it repairs the owning code and runs fresh targeted validation, then finishes. This finding alone does not schedule re-review.
- residual risk: any external response consumers that repository inspection could not verify.
- result: actual changed files, commands, results, denied-path evidence,
  compatibility note, unverified scope, residual risk, and next step if needed.

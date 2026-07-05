# Expected Evidence

- read before plan: route, controller, service, repository, permission policy, existing invoice tests, API error format, and adjacent download endpoints.
- TDD: add or update allowed-admin and denied-cross-organization tests before or alongside implementation.
- validation evidence: targeted backend test command, same-pattern scan for invoice lookup by identifier, and API contract compatibility check.
- independent review: `quality-test-gate` reviews the implementation and denied-path coverage; `security-privacy-gate` reviews authorization boundary evidence.
- repair/re-review: any missing denied path routes back to `backend-change-builder`, then re-review repeats.
- residual risk: undocumented external consumers of the invoice response format.
- handoff: include route manifest, inspected files, test output, denied-path evidence, compatibility note, residual risk, and next release gate.

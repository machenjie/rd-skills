Selected stage: bug-fix.
Selected professional skill: backend-change-builder.
Selected capabilities: permission-boundary-modeling, authentication-authorization, agent-execution-discipline, regression-testing.

Hidden risks: IDOR from missing object ownership check; tenant data leak from identifier-only query; local fix without same-pattern scan.

Inspected boundaries: controller route, service method, repository invoice/resource ID queries, permission policy, tenant filter path, and sibling resource lookups.

Evidence required: same-pattern scan for invoice/resource ID queries; denied-case regression test with another user or tenant; authorization and tenant filter path inspected.

Validation command: `python3 -m pytest tests/backend/test_invoice_authz.py`.
What evidence proves: denied cross-tenant access and sibling-query scan coverage.
What evidence does not prove: production data contains no historic leak.

Output obligations covered: boundaries inspected for controller, service, repository, and permission policy; validation evidence for denied-case regression; residual risk and next gate stated.

Residual risk: historic access logs were not audited.
Next gate: security-privacy-gate if audit or breach assessment is required.

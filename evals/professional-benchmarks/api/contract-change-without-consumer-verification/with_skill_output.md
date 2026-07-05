Selected stage: implementation-planning.
Selected professional skill: data-api-contract-changer.
Selected capabilities: contract-testing, version-compatibility.

Hidden risks: contract change without consumer verification; provider-only test misses consumer compatibility; breaking API field change lacks schema diff or migration evidence.

Inspected boundaries: `GET /accounts` response schema, provider implementation, OpenAPI source, generated clients, mobile consumer, consumer pact expectations, and deprecation window.

Evidence required: consumer verification command output; provider contract validation output; schema diff and compatibility assessment.

Output obligations covered: provider and consumer evidence; compatibility claim; what evidence proves and does not prove; residual unverified consumer owner.

Validation command: `openapi-diff old.yaml new.yaml && pact-broker can-i-deploy --pacticipant accounts-api --version <sha>` (not run in fixture; expected outcome is compatibility report and consumer verification output).
What evidence proves: named consumers can still parse the provider response or have a versioned migration path.
What evidence does not prove: unknown consumers, production traffic compatibility, or business semantics outside the schema.

Residual risk: one partner SDK consumer remains unverified; owner: data-api-contract-changer.
Next gate: delivery-release-gate before removing `account_status`.

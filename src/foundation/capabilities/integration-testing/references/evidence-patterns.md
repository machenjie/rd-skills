# Integration Testing Evidence Patterns

Use this reference when integration-testing closure depends on repository inspection, prior task evidence, observable action sequence, validation freshness, real-boundary proof, fixture/fake/emulator calibration, tool permission boundaries, or changed-surface-to-validation mapping. Keep it as an evidence map, not a second tooling guide.

## Changed-Integration-Surface-To-Validation Map

| Integration claim | Minimum evidence | What it proves | What it does not prove |
| --- | --- | --- | --- |
| Real boundary is exercised | Current source/test/config paths, components included, real dependency or calibrated substitute, and why a unit test cannot prove the seam | The inspected test crosses the named seam that carries the risk | Full user journeys, unrelated services, or production-scale behavior are covered |
| Accepted data lifecycle is verified | `test-data-management` fixture, namespace, sensitive-data, cleanup, and parallel-safety decision plus seam observations | The exercised seam honors the accepted data-lifecycle behavior | Shared staging state, hidden provider state, or future parallel suite behavior is fully safe |
| Disposable non-data infrastructure is cleaned | Integration-owned resource identity, isolation boundary, cleanup command, and postcondition | The exercised test cleans its disposable non-data seam infrastructure | Test-data lifecycle or shared infrastructure ownership is established |
| Failure path is covered | Injected constraint/timeout/error/denial, expected final durable state, retry/DLQ/rollback assertion, and command result | The selected seam handles the named failure without the inspected partial-state bug | Every failure mode, scheduler interleaving, or production recovery path is covered |
| Stub/fake/emulator is calibrated | Stub/fake/emulator source, contract or captured fixture version, request/response verification, and recalibration command or owner | The substitute matches the named contract for the inspected behavior | All provider behavior, undocumented fields, or future contract drift is proven |
| Auth and tenant scope are realistic | Principal/role/scope fixture, tenant/object predicate, denied-case identity, and no-state-change assertion | The inspected real auth path covers allowed and denied access for the named scope | All roles, policy combinations, or external identity provider behavior are covered |
| Prior integration evidence is fresh | Current changed-path map, fixture/generated artifact version, command/report path, exit code/status, and final-edit freshness | The prior run still covers the current wiring and fixture graph | Later source/config/migration/schema/container changes remain covered |

## Evidence Quality Labels

- **Strong evidence**: current source/test/config/fixture inspected, real boundary or calibrated substitute named, command or artifact recorded, exit code/status captured, final-edit freshness stated, and proof limits named.
- **Weak evidence**: happy-path smoke only, mock-only test for a real seam, old CI output, uncalibrated fake, shared staging success, or prior claim without current source.
- **Missing evidence**: no boundary map, accepted test-data decision, seam cleanup verification, failure path, relevant auth denial, command/status, or owner for not-run validation.
- **Invalid evidence**: mocked primary seam presented as integration proof, catch-all HTTP stub, shared uncontrolled production/staging dependency, stale generated fixture, or inaccessible report.

- If shared sandbox, cloud emulator, connector, credential-backed provider, staging dependency, destructive cleanup, or migration-backed integration run, require explicit scope, redaction, rollback/cleanup, stop condition, and retained-output boundary.
- Classify the mapped risk as real boundary, accepted data lifecycle, disposable non-data infrastructure, failure path, calibrated substitute, auth scope, or freshness.

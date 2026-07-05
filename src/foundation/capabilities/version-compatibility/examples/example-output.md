# Example Output

```markdown
## Compatibility Assessment

mode_selected: API/DTO compatibility + event/schema compatibility + rollout and rollback compatibility

source_evidence:
- OpenAPI `payments.yaml`, `PaymentUpdated.avsc`, generated TypeScript and Kotlin clients, payment web/mobile caller search, event consumer list, contract tests, production enum telemetry.
- graph_memory_trajectory_judgment: prior note saying "internal consumers only" rejected because mobile client and partner webhook consumer are present; existing schema registry FULL mode accepted after source check.

affected_contract:
- `PaymentStatus` enum in REST API response and `PaymentUpdated` event.

change_description:
- Add `PENDING_REVIEW`.

consumer_inventory:
- Web app, iOS/Android apps, Kotlin SDK, partner webhook consumer, fraud-reporting job.
- Unknown-consumer risk remains for partner-side internal processors; partner owner must confirm.

compatibility_matrix:
- Old producer -> new consumer: safe; new consumer already handles old statuses.
- New producer -> old consumer: conditional/breaking for old mobile and partner consumers unless unknown enum is tolerated.
- Old code reading new data after rollback: risky if new status is persisted before old code supports fallback.
- New code reading old data: safe.

compatibility_classification:
- Structure: enum expansion.
- Meaning: new review lifecycle state.
- Validation/default: no request validation change.
- Behavior: consumers must not treat unknown status as terminal failure.

migration_strategy:
- Bridge through unknown-status handling before producers emit the new value.
- Producer emission guarded by feature flag until consumer readiness and telemetry gates pass.

rollout_sequence:
1. Release consumers and SDKs that map unknown payment status to pending/review-safe behavior.
2. Verify contract tests and generated-client compile for old and new statuses.
3. Enable producer flag for internal traffic.
4. Monitor API client errors, event deserialization errors, and status distribution.
5. Enable partner/webhook emission only after partner confirmation.

rollback_behavior:
- Disable producer flag.
- Keep unknown-status tolerance permanently.
- If any new status has been persisted, old code must map it to pending or rollback is not safe.

deprecation_window:
- None for enum value; compatibility rule becomes open-enum/unknown handling.

schema_registry_compatibility_mode:
- FULL for payment events.

generated_client_impact:
- TypeScript open enum helper generated.
- Kotlin sealed enum requires unknown fallback variant before release.

telemetry_gate:
- Old mobile versions with strict enum parsing below approved threshold.
- Event deserialization errors remain zero through canary.

contract_test_plan:
- OpenAPI enum fixture for known and unknown status.
- Avro schema registry compatibility check.
- Generated Kotlin/TypeScript compile tests.
- Partner webhook replay fixture.

changed_compatibility_to_validation_map:
- Enum expansion -> generated-client compile + contract fixtures.
- Event payload -> schema registry FULL check + replay.
- Rollback -> old-code fallback test or residual risk owner.
- Partner readiness -> partner confirmation and canary telemetry.

handoff_boundaries:
- `contract-testing`: executable API/event/generated-client checks.
- `consumer-impact-analysis`: partner and mobile consumer readiness.
- `delivery-release-gate`: flag rollout, canary, and rollback decision.

evidence_limits:
- Partner internal processors were not inspected directly.
- Production old-app adoption telemetry must be refreshed before enablement.
```

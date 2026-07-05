# Example Output

```markdown
## DTO Schema Contract

mode_selected: existing DTO evolution

boundaries_inspected:
- Schema: `openapi/refunds.yaml`
- DTO class: `src/refunds/dto.py`
- Mapper: `src/refunds/mapper.py`
- Generated client: `clients/typescript/refunds.ts`
- Prior memory: refund request mentioned in migration notes; accepted only as a naming hint

source_evidence:
- Refund request is a public API request body.
- Mapper currently allowlists `amount`, `currency`, `reason`, `note`, and `idempotencyKey`.

graph_memory_trajectory_judgment:
- Repository graph confirms one request DTO and one TypeScript generated client.
- Project memory does not prove all consumers; unknown-consumer risk remains.

dto_name: RefundRequest
direction: request
purpose: client requests a refund for an existing charge
owner: payments API
contract_surface: public HTTP API request

fields:
- `amount`: string decimal, required, not nullable, absent invalid, empty invalid, example `"10.35"`, sensitive financial, maps to Money value object.
- `currency`: string ISO 4217, required, not nullable, absent invalid, empty invalid, example `"USD"`.
- `reason`: string enum, required, not nullable, values `CUSTOMER_REQUESTED`, `FRAUD`, `DUPLICATE`; unknown invalid for requests.
- `note`: string, optional, nullable; null clears note, absent leaves note unchanged, empty stores empty note, max 500 characters.
- `idempotencyKey`: string, required, max 128 characters, deduplicates retried refund requests.

additional_properties_policy:
- Request DTO rejects unknown fields.

validation_rules:
- Amount must be a positive decimal string.
- Currency must be supported by the account.
- Unknown fields return a validation problem detail.

mapping_spec:
- DTO maps to `RefundCommand` through explicit allowlist.
- Request DTO is not passed into domain logic.

compatibility_classification:
- Adding optional `note` is compatible if absent means unchanged.
- Renaming `reason` enum values is breaking and requires a new version or bridge.

schema_version_and_source:
- OpenAPI component `RefundRequest`, version v1.
- TypeScript generated client must be regenerated before release.

consumer_contract_tests:
- OpenAPI schema validator.
- Generated TypeScript compile.
- Unknown-field rejection fixture.
- Null-vs-absent mapper fixture.

changed_dto_to_validation_map:
- `note` semantics -> null, absent, empty fixtures.
- `amount` type -> schema validator and money parsing unit.
- `idempotencyKey` -> duplicate request behavior test handoff.

reuse_and_placement_rationale:
- Reuse existing OpenAPI component and mapper; do not expose `RefundEntity`.

behavior_preservation:
- Existing clients that omit `note` keep prior behavior.

validation_evidence:
- Not verified yet; commands and fixtures above are required before release.

handoff_boundaries:
- `api-contract-design` for endpoint status codes.
- `error-code-design` for problem detail code.
- `version-compatibility` for generated-client rollout.

evidence_limits:
- Partner consumers and production telemetry were not inspected.
- Residual risk owner: payments API.
```

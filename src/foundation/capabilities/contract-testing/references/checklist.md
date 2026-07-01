# Contract Testing Checklist

## Scope

- Identify provider, consumer, contract surface, schema source, version, and release cadence.
- Classify the mode: API schema, event/message, consumer-driven pact, vendor fixture, or compatibility repair.
- Record skipped boundaries such as unknown consumers, unqueried telemetry, unavailable broker, or provider-internal behavior.

## Coverage

- Verify success, error, auth, pagination, nullability, default, enum, unknown-field, and version behavior.
- Include examples that represent supported consumer expectations, not provider implementation details.
- Check backward compatibility or document the approved breaking-change path, migration window, and rollback behavior.
- Validate events, webhooks, schemas, generated clients, and vendor fixtures with machine-readable checks where possible.

## Evidence

- Map each changed surface to provider verification, consumer verification, schema diff, registry check, generated-client check, fixture replay, or residual risk.
- Reconcile project memory, repository graph, prior summaries, and execution trajectory as selectors, not proof.
- Mark validation freshness after the final schema, fixture, generated-client, broker, registry, or docs edit.
- Record tool permission boundaries for shell, broker, registry, vendor sandbox, fixture capture, and sensitive fixture redaction.
- Run provider verification in CI before release or name the owner and release consequence for a not-run check.

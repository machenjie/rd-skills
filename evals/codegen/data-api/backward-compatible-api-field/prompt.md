# Benchmark Prompt

## Task

Add a backward compatible `preferred_contact_method` field to the customer
profile API response and update validation for clients that choose to send it
on profile update.

## Context

Existing clients call `GET /customers/{id}/profile` and `PATCH
/customers/{id}/profile`. The response currently includes name, email, phone,
and marketing consent. New clients need a nullable preferred contact method of
email, phone, or sms. Existing clients must keep working without changes.

## Requirements

- Add the response field without removing or renaming existing fields.
- Accept the new field on PATCH when present and validate allowed values.
- Default omitted values safely for existing customers.
- Update schema, DTO, tests, and API documentation examples.
- Add contract tests proving old clients can omit and ignore the field.

## Constraints

- Do not make the new field required for existing clients or existing rows.
- Do not overload marketing consent as contact preference.
- Do not change unrelated customer profile behavior or response status codes.

## Deliverables

- Updated DTO, controller, persistence mapping, and docs.
- Migration or data default note for existing profiles.
- Contract and regression tests for old and new client behavior.

## Completion Evidence

- Passing unit, integration, and contract tests.
- API diff or schema note showing the change is additive.
- Documentation examples for responses with and without the new field.
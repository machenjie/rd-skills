# Security Checks

## Threat Surface

Model leakage can expose persistence-only fields, internal flags, audit metadata, or generated schema internals to API consumers.

## Required Checks

- Persistence-only fields are excluded from API and event payloads unless explicitly part of the contract.
- Validation owner prevents unsafe client-supplied values from entering the domain.
- Generated models do not bypass authorization or domain validation.

## Rejection Cases

- Reject ORM model responses that include internal fields.
- Fail when mapper logic trusts API DTO permission flags.
- Reject event payloads that expose private persistence columns.

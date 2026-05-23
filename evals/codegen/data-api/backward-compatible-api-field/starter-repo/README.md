# Starter Repo

## Stack

TypeScript Node API with strict DTO types, repository mapping, OpenAPI schema,
and contract tests. The starter uses existing validation helpers and a small
in-memory repository fixture.

## Initial State

The customer profile API has stable GET and PATCH behavior with tests for name,
email, phone, and marketing consent. There is no preferred contact field in the
DTO, schema, persistence mapper, or docs.

## Files

- `src/customers/profileController.ts` handles GET and PATCH routes.
- `src/customers/profileDto.ts` defines request and response DTOs.
- `src/customers/profileRepository.ts` maps stored profile fields.
- `openapi/customer-profile.yaml` documents the public API.
- `tests/customerProfile.contract.test.ts` covers existing client behavior.

## Constraints

Preserve public route names, status codes, and existing field names. New values
must use existing validation and error response conventions. Avoid global schema
rewrites outside the customer profile contract.
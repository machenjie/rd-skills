# Benchmark Prompt

## Task

Refactor an account profile endpoint that uses the API DTO as the domain object and returns the ORM model directly from one response path.

## Context

The starter repository mixes request DTO validation, domain behavior, database columns, event payload serialization, and view model fields in one class. A mapper also applies a business eligibility rule.

## Requirements

- Separate API DTO, command/query object, domain object, value object, persistence model, event payload, and view model as needed.
- Define mapping owners and validation owners.
- Preserve null, default, optional, serialization, and version compatibility semantics.
- Keep generated models at generated boundaries.
- Add tests for mapping and compatibility.

## Constraints

- Do not use DTOs as domain objects.
- Do not leak ORM or persistence models to API responses.
- Do not let mappers own business rules unless the mapper is explicitly a policy.
- Do not change null/default semantics accidentally.

## Deliverables

- Model Boundary Map.
- Mapper or assembler placement decision.
- Mapping tests and compatibility cases.
- Rejected leakage alternatives.

## Completion Evidence

- API, domain, persistence, event, and view models have explicit boundaries.
- Response fields no longer expose persistence-only data.
- Tests prove null/default/optional behavior and schema version compatibility.

# Benchmark Prompt

## Task

Add tenant invitation normalization without duplicating existing helper logic.
The starter repo already contains `normalizeEmail()`,
`validateTenantAccess()`, and `formatMoney()` in established modules.

## Context

The invitation flow currently compares raw email input before looking up an
existing invite. Similar normalization already exists in the identity module,
and tenant authorization already goes through a shared access policy owned by
the tenant module.

## Requirements

- Reuse `normalizeEmail()` for email normalization.
- Reuse `validateTenantAccess()` before invite lookup.
- Do not create a new `shared/utils` business helper.
- Add focused tests proving the invitation flow uses normalized email and
  preserves tenant authorization.
- Include an implementation structure note naming searched files and rejected
  duplicate helper alternatives.

## Constraints

- Do not reimplement email normalization with local string manipulation.
- Do not move tenant access validation into the invitation service.
- Do not change `formatMoney()` or unrelated billing behavior.

## Deliverables

- Updated invitation flow code.
- Tests for normalized email lookup and tenant access denial.
- Short Implementation Structure Plan covering reuse candidates, placement,
  dependency direction, and test location.

## Completion Evidence

- Unit or integration tests fail if normalization is duplicated incorrectly.
- Review evidence shows existing helpers were searched and reused.
- No new shared utility contains tenant or invitation business terminology.

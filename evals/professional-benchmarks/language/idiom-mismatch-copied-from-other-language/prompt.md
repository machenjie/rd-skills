Review this TypeScript backend change:

The PR adds `common/helper.ts`, `AbstractOrderDeadlineFactory`,
`IOrderDeadlineProcessor`, `data`, and `handle()` by copying Java service
patterns into an existing repository that uses feature modules, named services,
domain vocabulary, and camelCase request DTOs. The change bypasses the existing
`OrderPolicy` deadline method and adds framework-inconsistent naming without
formatter, lint, or typecheck evidence.

# Naming Taxonomy — Full Table

Deep reference for the `## Naming` rules in `implementation-structure-design`. The capability
body carries the decision-critical summary and the category list; this file carries the full
naming taxonomy table. It is loaded in the `dev` profile and by skill authors.

Use the narrowest accurate category. Do not use these words interchangeably:

| Category | Means | Belongs In | Naming Guidance | Reject When |
| --- | --- | --- | --- | --- |
| Business / Domain | Core business concept, rule, invariant, lifecycle, permission, event, or policy | Domain module, application service, use case, policy, state machine | Use business vocabulary from requirements and existing domain model | It is only formatting, parsing, transport, or persistence mechanics |
| Feature | User-visible capability or product workflow slice | Feature module, route/page area, feature-local component/state/tests | Name after the user outcome or workflow, not implementation mechanics | It is reused by unrelated features or has no product behavior |
| Component | UI composition unit with props, slots, state, render behavior, accessibility contract | Feature-local UI folder or design-system/component package | Name by rendered role and product meaning | It contains data access, business rules, or global state ownership |
| Module | Coherent code boundary with owner, public API, allowed dependencies | Module/package directory | Name after owned capability or technical layer | It is just a folder for convenience |
| Service | Application orchestration, use case coordination, transaction boundary, external operation boundary | Application/backend service layer | Name after use case or owned operation | It only wraps one repository call or hides procedural helpers |
| Domain Object / Value Object | Object with identity or value semantics, invariants, lifecycle, or behavior | Domain model | Name after the concept it protects | It is a DTO, record, or getter/setter bag |
| Repository | Persistence boundary and query/write contract | Infrastructure or data access layer behind an interface | Name after aggregate/resource being persisted | It leaks ORM/persistence types into domain logic |
| Adapter / Client | External system, framework, transport, provider, or infrastructure boundary | Infrastructure/integration/adapter directory | Name after external system and role | It contains business rules instead of translation, retry, or failure handling |
| Utility | Pure technical, domain-free helper reused across modules | Shared/common utility package | Name by technical transformation; no business terms | It contains order, tenant, invoice, permission, workflow, or other domain terms |
| Helper | Small local implementation detail private to a file/module | Same file or module-internal area | Prefer private/local names and keep scope narrow | It becomes public, reused widely, or hides a missing domain/service concept |
| Common / Shared | Stable cross-module technical contract or primitive | Shared/common package with clear ownership | Use only for domain-free primitives or intentional public contracts | It is used to avoid choosing the owning module |

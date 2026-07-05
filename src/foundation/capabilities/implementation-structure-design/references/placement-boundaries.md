# Placement Boundaries — Full Decision Trees

Deep reference for the `## Placement Boundaries` rules in `implementation-structure-design`.
The capability body carries the decision-critical summary; this file carries the full file
and directory decision trees and the frontend/backend placement rationale. It is loaded in
the `dev` profile and by skill authors.

## File Decision Tree

```text
Need a new file?
|-- Does an existing file already own this responsibility?
|   |-- Yes: Add there unless it would exceed cohesion or readability threshold.
|   `-- No
|-- Is the new logic a private helper for one feature or module?
|   |-- Yes: Add under the module internal or private area.
|   `-- No
|-- Is it a public module contract?
|   |-- Yes: Put under module api, public, or export surface.
|   `-- No
|-- Is it an adapter to external infrastructure?
|   |-- Yes: Put under adapter, infrastructure, or integration area.
|   `-- No
|-- Is it pure shared technical utility?
|   |-- Yes: Put under shared or common only if no business terminology appears.
|   `-- No: Keep in the owning business module.
```

## Directory Decision Tree

```text
Need a new directory?
|-- Does it represent a business capability or bounded context?
|   |-- Yes: Create module or capability directory with owner and public API.
|   `-- No
|-- Does it represent a layer inside an existing module?
|   |-- Yes: Follow existing layer convention.
|   `-- No
|-- Does it represent an external adapter or generated-code boundary?
|   |-- Yes: Create with source-of-truth and regeneration policy.
|   `-- No: Reject directory. Use existing structure.
```

## Frontend And Backend Placement

Frontend placement must decide feature-local versus shared for components, hooks, validators, state, API clients, and route code. Avoid turning `components/common`, `hooks`, or `utils` into dumping grounds. Feature-local state must not move to a global store without actual cross-feature ownership.

Backend placement must decide controller, service, domain, repository, adapter, validator, mapper, DTO, and job ownership. Business rules do not belong in transport handlers, generic utilities, or persistence adapters.

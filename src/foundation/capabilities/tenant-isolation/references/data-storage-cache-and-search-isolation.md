# Tenant Data, Storage, Cache, And Search Isolation

**Load when:** Tenant isolation changes in database keys, queries, object paths, caches, search indexes, derived views, or storage topology.

**Do not load when:** No stored, cached, object, or indexed tenant boundary changes and current negative tests prove every affected surface.

**Required by:** `analysis-agent`, `task-agent`, `review-agent`

**Required output:** `boundary-decision`, `validation-plan`, `residual-risk`

## One Decision

Select one isolation contract for each data surface and prove that tenant scope survives the read, write, derivation, and cache path set.

## Decision Matrix

| Surface | Required isolation decision | Failure signal |
|---|---|---|
| Tenant authority | Trusted internal identifier, provenance, mismatch outcome, and refresh point | Caller data selects authoritative tenant scope |
| Relational data | Tenant-scoped primary, unique, and foreign keys; read/write predicates; database policy; privileged bypass | A globally unique ID permits a cross-tenant association |
| Partitioned data | Partition-key authority, routing map, transaction scope, and cross-partition behavior | Untrusted tenant input routes directly to another partition |
| Object storage | Account/container/bucket/path model, metadata, delegated URL scope, listing, copy, and delete | Prefix filtering occurs after listing or URL issuance |
| Cache | Tenant, permission/freshness variant, schema version, invalidation, local cache, and fallback | Shared key or fallback returns another tenant's value |
| Search index | Tenant field or index, ingest binding, query filter, counts/facets, writes, aliases, and rebuild | Post-query filtering hides hits but leaks aggregates |
| Derived surface | Source tenant, transformation, destination identity, correction, deletion, and rebuild | A projection drops tenant identity or joins tenants |

## Verification

- Exercise same identifier under two tenants for create, read, update, delete, list, aggregate, and relationship paths.
- Inspect generated SQL or query plans and database policies under normal and privileged roles.
- Compare cache keys and invalidation for two tenants with identical object identifiers.
- Exercise object listing, copy, signed access, search hits, counts, facets, aliases, and rebuilds with forged scope.
- Verify isolated and shared resource variants separately.

## Primary Sources

- [PostgreSQL row security policies](https://www.postgresql.org/docs/current/ddl-rowsecurity.html)
- [Azure storage and data approaches for multitenant solutions](https://learn.microsoft.com/en-us/azure/architecture/guide/multitenant/approaches/storage-data)
- [Azure compute approaches for multitenant solutions](https://learn.microsoft.com/en-us/azure/architecture/guide/multitenant/approaches/compute)
- [Elastic document and field level access control](https://www.elastic.co/docs/deploy-manage/users-roles/cluster-or-deployment-auth/controlling-access-at-document-field-level)

Official project and platform pages were accessed on 2026-07-26.

## Proof Limits

Vendor mechanisms differ by version, configuration, privilege, API, and operation. Row or document policies do not prove write, owner, superuser, aggregate, alias, cache, backup, or application paths unless those paths are separately exercised.

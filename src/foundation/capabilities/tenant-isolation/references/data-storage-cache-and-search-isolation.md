# Tenant Data, Storage, Cache, And Search Isolation

**Load when:** Database keys, queries, objects, caches, indexes, views, or storage topology change tenant isolation.

**Do not load when:** No stored, cached, object, or indexed boundary changes and current negative evidence covers affected surfaces.

**Required by:** `analysis-agent`, `task-agent`, `review-agent`

**Required output:** `boundary-decision`, `validation-plan`, `residual-risk`

## One Decision

Select isolation contracts for active data surfaces and prove tenant scope across reads, writes, derivation, and caches.

## Decision Matrix

| Surface | Required decision | Failure signal |
|---|---|---|
| Authority | Trusted tenant identifier, provenance, mismatch, refresh | Caller data selects scope |
| Relational | Tenant keys, predicates, policy, privileged bypass | Global ID crosses tenants |
| Partition | Key authority, routing, transaction, cross-partition behavior | Untrusted input routes partitions |
| Object | Container/path, metadata, delegated URL, list/copy/delete | Filtering follows listing or URL issue |
| Cache | Tenant and permission/freshness/schema key, invalidation, fallback | Shared key or fallback leaks |
| Search | Tenant ingest/query, counts/facets, writes, aliases, rebuild | Post-filtering leaks aggregates |
| Derived | Source tenant, transform, destination, correction, deletion, rebuild | Projection drops or joins tenant identity |

## Verification

- Exercise same-tenant, wrong-tenant, forged, stale, privileged, and missing tenant context.
- Use identical local IDs, object names, cache keys, and search terms across tenants.
- Test list, count, facet, join, copy, delete, restore, reindex, rebuild, and cache fallback.
- Inspect generated queries, policies, partition keys, object grants, cache keys, and search filters.

## Primary Sources

- [AWS SaaS tenant isolation strategies](https://docs.aws.amazon.com/whitepapers/latest/saas-tenant-isolation-strategies/saas-tenant-isolation-strategies.html)
- [Azure multitenant storage and data approaches](https://learn.microsoft.com/en-us/azure/architecture/guide/multitenant/approaches/storage-data)
- [PostgreSQL row security policies](https://www.postgresql.org/docs/current/ddl-rowsecurity.html)
- [Azure AI Search security filters](https://learn.microsoft.com/en-us/azure/search/search-security-trimming-for-azure-search)

Official platform pages were accessed on 2026-07-26.

## Proof Limits

Local tests and query inspection do not prove deployed policy activation, provider control-plane isolation, external copies, all replicas, or production restore isolation. Record those as residual risk with an owner.

## Failure Evidence

- Tenant filtering occurs after read, list, count, or facet computation.
- Cache, object, or search scope can be selected from caller-controlled identity.
- Privileged paths bypass tenant predicates without explicit scope and audit.

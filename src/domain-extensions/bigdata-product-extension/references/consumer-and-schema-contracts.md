# Consumer and Schema Contracts

Use this Reference only for the named BigData consumer-and-schema-contracts decision.

## Decision Rules

- **Prove consumer compatibility**: verify that active consumers in the current source-backed inventory can read the deployed schema transition, with inventory gaps recorded as a blocking proof limit.
- Identify authoritative source systems, sinks, owners, freshness contracts, classified fields, and downstream consumers for affected assets.
- Make metric meaning explicit: grain, dimensions, filters, time-zone and calendar rules, aggregation, correction, and consumer-visible null or default behavior.
- Separate structural compatibility from semantic consumer compatibility. Treat changes to grain, meaning, units, defaults, ordering, or correction as contract changes, and cover active readers plus replay within the compatibility window.

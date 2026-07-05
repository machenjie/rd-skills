# Big Data Product Extension Checklist

- Source systems, sinks, owners, freshness targets, and downstream consumers are identified.
- Metric definitions, grain, dimensions, filters, time zones, and aggregation rules are explicit.
- Schema evolution covers nullable fields, renames, type changes, deleted fields, and compatibility windows.
- Pipeline mode defines batch, stream, incremental, full refresh, and hybrid behavior.
- Idempotency, deduplication keys, ordering, watermarking, late data, and replay semantics are defined.
- Backfill plan is bounded, repeatable, observable, interruptible, and validated against sample totals.
- Quality checks cover completeness, uniqueness, validity, referential integrity, distribution shifts, and row counts.
- Lineage records upstream source, transformations, storage tables, dashboards, and API consumers.
- Cost controls cover partitions, clustering, indexes, query limits, retention, and compute budget.
- Monitoring covers freshness, lag, volume anomalies, failed tasks, bad records, cost spikes, and data quality failures.

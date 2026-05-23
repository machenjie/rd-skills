---
name: bigdata-product-extension
description: Adds professional product rules for data warehouse, stream and batch jobs, analytics, reporting, ETL and ELT, data quality, lineage, backfill, replay, freshness, and cost-sensitive data changes.
license: MIT
changeforge_kind: domain-extension
changeforge_version: 0.1.0
---

## Mission
Extend ChangeForge product and code change analysis with big data engineering discipline for distributed processing correctness, pipeline reliability, schema evolution safety, query performance integrity, data quality assurance, and cost governance — ensuring data products are accurate, observable, scalable, and compliant with data residency and privacy obligations.

## Trigger Signals
- Any change to data pipeline code: ingestion, transformation, aggregation, enrichment, loading.
- Apache Spark, Flink, Beam, Databricks, dbt, or other distributed processing job changes.
- Kafka producer or consumer configuration changes; topic creation, partition configuration, schema evolution.
- Data warehouse or data lake changes: partition strategy, table format (Parquet, ORC, Delta Lake, Iceberg), ZORDER, file compaction.
- Schema changes in data models that will be consumed by downstream jobs, BI tools, or ML pipelines.
- New or modified dbt models, Great Expectations checks, or data quality validation rules.
- Changes to data catalog entries (Apache Atlas, OpenMetadata, DataHub) or data lineage registrations.
- GDPR right-to-be-forgotten implementation in distributed storage systems.
- Cost-sensitive pipeline changes: increased scan volume, new external tables, materialized view additions.
- Product analytics and experimentation changes: event taxonomy, funnel/cohort definitions, exposure logging, dashboards, north-star metrics, guardrail metrics, or A/B test data.
- Classical ML and MLOps changes involving feature stores, training pipelines, model registry inputs, drift metrics, shadow/canary data, or online/offline metric alignment.
- Changes to streaming-to-batch or batch-to-streaming architecture (Lambda/Kappa architecture selection).

## Do Not Use When
- The change is a standard relational OLTP database query optimization with no distributed processing involvement.
- The change is a simple ETL script with no distributed execution, no schema versioning, and no downstream dependencies.

## Non-Negotiable Rules
- **Schema changes must be backward-compatible with all registered consumers before deployment**: deploying a schema change that breaks an active downstream consumer causes silent data loss or pipeline failures — use Avro/Protobuf/JSON Schema with compatibility mode enforcement (`BACKWARD`, `FORWARD`, or `FULL`).
- **Partition strategy must align with the query access pattern, not just data volume**: a partition on `created_at` is efficient for time-range queries but catastrophically expensive for point lookups by `user_id` — design partitions for the dominant query pattern.
- **Idempotency is required for all pipeline re-runs**: every pipeline stage must be re-runnable without producing duplicate records — use INSERT OVERWRITE or MERGE patterns, not INSERT APPEND for re-runs.
- **Data quality checks must gate data promotion to production tables**: raw data ingested without quality checks promoted to production tables corrupts downstream analytics and ML features.
- **PII must be identified, inventoried, and handled per data classification policy before the pipeline ships**: data that flows through a pipeline without PII classification cannot satisfy GDPR Article 17 right-to-erasure or HIPAA minimum necessary standard.
- **Shuffle operations must be bounded**: Spark jobs that trigger an unbounded shuffle (repartition without target partition count, large join without broadcast hint for small tables) will cause memory pressure and task failure on large datasets.
- **Data lineage must be registered for any new data asset used by downstream consumers**: an undocumented data asset has no impact analysis path — downstream consumers are invisible.
- **Cost of new queries and scans must be estimated before deployment**: a full table scan on a petabyte-scale data lake costs real money and may violate budget constraints — use EXPLAIN or dry-run query cost estimation before enabling.
- **Experiment exposure and assignment events must be data-quality gated**: A/B results are invalid if exposure logging is missing, assignment units are unstable, sample ratio mismatch is unchecked, or event taxonomy changes are not backward-compatible.
- **Feature store data must be point-in-time correct**: training data must not include future information, labels must not leak into features, and online serving features must match offline training semantics.

## Industry Benchmarks
- **Lambda Architecture (Nathan Marz)**: Batch layer + speed layer + serving layer. Provides both accurate (batch) and low-latency (speed) views. Operational complexity is high; Kappa is preferred when a unified stream can serve both needs.
- **Kappa Architecture (Jay Kreps, Confluent)**: Single streaming pipeline serving all views; batch is replay of the stream. Preferred when stream processing latency meets SLA requirements for historical recomputation.
- **Apache Kafka Design (Confluent documentation)**: Partition count, replication factor, retention policy, consumer group lag, exactly-once semantics (EOS), consumer offset management, topic compaction. Replication factor ≥ 3 for production topics.
- **Apache Spark Optimization Guide**: Partition count = 2–4× cluster cores; avoid shuffles larger than memory; use broadcast join for tables < 200MB; cache only DataFrames that are reused; use Adaptive Query Execution (AQE) for dynamic partition coalescing.
- **dbt Data Transformation Practices**: Models structured in staging → intermediate → marts layers; tests at every model (not_null, unique, referential integrity, custom assertions); materializations chosen for access pattern (view for rarely accessed, table for frequently accessed, incremental for appending).
- **Great Expectations / dbt Tests**: Data quality validation as code — expectations are versioned, testable, and CI-gated. Run data quality checks before data promotion, not after incident discovery.
- **Apache Iceberg / Delta Lake / Apache Hudi**: ACID transactions on data lake tables; time-travel for audit and rollback; schema evolution with compatibility enforcement; hidden partitioning for query optimization. Iceberg is the emerging open standard for lakehouse tables.
- **GDPR Right to Erasure in Distributed Systems**: Deletion is not a row DELETE in distributed storage — it requires a documented erasure strategy: pseudonymization, crypto-shredding (delete the encryption key to render data unreadable), or physical deletion with tombstoning. Choose the strategy before data ingestion.

### Processing Model Selection Matrix

| Requirement | Recommended Architecture | Why |
|---|---|---|
| Near real-time alerts (< 5s latency) | Kappa (Kafka Streams / Flink) | Stream-first; batch replay via topic retention |
| Daily analytical aggregations, large historical recompute | Lambda or dbt batch | Batch is cheaper and simpler for non-latency-sensitive aggregation |
| Mutable rows with ACID updates (late-arriving corrections) | Delta Lake / Iceberg with MERGE | ACID transactions on lakehouse; time-travel for audit |
| ML feature store with point-in-time correctness | Tecton / Feast with Iceberg | Feature backfilling and historical training without future leakage |
| GDPR right-to-erasure on distributed storage | Crypto-shredding on PII fields | Deletion without full re-write of partitioned data |

## Domain Risk Model
- **Silent data loss from schema mismatch**: a new Avro schema removes a field that downstream consumers use — consumers receive `null` silently; data silently corrupted for all records written after schema change.
- **Partition skew causes long-tail job failures**: one partition contains 80% of the data (hot key problem) — the task processing that partition runs 50× longer than average; job appears stuck; eventually OOM fails.
- **Data duplication from non-idempotent re-run**: a pipeline is re-run after a failure — it appends data to the output table instead of overwriting the affected partition — all downstream metrics are doubled.
- **Data quality failure not caught until BI report**: NULL injection or type coercion error in a transformation produces invalid metric values in production data — discovered 3 days later when a business report shows impossible values.
- **PII flows into logging or monitoring**: a data enrichment pipeline includes raw email addresses in Spark task logs — PII is exported to the log analytics platform without consent or retention controls.
- **GDPR erasure request fails on distributed storage**: a user requests deletion; the application deletes the OLTP record; the data warehouse ETL has already loaded the data into a Parquet partition that is append-only — the data survives for months.
- **Full table scan cost explosion**: a new analytical query is deployed without a partition filter — it scans 50TB on every execution; the query costs $2000/run in BigQuery/Snowflake scan fees.
- **Consumer group lag accumulates silently**: a Kafka consumer falls behind during a traffic spike; no lag alert is configured; 6 hours of events are buffered in Kafka; when the consumer catches up, it floods downstream systems.
- **Experiment conclusion is invalid**: exposure events are logged only on click instead of view; control and treatment allocation diverges; dashboard shows a lift that is actually sample ratio mismatch.
- **Training-serving skew degrades model**: offline features use corrected late-arriving data while online serving uses defaults; offline metrics look strong but online conversion drops.
- **Label leakage inflates offline metrics**: training data includes a post-outcome feature; validation AUC is high, but production model fails.

## Analytics And Experimentation Data Controls

Apply these controls when product analytics or experiments are part of the change:

- Event taxonomy: event names, schema versions, required fields, compatibility, and deprecation plan.
- Funnel and cohort definitions: inclusion/exclusion rules, time windows, identity stitching, and backfill approach.
- North-star metric: metric owner, definition, source table, freshness, and dashboard.
- Guardrail metrics: reliability, revenue, retention, support, safety, accessibility, and data quality thresholds.
- Exposure logging: event timing, de-duplication, assignment unit, experiment id, variant id, and eligibility.
- Sample ratio mismatch: threshold, query, alert owner, and decision rule.
- Experiment conflict: mutually exclusive experiments, overlapping cohorts, priority, and analysis exclusion.
- Decision memo: launch/rollback decision, metric readout, guardrail status, caveats, and owner.

## MLOps Data Governance

Apply these controls when data pipelines feed model training or serving:

- Feature store point-in-time correctness with event-time joins and late-data handling.
- Label leakage checks that prove labels or post-outcome fields cannot enter features.
- Training-serving skew comparison for feature defaults, transformations, null handling, and freshness.
- Model registry metadata: model version, training dataset version, feature set version, owner, and approval.
- Drift signals: data drift, model drift, concept drift, and online/offline metric mismatch thresholds.
- Shadow/canary data capture with no user-impacting side effects.
- Rollback model data path: previous model version, compatible feature set, and data validation before rollback.
- Fairness/bias audit dataset slices and acceptance thresholds.

## Linked Foundation Capabilities
- data-model-design
- api-contract-design
- test-strategy
- regression-testing
- observability
- logging-error-handling
- backup-recovery
- performance-budgeting
- profiling
- concurrency-control

## Linked Professional Skills
- data-api-contract-changer
- data-middleware-change-builder
- quality-test-gate
- reliability-observability-gate
- security-privacy-gate
- change-documentation-gate

## Critical Details
- **Spark partition count guideline**: target 128MB–256MB per partition for read-heavy operations; 64MB for shuffle-heavy operations. Too few partitions under-utilizes the cluster; too many creates excessive task scheduling overhead.
- **AQE (Adaptive Query Execution) does not eliminate partitioning design requirements**: AQE dynamically coalesces small shuffle partitions but cannot fix a fundamentally skewed join on a high-cardinality key — design the data model first, rely on AQE for execution efficiency.
- **Kafka EOS (Exactly-Once Semantics) requirements**: EOS requires `enable.idempotence=true`, `acks=all`, `max.in.flight.requests.per.connection=5`, and transactional producer configuration — missing any one setting silently degrades to at-least-once semantics.
- **Delta Lake / Iceberg VACUUM caution**: running VACUUM with a retention period shorter than the longest active read transaction will delete files that open readers still reference — readers fail with FileNotFoundException after VACUUM.
- **Data lineage gaps break GDPR erasure**: if a pipeline stage is not registered in the data catalog, it is invisible to the erasure process — GDPR right-to-be-forgotten compliance cannot be verified.
- **Re-indexing Elasticsearch from a data lake**: re-indexing is a full-table read; it competes with production analytical workloads for I/O; schedule during off-peak with explicit resource isolation.
- **Storage lifecycle is a cost control**: raw, staging, feature, mart, and dashboard tables need retention and tiering rules. Unbounded warehouse tables, orphaned materializations, and abandoned experiment tables become recurring cost.
- **Egress is often hidden in data products**: cross-region feature serving, BI extracts, reverse ETL, and model training exports can dominate cost even when compute looks healthy.

### Anti-Examples

| Big Data Pattern | Problem | Corrected Approach |
|---|---|---|
| `df.repartition(1).write.parquet(output)` | Single-partition write creates a bottleneck and 1 huge file | `df.repartition(200, "partition_col").write.parquet(output)` |
| Schema removed a non-nullable field; old consumers not updated | Consumers fail with deserialize error | Use schema registry with BACKWARD compatibility check before schema publish |
| Pipeline INSERT APPEND on re-run | Re-run creates duplicate records | Use INSERT OVERWRITE partition or MERGE INTO for idempotency |
| `SELECT * FROM events` without partition filter | Full table scan on PB-scale table | `SELECT * FROM events WHERE dt >= '2025-01-01'` with partition pruning |
| No data quality tests on raw source data | Bad data silently propagates to production tables | Great Expectations suite runs after ingestion; gates promotion on failure |

## Failure Modes
- **Hot partition OOM**: a Spark job joins on a user_id with extreme skew — one task processes 90% of the data, runs out of memory, and the job fails after 4 hours of processing.
- **Exactly-once semantics silently degraded**: Kafka producer configuration is incomplete — messages are delivered at-least-once; consumers see duplicate events; financial aggregations are inflated.
- **Schema evolution breaks downstream ML pipeline**: a feature column is renamed in the feature store schema without updating the ML training pipeline — training silently uses `null` for all new records; model degrades.
- **GDPR erasure incomplete in data warehouse**: user deletion is processed in OLTP; the ETL has already written the data to a Parquet partition — the data persists for the partition retention period (months to years).
- **Kafka consumer lag undetected**: a consumer group accumulates 10M records of lag; no alert is configured; the "real-time" dashboard has been 6 hours stale for days.
- **Cost alarm triggers on production launch**: a new analytical query deployed without cost estimation runs full table scans 500 times per day; the BigQuery bill exceeds the monthly budget in the first 3 days.

## Output Contract
Return big data change assessment with:
- **Schema evolution safety**: backward compatibility analysis, schema registry constraint verification, consumer impact assessment.
- **Partition strategy review**: alignment with query access pattern, skew risk, cost implications.
- **Pipeline idempotency audit**: re-run safety for every pipeline stage.
- **Data quality gate requirements**: required data quality checks, thresholds, and promotion gating.
- **PII inventory and erasure strategy**: PII fields identified, classification applied, erasure mechanism defined.
- **Cost estimate**: query scan volume, compute estimate, cost per run and per day.
- **Cost guardrails**: query scan budget, cost per pipeline/job, storage lifecycle cost, egress cost, budget owner, and cost anomaly alert.
- **Experiment data contract**: event taxonomy, exposure event, assignment unit, primary/north-star metric, guardrail metrics, SRM check, dashboard migration, and decision memo owner.
- **MLOps governance**: `model_version`, `feature_store`, point-in-time correctness, label leakage controls, training-serving skew check, `drift_metric`, offline/online metric alignment, fairness/bias audit, and `rollback_model`.
- **Observability plan**: consumer lag metric, data freshness metric, data quality pass rate, pipeline duration, cost metric.
- **Lineage registration requirements**: data assets to register before deployment.
- **Block/pass decision** with required conditions for approval.

## Quality Gate
1. Schema changes are registered in schema registry with BACKWARD or FULL compatibility enforcement.
2. All downstream consumers of a changed schema are identified and validated.
3. All pipeline stages are idempotent — re-run test passed on staging data.
4. Data quality checks are configured with defined thresholds; promotion to production tables is gated on check pass.
5. PII fields are identified, classified, and have a documented erasure strategy.
6. Partition strategy is aligned with the dominant query access pattern; skew risk is assessed.
7. Full table scans are eliminated (partition filter required) or cost-estimated and budget-approved.
8. Kafka topics have replication factor ≥ 3, consumer group lag alerting, and DLQ routing for processing failures.
9. Data lineage is registered for all new data assets consumed by downstream consumers.
10. Consumer group lag alerting is configured with a defined SLA for data freshness.
11. Experiment analytics define taxonomy, exposure event, assignment unit, primary/guardrail metrics, SRM check, dashboard migration, and decision memo owner.
12. ML data paths prove feature store point-in-time correctness, no label leakage, training-serving skew checks, drift metrics, and rollback model compatibility.
13. Storage lifecycle, egress, and cost anomaly detection are defined for cost-sensitive data assets.

## Handoff
- **data-middleware-change-builder** — for Kafka topic configuration, Spark job optimization, and database query performance.
- **data-api-contract-changer** — for schema evolution coordination with API consumers and schema registry.
- **security-privacy-gate** — for PII classification, erasure strategy, and data residency compliance.
- **reliability-observability-gate** — for pipeline SLI, data freshness SLO, consumer lag alerting, and cost monitoring.
- **quality-test-gate** — for data quality test requirements, pipeline integration tests, and idempotency tests.
- **experience-impact-modeler** — for user-facing experiment flows, exposure semantics, and analytics event compatibility.
- **acceptance-criteria-builder** — for primary metric, guardrail, exposure event, and experiment rejection criteria.

## Completion Criteria
The big data change is approved when schema evolution is backward-compatible with all consumers, pipeline stages are idempotent, data quality gates are configured and threshold-tested, PII is classified and has an erasure strategy, partition strategy aligns with query access patterns, full table scans are eliminated or cost-approved, analytics and experiment metrics are contract-safe, ML feature/model data paths are governed when present, Kafka topics have lag alerting and DLQ routing, and data lineage is registered for all new assets.

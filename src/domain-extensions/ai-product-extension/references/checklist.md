# AI Product Extension Checklist

- Define user-facing evidence authority across source evidence, model inference, uncertainty, abstention, independent verification, and human review. The contract covers unavailable evidence, fallback, appeal, correction, and explicit degraded decisions.
- Govern retrieval data and indexes by source permission, tenant, retention, redaction, deletion, ownership, version, namespace, refresh, and freshness. Verify revocation across active and fallback serving indexes, with a bounded lag.
- Separate trusted policy, user input, retrieved content, tool output, stored memory, and generated output. Exercise direct and indirect injection and poisoned tool results against instruction priority, data access, and future decisions.
- Bind tool calls to identity, principal, argument schema, data scope, side-effect class, confirmation, retry, recovery, and audit evidence. Approved authority excludes excess model fields and call sequences.
- Authorize durable memory reads and writes as product effects. Bind provenance, principal, tenant, purpose, policy version, trust, deletion, and revocation while preventing cross-actor poisoning or retrieval.
- Record evaluation-set source, owner, collection window, labels, transformations, version, and intended population. Detect overlap with training, tuning, retrieval, prompt development, and prior evaluation outputs before claiming independent evidence.
- Record judge identity or assignment, model version, rubric, calibration, scoring direction, disagreement, overrides, and adjudication. Independent or blinded review applies when variance or automation bias can change consequential decisions.
- Compare baseline and treatment across representative success, boundary, refusal, hallucination-prone, adversarial, and regression cases by consequential cohort.
- Derive evaluation thresholds and sample effort from harm, prevalence, and observed variance.
- Record deployable lineage for applicable behavior-bearing prompts, models, providers, retrievers, embeddings, indexes, tool schemas, safety policies, data snapshots, and evaluators.
- Bind prompt and response cache identity to principal, tenant, visibility, and behavior-bearing versions. Invalidate affected cache entries and proof when those inputs change.
- Exercise reachable timeout, rate-limit, retrieval, tool, refusal, unsafe-output, truncation, and configured fallback failures. Verify compatible refusal, structured output, tool authority, required evidence, and safety behavior.
- Treat model output as untrusted at parsing, rendering, storage, query, API, policy, and authorization boundaries. Validate structure and business authority independently of model confidence.
- Segment quality, retrieval, tool, refusal, latency, cost, drift, and safety signals by deployable lineage and consequential cohort. Bound labels and sensitive payloads, with named alert ownership.
- Map provider-bound and retained AI data across providers, logs, traces, caches, evaluation stores, and human-review queues. Applicable consent, purpose, region, fallback, residency, retention, deletion, and access rules govern each copy.

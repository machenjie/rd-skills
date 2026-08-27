# Rendered Context Budget Evaluation

Status: **pass**

Evidence scope: **deterministic-rendered-artifacts**

Compiled Layer 3 format: **ai-consumption-v1**

Tokenizer: **o200k_base**

Fixtures: **16**; dispatches: **40**; host/profile measurements: **360**.
Explicit nested Layer 3 Reference loads: **8**; logical IDs: **ai-product-extension/references/checklist.md, module-boundary-design/references/benchmarks-and-enforcement.md, payment-trading-extension/references/duplicate-financial-effect-control.md, release-rollback/references/benchmarks-and-patterns.md, release-rollback/references/evidence-patterns.md, test-strategy/references/checklist.md, transaction-consistency/references/evidence-patterns.md, web-security/references/checklist.md**.
Measured nested Reference components across host/profile combinations: **72**.

Fixture Capsule contract: **changeforge.fixture-capsule.v2**. Its hash detects drift, its typed semantic gate rejects synchronized placeholder/low-diversity forgeries, and its deterministic renderer is evaluator-only and excluded from build/install artifacts.

The Control Prompt is embedded in each rendered Main Profile and is not added a second time.

## Authoritative Limits and Observed Maxima

Soft targets and hard ceilings come only from the Core Model and are provisional migration values, not calibrated optima. Soft overage is an advisory; hard overage fails Conformance without truncating required context.

Mode: **conformance**.

| Context | Soft target | Hard ceiling | Observed maximum | Soft margin | Hard margin | Soft status | Hard status |
| --- | ---: | ---: | ---: | ---: | ---: | --- | --- |
| Main always-loaded | 2305 | 2650 | 2177 | 128 | 473 | within | within |
| Direct Task dispatch | 3000 | 3200 | 2025 | 975 | 1175 | within | within |
| Analyzed Task dispatch | 6000 | 6500 | 3750 | 2250 | 2750 | within | within |
| Analysis dispatch | 4500 | 5000 | 2400 | 2100 | 2600 | within | within |
| Review dispatch | 3700 | 4000 | 2216 | 1484 | 1784 | within | within |
| Utility dispatch | 2000 | 2500 | 828 | 1172 | 1672 | within | within |

## Calibration Distribution

Calibration candidate selection and frontier construction do not apply soft targets or hard ceilings. Percentiles use nearest rank.

| Context | Count | P50 | P90 | P95 | P99 | Max | Growth distribution |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| Main always-loaded | 9 | 2170 | 2177 | 2177 | 2177 | 2177 | unavailable |
| Direct Task dispatch | 19281 | 2187 | 2641 | 2704 | 2816 | 2934 | unavailable |
| Analyzed Task dispatch | 66150 | 2685 | 3196 | 3351 | 3566 | 4019 | unavailable |
| Analysis dispatch | 112828 | 1790 | 2126 | 2310 | 2658 | 3445 | unavailable |
| Review dispatch | 38009 | 2364 | 2811 | 3003 | 3174 | 3363 | unavailable |
| Utility dispatch | 18 | 806 | 828 | 828 | 828 | 828 | unavailable |

Valid-candidate selection identity: `6b5ba791f34462249547d7134de05926c78a6ec86469a3428356d2c5920b193d`. Temporal growth is unavailable because this run has one comparable snapshot.

## Admissible Context Composition Gate

Contract: **changeforge.admissible-context-composition-eval/v1**; selector owner surfaces: **65**; canonical legal selection equivalence classes: **14051**; exact measurements: **6**.

| Context | Soft target | Hard ceiling | Reachable maximum | Professional | Layer 3 | Owner | Build | Host |
| --- | ---: | ---: | ---: | --- | --- | --- | --- | --- |
| task | 3000 | 3200 | 2934 | change-documentation-gate | documentation-generation | main-control-agent | dev | copilot |
| analyzed_task | 6000 | 6500 | 4019 | backend-change-builder | failure-diagnosis, filesystem-process-safety, nodejs-runtime-professional-usage | engineering-brief | dev | copilot |
| analysis | 4500 | 5000 | 3445 | engineering-change-analysis | iot-embedded-extension, failure-diagnosis, package-dependency-management | main-control-agent | dev | claude |
| review | 3700 | 4000 | 3363 | ai-code-review-refactor | domain-object-identification, implementation-structure-design, refactoring | engineering-brief | dev | copilot |

### Dominance Frontier Projection

| Context | Canonical candidates | Exact render signatures | Over target |
| --- | ---: | ---: | ---: |
| task | 19281 | 19281 | 0 |
| analyzed_task | 66150 | 66150 | 0 |
| analysis | 112828 | 46158 | 0 |
| review | 38009 | 16641 | 0 |

Global Task/Review frontier counts: professional=0, layer3=0, active_reference=0; safe complement: professional=17, layer3=68, active_reference=267.

Mapping digest: `e0f64819d75f714f76df8f56e8b3a3a017d8190a00cf951a03dec84f6c3b4192`; runtime consumers: **0**; build consumers: **0**.

Coverage: analysis_foundation_domain=yes, analyzed_task_three_layer3=yes, review_domain_foundation=yes, nested_targeted_references=yes, direct_main_owner=yes, initial_analysis_main_owner=yes, analyzed_brief_owner=yes, direct_false_worst_excluded=yes.

Forbidden-combination evidence: >3 rejected=47; unauthorized exact rejected=65; duplicate exact rejected=63; silent truncations=0; nearest-negative leaks=0.

### Composition Proof Limits

- Selector equivalence classes use declarative positive and nearest-negative signals; the evaluator does not classify task prose.
- Reference subset coverage is a conservative role-compatible upper envelope; registry indexes and catalogs are forbidden and mode contracts remain isolated.
- Capsule contribution uses the largest validated checked-in fixture Capsule per budget class, not arbitrary future user prose.
- Every legal render candidate maps to one source-derived reduction stratum; exact tokenization is memoized by ordered component fingerprint and applied to the highest component-token representative of every stratum.
- Sequenced Reference stages are source-owned; only canonically replayed engineering-brief Task/Review carriers may replace a predecessor body, while other owner surfaces conservatively co-load.
- Reported maxima are exact for the deterministic canonical representatives; the full inventory count and dominance mapping remain available separately.

Maximum exact normalized duplicate-rule ratio: **0.003737** (gate: **0.03**; margin: **0.026263**).

Discovery metadata is reported separately because actual host discovery injection is not observed.

## Transferred Context Measurement

Gross exclusive transferred-context tokens: **14640**; non-compressible: **14640**; compressible: **0**; ratio: **0.0**.

Long tasks joined from lightweight required progress: **9**. Candidate-only transfer measurements carry no baseline claim.

Overlap views (Evidence Ledger, Diff, Validation, duplicate context, and superseded evidence) are reported outside the gross denominator.

### Transfer Proof Limits

- Transferred-context counts are deterministic projections from checked-in trace fields, canonical Capsules, and current handoff contracts; they are not host-observed requests or model responses.
- Skill / Reference counts cover only selectors crossing the dispatch boundary; full loaded Skill content remains measured by the existing rendered instruction contexts.
- Execution Delta, review input, and repair input are bounded field projections; the fixtures do not store full natural-language handoff bodies.
- Diff counts cover actual-diff metadata or an accessible fixture reference, not diff contents; validation is structured and excludes full command logs, which remain JIT-only.
- Duplicate context detects exact normalized blocks in the projected transfers, not semantic paraphrases.
- Current-evidence selection uses explicit fixture ordering and freshness; it does not infer unstated runtime evidence.

## Limitations

- Counts cover deterministic rendered rd-skills instructions and canonical Capsules rendered from versioned checked-in fixture data, not a host-observed model request.
- Counts exclude host system prompts, tool schemas, user conversation history, repository reads, diffs, command output, and other dynamic evidence.
- Host loaders may transform Profile or Skill files and may expose discovery metadata differently; this report does not prove real-host accuracy.
- Token counts do not prove wall-clock performance, production accuracy, Profile startup, or the installed user experience.
- Duplicate-token measurement detects exact normalized Markdown rule blocks, not semantic paraphrases.
- Nested Layer 3 Reference counts include only explicitly named fixture files; directories, indexes, catalogs, and recursively linked files are never loaded.

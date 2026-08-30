# Rendered Context Budget Evaluation

Status: **pass**

Evidence scope: **deterministic-rendered-artifacts**

Compiled Layer 3 format: **ai-consumption-v1**

Tokenizer: **o200k_base**

Fixtures: **16**; dispatches: **40**; host/profile measurements: **120**.
Explicit nested Layer 3 Reference loads: **8**; logical IDs: **ai-product-extension/references/checklist.md, module-boundary-design/references/benchmarks-and-enforcement.md, payment-trading-extension/references/duplicate-financial-effect-control.md, release-rollback/references/benchmarks-and-patterns.md, release-rollback/references/evidence-patterns.md, test-strategy/references/checklist.md, transaction-consistency/references/evidence-patterns.md, web-security/references/checklist.md**.
Measured nested Reference components across host/profile combinations: **24**.

Fixture Capsule contract: **changeforge.fixture-capsule.v2**. Its hash detects drift, its typed semantic gate rejects synchronized placeholder/low-diversity forgeries, and its deterministic renderer is evaluator-only and excluded from build/install artifacts.

The Control Prompt is embedded in each rendered Main Profile and is not added a second time.

## Authoritative Limits and Observed Maxima

Soft targets and hard ceilings come only from the Core Model and are provisional migration values, not calibrated optima. Soft overage is an advisory; hard overage fails Conformance without truncating required context.

Mode: **conformance**.

| Context | Soft target | Hard ceiling | Observed maximum | Soft margin | Hard margin | Soft status | Hard status |
| --- | ---: | ---: | ---: | ---: | ---: | --- | --- |
| Main always-loaded | 2305 | 2650 | 2177 | 128 | 473 | within | within |
| Direct Task dispatch | 3000 | 3200 | 2042 | 958 | 1158 | within | within |
| Analyzed Task dispatch | 6000 | 6500 | 3719 | 2281 | 2781 | within | within |
| Analysis dispatch | 4500 | 5000 | 2414 | 2086 | 2586 | within | within |
| Review dispatch | 3700 | 4000 | 2224 | 1476 | 1776 | within | within |
| Utility dispatch | 2000 | 2500 | 850 | 1150 | 1650 | within | within |

## Calibration Distribution

Calibration candidate selection and frontier construction do not apply soft targets or hard ceilings. Percentiles use nearest rank.

| Context | Count | P50 | P90 | P95 | P99 | Max | Growth distribution |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| Main always-loaded | 3 | 2170 | 2177 | 2177 | 2177 | 2177 | unavailable |
| Direct Task dispatch | 19281 | 2193 | 2643 | 2711 | 2819 | 3047 | unavailable |
| Analyzed Task dispatch | 66150 | 2677 | 3180 | 3334 | 3548 | 3995 | unavailable |
| Analysis dispatch | 112828 | 1793 | 2128 | 2312 | 2652 | 3445 | unavailable |
| Review dispatch | 38009 | 2357 | 2801 | 2992 | 3161 | 3341 | unavailable |
| Utility dispatch | 6 | 828 | 850 | 850 | 850 | 850 | unavailable |

Valid-candidate selection identity: `8dbe614c1f05bd042c11424f0e68f9534ff165eb13236a1c344077172b5b4893`. Temporal growth is unavailable because this run has one comparable snapshot.

## Admissible Context Composition Gate

Contract: **changeforge.admissible-context-composition-eval/v1**; selector owner surfaces: **65**; canonical legal selection equivalence classes: **14051**; exact measurements: **5**.

| Context | Soft target | Hard ceiling | Reachable maximum | Professional | Layer 3 | Owner | Build | Host |
| --- | ---: | ---: | ---: | --- | --- | --- | --- | --- |
| task | 3000 | 3200 | 3047 | change-documentation-gate | documentation-generation | main-control-agent | recommended | copilot |
| analyzed_task | 6000 | 6500 | 3995 | backend-change-builder | failure-diagnosis, filesystem-process-safety, nodejs-runtime-professional-usage | engineering-brief | recommended | copilot |
| analysis | 4500 | 5000 | 3445 | engineering-change-analysis | package-dependency-management, repository-context-map, minimal-correct-implementation | main-control-agent | recommended | claude |
| review | 3700 | 4000 | 3341 | ai-code-review-refactor | domain-object-identification, implementation-structure-design, refactoring | engineering-brief | recommended | codex |

### Dominance Frontier Projection

| Context | Canonical candidates | Exact render signatures | Over target |
| --- | ---: | ---: | ---: |
| task | 19281 | 19281 | 1 |
| analyzed_task | 66150 | 66150 | 0 |
| analysis | 112828 | 46158 | 0 |
| review | 38009 | 16641 | 0 |

Global Task/Review frontier counts: professional=1, layer3=1, active_reference=1; safe complement: professional=16, layer3=67, active_reference=266.

Mapping digest: `2e7f29316d4e6e4fcb9dd8fdb780da1f0dfd3f509cfccc848eaed5f4321e99e1`; runtime consumers: **0**; build consumers: **0**.

Coverage: analysis_foundation_domain=yes, analyzed_task_three_layer3=yes, review_domain_foundation=yes, nested_targeted_references=yes, direct_main_owner=yes, initial_analysis_main_owner=yes, analyzed_brief_owner=yes, direct_false_worst_excluded=yes.

Forbidden-combination evidence: >3 rejected=47; unauthorized exact rejected=65; duplicate exact rejected=63; silent truncations=0; nearest-negative leaks=0.

### Composition Proof Limits

- Selector equivalence classes use declarative positive and nearest-negative signals; the evaluator does not classify task prose.
- Reference subset coverage is a conservative role-compatible upper envelope; registry indexes and catalogs are forbidden and mode contracts remain isolated.
- Capsule contribution uses the largest validated checked-in fixture Capsule per budget class, not arbitrary future user prose.
- Every legal render candidate maps to one source-derived reduction stratum; exact tokenization is memoized by ordered component fingerprint and applied to the highest component-token representative of every stratum.
- Sequenced Reference stages are source-owned; only canonically replayed engineering-brief Task/Review carriers may replace a predecessor body, while other owner surfaces conservatively co-load.
- Reported maxima are exact for the deterministic canonical representatives; the full inventory count and dominance mapping remain available separately.

Maximum exact normalized duplicate-rule ratio: **0.003713** (gate: **0.03**; margin: **0.026287**).

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

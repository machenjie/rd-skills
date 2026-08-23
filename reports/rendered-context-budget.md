# Rendered Context Budget Evaluation

Status: **fail**

Evidence scope: **deterministic-rendered-artifacts**

Compiled Layer 3 format: **ai-consumption-v1**

Tokenizer: **o200k_base**

Fixtures: **16**; dispatches: **38**; host/profile measurements: **342**.
Explicit nested Layer 3 Reference loads: **8**; logical IDs: **ai-product-extension/references/checklist.md, module-boundary-design/references/benchmarks-and-enforcement.md, payment-trading-extension/references/duplicate-financial-effect-control.md, release-rollback/references/benchmarks-and-patterns.md, release-rollback/references/evidence-patterns.md, test-strategy/references/checklist.md, transaction-consistency/references/evidence-patterns.md, web-security/references/checklist.md**.
Measured nested Reference components across host/profile combinations: **72**.

Fixture Capsule contract: **changeforge.fixture-capsule.v2**. Its hash detects drift, its typed semantic gate rejects synchronized placeholder/low-diversity forgeries, and its deterministic renderer is evaluator-only and excluded from build/install artifacts.

The Control Prompt is embedded in each rendered Main Profile and is not added a second time.

## Authoritative Limits and Observed Maxima

Capacity ceilings, minimum headroom ratios, and minimum release margins come from the Core Model. Release and evolution targets are derived; calibration relaxations: **none**.

| Context | Capacity ceiling | Required reserve | Release target | Minimum release margin | Evolution target | Observed maximum | Release margin | Evolution margin | Capacity headroom ratio |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Main always-loaded | 2200 | 220 | 1980 | 80 | 1900 | 1800 | 180 | 100 | 0.181818 |
| Direct Task dispatch | 3200 | 0 | 3200 | 0 | 3200 | 2281 | 919 | 919 | 0.287187 |
| Analyzed Task dispatch | 6500 | 0 | 6500 | 0 | 6500 | 4876 | 1624 | 1624 | 0.249846 |
| Analysis dispatch | 5000 | 0 | 5000 | 0 | 5000 | 3036 | 1964 | 1964 | 0.3928 |
| Review dispatch | 4000 | 0 | 4000 | 0 | 4000 | 2961 | 1039 | 1039 | 0.25975 |
| Utility dispatch | 2500 | 0 | 2500 | 0 | 2500 | 1030 | 1470 | 1470 | 0.588 |

## Admissible Context Composition Gate

Contract: **changeforge.admissible-context-composition-eval/v1**; selector owner surfaces: **65**; canonical legal selection equivalence classes: **14035**; exact measurements: **8**.

| Context | Phase 3 target | Reachable maximum | Professional | Layer 3 | Owner | Build | Host |
| --- | ---: | ---: | --- | --- | --- | --- | --- |
| task | 3000 | 4456 | frontend-change-builder | interaction-state-modeling, accessibility-inclusive-design, web-platform-professional-usage | main-control-agent | dev | copilot |
| analyzed_task | 6000 | 4897 | repository-tooling-change-builder | implementation-structure-design, build-tool-professional-usage, filesystem-process-safety | engineering-brief | dev | copilot |
| analysis | 4500 | 3998 | engineering-change-analysis | package-dependency-management, repository-context-map, minimal-correct-implementation | main-control-agent | dev | claude |
| review | 3700 | 4724 | architecture-impact-reviewer | module-boundary-design, implementation-structure-design, technology-stack-selection | engineering-brief | dev | copilot |

### Dominance Frontier Projection

| Context | Canonical candidates | Exact render signatures | Over target |
| --- | ---: | ---: | ---: |
| analysis | 112735 | 46065 | 0 |
| task | 22529 | 22529 | 18843 |
| analyzed_task | 65028 | 65028 | 0 |
| review | 41203 | 16079 | 5208 |

Global Task/Review frontier counts: professional=16, layer3=70, active_reference=227; safe complement: professional=2, layer3=0, active_reference=43.

Mapping digest: `3be8e358015548cd26e175e7868b8eacfb83f730d76902a8fdc3c798a66d7ed5`; runtime consumers: **0**; build consumers: **0**.

Coverage: analysis_foundation_domain=yes, analyzed_task_three_layer3=yes, review_domain_foundation=yes, nested_targeted_references=yes, direct_main_owner=yes, initial_analysis_main_owner=yes, analyzed_brief_owner=yes, direct_false_worst_excluded=yes.

Forbidden-combination evidence: >3 rejected=47; unauthorized exact rejected=65; duplicate exact rejected=63; silent truncations=0; nearest-negative leaks=0.

### Composition Proof Limits

- Selector equivalence classes use declarative positive and nearest-negative signals; the evaluator does not classify task prose.
- Reference subset coverage is a conservative role-compatible upper envelope; registry indexes and catalogs are forbidden and mode contracts remain isolated.
- Capsule contribution uses the largest validated checked-in fixture Capsule per budget class, not arbitrary future user prose.
- Every legal render candidate maps to one source-derived reduction stratum; exact tokenization is memoized by ordered component fingerprint and applied to the highest component-token representative of every stratum.
- Sequenced Reference stages are source-owned; only canonically replayed engineering-brief Task/Review carriers may replace a predecessor body, while other owner surfaces conservatively co-load.
- Reported maxima are exact for the deterministic canonical representatives; the full inventory count and dominance mapping remain available separately.

Maximum exact normalized duplicate-rule ratio: **0.021361** (gate: **0.03**; margin: **0.008639**).

Discovery metadata is reported separately because actual host discovery injection is not observed.

## Transferred Context Measurement

Gross exclusive transferred-context tokens: **14344**; non-compressible: **14344**; compressible: **0**; ratio: **0.0**.

Long tasks joined from lightweight required progress: **9**; conservative ratio: **0.551552**.

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

## Errors

- admissible composition task maximum 4456 exceeds Phase 3 target 3000
- admissible composition review maximum 4724 exceeds Phase 3 target 3700

# Rendered Context Budget Evaluation

Status: **pass**

Evidence scope: **deterministic-rendered-artifacts**

Compiled Layer 3 format: **ai-consumption-v1**

Tokenizer: **o200k_base**

Fixtures: **16**; dispatches: **38**; host/profile measurements: **342**.
Explicit nested Layer 3 Reference loads: **8**; logical IDs: **ai-product-extension/references/checklist.md, module-boundary-design/references/benchmarks-and-enforcement.md, payment-trading-extension/references/checklist.md, release-rollback/references/benchmarks-and-patterns.md, release-rollback/references/evidence-patterns.md, test-strategy/references/checklist.md, transaction-consistency/references/evidence-patterns.md, web-security/references/checklist.md**.
Measured nested Reference components across host/profile combinations: **72**.

Fixture Capsule contract: **changeforge.fixture-capsule.v2**. Its hash detects drift, its typed semantic gate rejects synchronized placeholder/low-diversity forgeries, and its deterministic renderer is evaluator-only and excluded from build/install artifacts.

The Control Prompt is embedded in each rendered Main Profile and is not added a second time.

## Authoritative Limits and Observed Maxima

Capacity ceilings, minimum headroom ratios, and minimum release margins come from the Core Model. Release and evolution targets are derived; calibration relaxations: **none**.

| Context | Capacity ceiling | Required reserve | Release target | Minimum release margin | Evolution target | Observed maximum | Release margin | Evolution margin | Capacity headroom ratio |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Main always-loaded | 2200 | 220 | 1980 | 80 | 1900 | 1894 | 86 | 6 | 0.139091 |
| Direct Task dispatch | 3200 | 0 | 3200 | 0 | 3200 | 3124 | 76 | 76 | 0.02375 |
| Analyzed Task dispatch | 6500 | 0 | 6500 | 0 | 6500 | 6386 | 114 | 114 | 0.017538 |
| Analysis dispatch | 5000 | 0 | 5000 | 0 | 5000 | 4885 | 115 | 115 | 0.023 |
| Review dispatch | 4000 | 0 | 4000 | 0 | 4000 | 3357 | 643 | 643 | 0.16075 |
| Utility dispatch | 2500 | 0 | 2500 | 0 | 2500 | 1344 | 1156 | 1156 | 0.4624 |

Maximum exact normalized duplicate-rule ratio: **0.013804** (gate: **0.03**; margin: **0.016196**).

Discovery metadata is reported separately because actual host discovery injection is not observed.

## Limitations

- Counts cover deterministic rendered ChangeForge instructions and canonical Capsules rendered from versioned checked-in fixture data, not a host-observed model request.
- Counts exclude host system prompts, tool schemas, user conversation history, repository reads, diffs, command output, and other dynamic evidence.
- Host loaders may transform Profile or Skill files and may expose discovery metadata differently; this report does not prove real-host accuracy.
- Token counts do not prove wall-clock performance, production accuracy, Profile startup, or the installed user experience.
- Duplicate-token measurement detects exact normalized Markdown rule blocks, not semantic paraphrases.
- Nested Layer 3 Reference counts include only explicitly named fixture files; directories, indexes, catalogs, and recursively linked files are never loaded.

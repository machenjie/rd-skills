# Skill Efficacy Benchmark Patterns

Dev/evaluation-only reference for `skill-efficacy-benchmark`. Load only for an explicit Skill/Agent Profile/routing/reference/evaluation change; never route it into ordinary product tasks or claim live efficacy from static repository evidence.

## Comparable Case Contract

| Element | Required decision |
| --- | --- |
| Claim and case | Name changed surface, bounded task, route risk, expected behavior delta, and defect/overhead consequence. |
| Baseline/treatment | Same task, Agent Profile, unique Runtime build identity, source-vs-dist boundary, fixtures, evidence availability, and metric definitions. |
| Blind execution | Use opaque arms and neutral agent-visible identifiers. Keep the agent packet, evaluator-only oracle, observations, verifier-owned captures, and post-capture reveal in separate artifacts. Bind task, Host, Model, Agent Profile, repository state, evidence boundary, evaluator, and expected-definition digest identically; verify capture bytes, SHA-256, ordered treatment source, and provenance before a live claim. |
| Missing baseline | Evidence class is `structural-only` and final verdict is `not_enough_evidence`; empirical improvement, productivity, accuracy, latency, and user-outcome language remains unsupported. |
| Routing/reference guard | Record selected and skipped Agent Profiles/Skills/references with task-specific reasons plus trivial over-routing and hidden-risk under-routing cases. |
| Validation freshness | When the benchmark changes a body, reference, registry, Agent Profile, fixture, report, or Runtime build output, map that surface to a post-final-edit validator or residual owner. |
| Context cost | Record measured token/turn/elapsed values or `not_collected`; proxy tokens and turn counts are not live user experience. |

Use the Core-owned behavior metric set and directions. It covers routing path,
Agent Profile, primary and Layer 3 selection, Domain false positives/negatives,
fallback and boundary stability, Review routing, Review Input Ready,
independence, required-specialist recall/FNR, complete Initial Review, fresh
focused Re-review, exact finding relation/disposition, over-review, and
context cost. A score without a negative case or behavior difference is not
efficacy evidence. Preserve per-case outcomes: no aggregate improvement can
offset a NEW regression, and partial success is not demonstrated improvement.

Fixtures remain bounded, synthetic or repository-owned, redacted, and reproducible. Exclude raw user prompts outside approved fixtures, secrets, environment values, private URLs or identifiers, and personal archives. Also exclude unbounded source corpora, connector payloads without a boundary, and full command logs when status plus a bounded summary suffices.

## Proof Limits And Routes

Route fixtures and static validators prove the represented cases, not unrepresented ones. Small samples do not estimate population catch rate. Token proxies are not live usage. Reports and builds do not prove real-host startup, wall-clock performance, production accuracy, or installed user experience.

Reject score-only success, no negative control, all-references treatment, raw prompt corpora, static reports described as live improvement, and validation predating the final edit. Route authoring gaps to `skill-authoring-expert`, route changes to `routing-quality-review`, release validation to `quality-test-gate`/`targeted-validation-selection`, and context-boundary questions to `task-context-selection`. Benchmark completion, execution-level, retry, and review behavior directly against their contracts in `src/control-model/core-contracts.json`; use `scripts/eval-agent-lightweight.py` and `scripts/eval-pressure-behavior.py` as applicable.

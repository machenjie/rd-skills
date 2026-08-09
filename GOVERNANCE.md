# Governance

This document defines the default governance model for ChangeForge until maintainers publish a more formal structure.

## Roles

Maintainers are responsible for repository direction, review standards, release decisions, security handling, and enforcement of project boundaries.

Contributors propose issues, pull requests, documentation, tests, examples, and review feedback. Contributors do not gain release authority unless maintainers explicitly grant it.

## Decision Process

Routine fixes may be accepted after maintainer review and passing validation.

Documentation-only wording changes can remain documentation-only in file scope.
Every committed Skill-system change still runs Development Affected validation.
The local Full Regression is required at the integration or release-candidate
boundary. Changes to validation commands, quality levels, routing,
operating-model semantics, benchmark interpretation, eval fixtures, or release
evidence also require maintainer review because they change execution or
evidence semantics.

Changes require explicit maintainer agreement when they affect:

- Runtime profile semantics.
- Installer, upgrade, uninstall, or doctor behavior.
- Registry schema or routing behavior.
- Security, privacy, licensing, or release policy.
- Public documentation promises.
- The repository boundary against personal asset mapping or raw `src/` installation.

Maintainers should prefer small, evidence-backed changes with clear validation output. Unresolved assumptions should be documented in the pull request or release handoff.

## Release Authority

Only maintainers may cut releases, publish packaged artifacts, or change project license metadata. Releases must follow [docs/RELEASE.md](docs/RELEASE.md).

## Conflict Of Interest

A maintainer should recuse themselves from final decisions when they have a direct personal, employment, financial, or security-reporting conflict that could reasonably affect judgment.

## License Decision

The root [LICENSE](LICENSE) is the repository's MIT legal grant for source,
tooling, validation, build, package, installer, and generated Skill or Agent
Profile artifacts unless a file states otherwise. Repository license metadata
and generated Skill frontmatter are separate contracts; build and installation
preserve the generated frontmatter.

Maintainers may change the license or its project metadata only through an
explicit governance decision, documentation update, and release-readiness
validation. [Open-source readiness](docs/OPEN_SOURCE_READINESS.md) owns the
current metadata and publication checks.

## Final Requirements Remediation Backlog

This is the lightweight maintainer record for verified final-requirements gaps.
IDs are stable; status changes require source-backed acceptance and the listed
targeted validation. This document is not a runtime task-state or evidence
system.

<!-- BEGIN CHANGEFORGE GOVERNANCE CONTEXT BUDGET AUTHORITY -->
## Rendered Context Budget Authority

[reports/rendered-context-budget.json](reports/rendered-context-budget.json) is
the single source of truth for current rendered token totals, maximum fixture
IDs, margins, duplicate-rule ratio, and pass/fail status. Governance records no
current measurement snapshot.

The fixed capacity ceilings below come from
`src/control-model/core-contracts.json#/context_budget_contract`. They are
constraints, not current measurements.

| Context | Fixed capacity ceiling |
| --- | ---: |
| Main always-loaded | 2200 |
| Direct Task dispatch | 3200 |
| Analyzed Task dispatch | 6500 |
| Analysis dispatch | 5000 |
| Review dispatch | 4000 |
| Utility dispatch | 2500 |

The report must exist, have `status: pass`, report no errors, and project these
ceilings unchanged. Run `python3 scripts/eval-rendered-context-budget.py` to
refresh current evidence.
<!-- END CHANGEFORGE GOVERNANCE CONTEXT BUDGET AUTHORITY -->

### RDS-001 — Tighten Direct Task Eligibility

- **Status:** `resolved`
- **Sections:** authoritative final requirements §5; prior audit
  category: routing eligibility.
- **Requirement:** Direct Task eligibility must require owner, placement,
  acceptance, rollback, and non-production verification to be known before
  dispatch. Discovery of owner or verification routes to Analyzed Work.
- **Authoritative owner / scope:** `src/control-prompts/main-control-agent.md`,
  `src/control-model/core-contracts.json` execution-level eligibility,
  `src/control-skills/engineering-control-plane/references/direct-task-template.md`,
  and Direct-route fixtures.
- **Acceptance:** No Direct route authorizes owner, placement, acceptance, or
  verification discovery; positive fixtures prove every eligibility fact and
  negative fixtures route each unknown fact to analysis.
- **Targeted validation:** `python3 scripts/validate-control-plane-prompt.py`,
  `python3 scripts/validate-task-contracts.py`, `python3 scripts/eval-routing.py`,
  and the Direct pressure fixtures.
- **Closure evidence:** Direct eligibility is explicit, local, and known; six
  unresolved boundaries route to Analyzed Work, with four distinct negative
  fixtures. Supported Profiles and the showcase are current; the canonical Main
  prompt remains within its source budget. The current rendered-budget
  conclusion is `pass` under the
  [budget authority](#rendered-context-budget-authority); current totals,
  maxima, and margins are read only from its report and are not repeated here.
  The latest combined diff received independent approval. Historical pre-fix
  Red remains unavailable and live-host novelty remains unverified.
- **Dependency:** None.
- **Proof limit:** Static routing and fixtures do not prove a host will classify
  every novel request correctly.

### RDS-002 — Guarantee Common Direct-Route Guards

- **Status:** `resolved`
- **Sections:** authoritative final requirements §6; prior
  audit category: execution discipline.
- **Requirement:** Every Direct implementation route must apply the common
  pre-edit inspection, measurable acceptance, bugfix same-pattern scan,
  reuse/placement check, and minimal-correct-change guards.
- **Authoritative owner / scope:** the common control contract in
  `src/control-model/core-contracts.json`, Task Profile instructions in
  `src/agent-profiles/role-agents.json`, control templates, and every
  task-routable Professional Skill in `src/registry/professional-skills.yaml`.
- **Acceptance:** Before editing, every Direct route verifies the owning
  implementation, relevant existing tests, minimum caller/consumer path,
  current behavior, ownership, reuse candidates, and edit boundary. Acceptance
  names observable normal, invalid, boundary, and forbidden outcomes when
  relevant. A bugfix first verifies the failure mechanism, separates symptom
  from cause, and scans every materially reachable same-pattern path. The
  contract requires reuse before new structure, owner-local placement, no
  public API created only for testing, and the smallest complete change; it
  stops or returns to analysis when any required fact or boundary is unknown.
- **Targeted validation:** `python3 scripts/validate-agent-profiles.py`,
  `python3 scripts/validate-task-contracts.py`,
  `python3 scripts/validate-professional-routing-coverage.py`, and
  `python3 scripts/eval-agent-lightweight.py`.
- **Closure evidence:** The authoritative
  [implementation-discipline Core profile projection](src/control-model/core-contracts.json)
  projects only to `task-agent`. The same Core source owns the role-specific
  Profile instruction maximum, so Governance does not repeat either current
  count. The
  [Profile validation test module](tests/scripts/test_validate_agent_profiles.py)
  is authoritative for the current profile projection and maximum result, and
  the
  [lightweight evaluator test module](tests/scripts/test_eval_agent_lightweight_utility.py)
  is authoritative for the current normal-route and guard-mutation result.
  Every real normal edit trajectory has typed owner, test, and caller reads
  plus closed, ordered A–F evidence before editing. Direct and post-analysis
  positives, guard mutations, and edit-before-evidence negatives pass.
  Internal evidence is excluded only from user-visible metrics. The current
  rendered-budget conclusion for Direct and Analyzed contexts is `pass` under
  the [budget authority](#rendered-context-budget-authority); its report owns
  all current totals and margins. Requested L1 cannot undercut L3/L4. The
  latest independent review is `PASS`.
- **Dependency:** RDS-001.
- **Proof limit:** Deterministic fixtures do not prove live-host behavior, the
  full authoring gate, or formal-release readiness.

### RDS-003 — Add Adaptive Testing And A Valid Red Contract

- **Status:** `resolved`
- **Sections:** authoritative final requirements §7; prior
  audit category: testing discipline.
- **Requirement:** Every normal behavior batch must choose exactly one approach:
  test-first, test-after, existing-proof-only, or non-test validation. The
  choice follows the changed failure mechanism, boundary, derived risk, and
  available oracle, and current proof follows the final material edit.
- **Authoritative owner / scope:** the schema-2 implementation-discipline Core
  contract in `src/control-model/core-contracts.json` is the single Guard G
  owner. The Task Profile, task-routable Skills, control templates, validators,
  and full-trajectory fixtures are validated projections and consumers.
- **Acceptance:** The contract records one approach, its reason, oracle,
  evidence, and proof boundary, and rejects fixed test-layer recipes. Valid Red
  fails for the intended behavior before the fix; environment, fixture,
  import, syntax, or unrelated failures are invalid, as are weakened assertions
  that merely turn Red Green. Existing-proof-only requires fresh mechanism
  coverage; non-test validation is limited to named non-testable change kinds.
  Derived high-risk inputs cannot be omitted, misreported, or downgraded.
- **Targeted validation:** `python3 scripts/validate-agent-profiles.py`,
  `python3 scripts/validate-task-contracts.py`,
  `python3 scripts/validate-capabilities.py`, and
  `python3 scripts/eval-agent-lightweight.py`.
- **Closure evidence:** Guard G qualifies all four methods: test-first is
  preferred for derived high-risk work; test-after is limited to low-risk local
  exploration or existing primary coverage; existing-proof-only requires a
  current regression mechanism with no newly uncovered behavior; and non-test
  validation is limited to its closed change-kind set. Every full normal-edit
  trajectory binds one method before editing and current proof after its final
  material edit. Derived high-risk bindings fail closed against missing or
  downgraded risk. Fifteen adaptive-testing controls and the full-path negative
  fixtures pass. The
  [Core role-specific Profile instruction maximum](src/control-model/core-contracts.json),
  [Task Profile source](src/agent-profiles/role-agents.json), and
  [Profile validation test module](tests/scripts/test_validate_agent_profiles.py)
  are authoritative for the current profile limit, projection, and validation
  result; Governance does not copy the current rule count. Independent
  re-review is `PASS`.
- **Dependency:** RDS-002 and RDS-005.
- **Proof limit:** A synthetic Red/Green fixture does not prove production
  causality, integration fidelity, or absence of adjacent regressions.

### RDS-004 — Complete Mandatory Review Dimensions

- **Status:** `resolved`
- **Sections:** authoritative final requirements §9; prior
  audit category: review completeness.
- **Requirement:** Every Review Skill must decide applicability for correctness
  and invariants; authority/security/privacy; failure/recovery/concurrency;
  performance/resources; contracts/data/consumers; tests and evidence;
  maintainability/structure; and operational, documentation, and release
  effects.
- **Authoritative owner / scope:** all Professional Skills with
  `review-agent` support in `src/registry/professional-skills.yaml`, the
  `code-review` Foundation package, and review handoff/checklist contracts.
- **Acceptance:** A single canonical dimension matrix is validated across all
  Review Skills; each dimension is inspected, explicitly not applicable with
  evidence, or delegated to a named specialist, and no route can silently omit
  one.
- **Targeted validation:** `python3 scripts/validate-registry.py`,
  `python3 scripts/validate-professional-routing-coverage.py`,
  `python3 scripts/eval-skill-professionalism.py`, and review behavior fixtures.
- **Closure evidence:** The Core-owned `review_discipline_contract` defines one
  ordered eight-dimension professional-risk matrix. Its dynamic registry
  selector covers exactly the current 11 `review-agent` Professional Skills and
  automatically includes future matching Skills. Every dimension uses one of
  five closed statuses: `verified`, `finding`, `not-applicable`, `delegated`, or
  `blocked`. Not-applicable decisions require source-backed reasons and evidence;
  delegation requires a named specialist, scope, and reason. Missing, duplicate,
  or unknown dimensions block the verdict. Thirty typed full-path controls pass.
  The prior ten process dimensions remain uniform at L1-L5, and repair review kind
  still derives from actual material repair actions rather than declared labels.
  Independent matrix-implementation review is `PASS`; its only finding was this
  stale governance entry. Host and `dist/` projection freshness remains owned by
  open RDS-010 and does not reopen this requirement.
- **Dependency:** RDS-002 and RDS-005.
- **Proof limit:** Dimension coverage proves review instructions and fixtures,
  not defect detection completeness on an unseen implementation.

### RDS-005 — Make L1–L4 Evidence Lightweight

- **Status:** `resolved`
- **Sections:** authoritative final requirements §§1, 8, 10, and 16; prior audit
  category: evidence proportionality. The earlier L1–L5 requirement is a
  compatibility constraint, not a numbered final section.
- **Requirement:** L1–L4 share concise `Level` and `Basis` decisions and the
  nine-field visible Evidence Ledger; conditional comprehensive proof and
  independent review obligations remain explicit for L5.
- **Authoritative owner / scope:** execution-level and visible-evidence data
  in `src/control-model/core-contracts.json`, the main control prompt, the four
  Agent Profiles, control templates, and their validators/evals.
- **Acceptance:** The heavy execution-level manifest, identity, adapter, path,
  history, transition, and validation-attempt state system is removed. The
  `Level` / `Basis` projection, conditional L5 evidence, nine-field Evidence
  Ledger, lightweight `retry_policy`, and non-bypassable formal-release
  evidence remain.
- **Targeted validation:** `python3 scripts/validate-control-plane-prompt.py`,
  `python3 scripts/validate-agent-profiles.py`,
  `python3 scripts/validate-task-contracts.py`,
  `python3 scripts/eval-agent-lightweight.py`, and
  `python3 scripts/eval-rendered-context-budget.py`.
- **Closure evidence:** The two focused suites pass 84 + 6 tests, the production
  retired-symbol scan reports zero occurrences, and independent re-review is
  `PASS`.
- **Dependency:** None; settle before closing RDS-001 through RDS-004.
- **Proof limit:** Smaller instructions do not prove lower agent effort, lower
  latency, or better host compliance without separate observed-host evidence.

### RDS-006 — Remove Six Foundation Control Duplicates

- **Status:** `resolved`
- **Sections:** authoritative final requirements §3; prior
  audit category: layer ownership and duplication.
- **Requirement:** Remove or narrow the duplicated Control/Profile/general
  rules in `agent-execution-discipline`, `agent-tool-permission-sandbox`,
  `task-context-selection`, `task-handoff-context`,
  `task-dag-decomposition`, and `targeted-validation-selection`.
- **Authoritative owner / scope:** those six packages under
  `src/foundation/capabilities/`, their entries in
  `src/registry/foundation-skills.yaml`, and Professional owners that compile
  them.
- **Acceptance:** Each surviving package owns a distinct professional decision;
  Control/Profile rules have one authority, registry routes and output
  contracts remain complete, and normal builds contain no duplicate control
  instruction under a Foundation name.
- **Targeted validation:** `python3 scripts/validate-capabilities.py`,
  `python3 scripts/validate-registry.py`,
  `python3 scripts/validate-reference-content.py --strict`, and
  `python3 scripts/eval-rendered-context-budget.py`.
- **Progress / phase evidence:**
  - [x] `agent-tool-permission-sandbox` now owns only task-level command-risk
    classification. Its focused contract passes 4/4 tests, and independent
    review is `PASS`.
  - [x] `agent-execution-discipline` now owns only scoped execution-evidence
    assessment. Its focused target-and-consumer contract passes 6/6 tests, the
    consumer routes repeated same-path failure to Core `retry_policy` and
    material recurrence exposure to `regression-testing`, and independent
    review is `PASS`.
  - [x] `task-context-selection` now owns working-context selection before or
    during one decision; downstream transfer remains with
    `task-handoff-context`. Its focused target, consumer, and boundary contract
    passes 12/12 tests, the benchmark's stale completion/pressure route now
    resolves directly to Core contracts and evaluators, and independent review
    is `PASS`.
  - [x] `task-handoff-context` now owns only downstream-transfer context after
    work, while `task-context-selection` owns working context before or during
    a decision. Root and Reference readability report zero findings, the
    focused target, consumer-boundary, and semantic-anchor contract passes
    10/10 tests, and independent review is `PASS`.
  - [x] `task-dag-decomposition` now owns only pre-DAG candidate-graph
    evidence; `task-dag-planner` owns candidate node and edge acceptance or
    rejection, First Executable Slice selection, and the final authoritative
    Task DAG. Its single targeted Reference has zero readability findings, the
    focused target, consumer, routing, and semantic-anchor contract passes 5/5
    tests, and independent review is `PASS`.
  - [x] `targeted-validation-selection` now owns only post-strategy repository
    command-entry and coverage selection. `quality-test-gate` owns proof
    strategy and acceptance mapping, while Core Guard G and validation
    freshness own evidence timing. Its root and single targeted Reference have
    zero readability findings, the focused target, consumer, routing,
    semantic-anchor, and direct-projection contract passes 6/6 tests, and
    independent review is `PASS`.
- **Closure evidence:** All six exact subitems are resolved, and every retained
  package owns a distinct professional decision. Control/Profile ownership was
  removed while registry ownership, routing, and output contracts remained
  intact; all focused independent reviews are `PASS`. A post-closure capability
  drift repair restored canonical trigger boundaries for
  `agent-execution-discipline` and an exact eight-item root/Registry output
  projection for `targeted-validation-selection`. Capability validation passes
  all 133 Foundation Skills, Registry validation passes, and independent review
  is `PASS`. Global Reference validation remains blocked by open RDS-011, while
  generated and `dist/` freshness remains tracked by RDS-010.
- **Dependency:** RDS-002 and RDS-005 contract boundaries must be settled first.
- **Proof limit:** Structural deduplication does not prove semantic clarity or
  correct just-in-time selection for novel tasks.

### RDS-007 — Consolidate Five Control Fallback Blocks

- **Status:** `resolved`
- **Sections:** authoritative final requirements §§2 and 16; prior
  audit category: Control-template duplication.
- **Requirement:** Give the repeated complete integrity-fallback rule one
  Control authority while preserving fail-closed behavior in each consuming
  template.
- **Authoritative owner / scope:**
  `src/control-skills/engineering-control-plane/references/direct-task-template.md`,
  `src/control-skills/engineering-control-plane/references/engineering-brief-template.md`,
  `src/control-skills/engineering-control-plane/references/task-dag-template.md`,
  `src/control-skills/engineering-control-plane/references/implementation-handoff-template.md`,
  and
  `src/control-skills/engineering-control-plane/references/review-handoff-template.md`.
- **Acceptance:** The five templates resolve the same malformed-input rule from
  one authoritative contract without repeated compound prose; missing,
  malformed, or duplicate execution-level data still blocks editing and partial
  computation.
- **Targeted validation:** `python3 scripts/validate-control-skills.py`,
  `python3 scripts/validate-task-contracts.py`,
  `python3 scripts/validate-control-plane-prompt.py`, and
  `python3 scripts/eval-rendered-context-budget.py`.
- **Closure evidence:** One authoritative fallback now feeds five link-only
  preambles. The complete-preamble structural validator passes; the
  before/after-marker paraphrase/reorder mutation matrix passes 25/25; exact
  fail-closed behavior is preserved; and the latest diff received independent
  approval. Semantic currentness is owned by RDS-011 and does not reopen
  current-source closure.
- **Dependency:** RDS-005 and RDS-006.
- **Proof limit:** Exact projection and fixtures do not prove a host supplies
  valid execution-level data.

### RDS-008 — Split Payment And Web3 Compound Bullets

- **Status:** `resolved`
- **Sections:** authoritative final requirements §§2 and 3; prior
  audit category: AI readability and compound decisions.
- **Requirement:** Split compound decision bullets in the payment and Web3
  Domain Skills without moving domain authority into Control or Profiles.
- **Authoritative owner / scope:**
  `src/domain-extensions/payment-trading-extension/SKILL.md`,
  `src/domain-extensions/web3-product-extension/SKILL.md`, and their registries.
- **Acceptance:** Each revised bullet exposes one independently decidable
  domain obligation, retains its authority, failure boundary, and verification
  meaning, and leaves routing and output contracts unchanged.
- **Targeted validation:** `python3 scripts/audit-skill-content.py --gate authoring`,
  `python3 scripts/validate-root-content.py --strict`, and
  `python3 scripts/validate-domain-extensions.py`.
- **Closure evidence:** Payment now exposes 27 items across four domain
  sections; Web3 exposes 33 items across six. Original named semantics remain
  intact, shared evidence records are coherently grouped, and independently
  verifiable controls are separate. No detector exceptions were added;
  canonical advisories over 15 decision items remain visible. Domain, docs, diff, and
  focused collector checks passed; the latest diff received independent
  approval.
- **Dependency:** RDS-006.
- **Proof limit:** Static checks do not prove expert completeness; stale
  semantic disposition remains RDS-011.

### RDS-009 — Complete Seventeen Behavior Evaluations

- **Status:** `resolved`
- **Sections:** authoritative final requirements §15;
  prior audit category: behavior-eval completeness.
- **Requirement:** Cover all 17 mandatory behaviors with executable,
  machine-checked fixtures; replace pressure assertions that pass mainly by
  self-reported keywords with observable structural or state-transition checks.
- **Authoritative owner / scope:** `scripts/eval-agent-behavior.py`,
  `scripts/eval-pressure-behavior.py`, `evals/agent-behavior/`,
  `evals/pressure/hookless/`, and the required outcomes in
  `src/control-model/core-contracts.json`.
- **Acceptance:** A machine-readable coverage map names all 17 behaviors, every
  behavior has a required positive and bypass/negative case, missing coverage
  fails the gate, and keyword-only self-attestation cannot satisfy a behavior.
- **Resolution evidence:** The executable manifest covers exactly 17 behaviors
  in three closed groups: five AI-reading and ownership behaviors, six adaptive
  testing behaviors, and six engineering-closure behaviors. Every behavior has
  a full typed positive trajectory and a machine-applied bypass mutation that
  must produce its bound structured error. A single immutable per-ID evaluator
  oracle binds the positive case, validator family, bypass mutation, expected
  error code, and exact dimensions; each `cases.yaml` entry must equal that
  binding, so globally recognized mutations cannot be exchanged between IDs.
  Every positive first passes the complete trajectory metrics and
  implementation-discipline checks before any scheduling, review, or completion
  specialization runs.
- **Validation:** The
  [lightweight evaluator test module](tests/scripts/test_eval_agent_lightweight_utility.py)
  is authoritative for the current focused and utility test result, and
  `python3 scripts/eval-agent-lightweight.py --no-write-report` passed for all
  contract-required behavior entries. Independent review returned `PASS`. The
  validation intentionally wrote no report; checked-in report and broader
  source-freshness claims remain governed by RDS-010 and RDS-011 where
  applicable.
- **Dependency:** RDS-001 through RDS-005; update fixtures after those behavior
  contracts stabilize.
- **Proof limit:** Deterministic captured fixtures do not execute a model or
  prove real-host behavior, production accuracy, or pressure resistance. The
  no-write validation also does not refresh or attest checked-in reports.

### RDS-010 — Bind Dist Manifests To Source Freshness

- **Status:** `resolved`
- **Sections:** authoritative final requirements §1; audit-added build-freshness
  proof gap, prior audit category: build provenance and freshness.
- **Requirement:** Each dist manifest must bind the built artifact to the whole
  authoritative source tree and, when available, the source commit rather than
  only version and selected-file digests.
- **Authoritative owner / scope:** manifest production in `scripts/build.py`,
  package checks in `scripts/package.py`, installation validation in
  `scripts/validate-installation.py`, build-profile documentation, and build
  tests.
- **Acceptance:** A deterministic source-tree digest covers every build input;
  commit and dirty/unavailable state are explicit; changing any authoritative
  input makes a prior manifest stale; package and installation checks reject a
  mismatched binding.
- **Targeted validation:** build all three profiles, run
  `python3 scripts/validate-installation.py`,
  `python3 scripts/validate-productization-assets.py`, and a mutation fixture
  that proves stale-manifest rejection.
- **Historical, non-current resolution evidence:** At resolution time, the
  authoritative build-input snapshot covered 760 files with SHA-256
  `c43791936b4d39f15c960ae3e5d23c3a0a2017c54c4b81296924ac87b9600e1d`.
  All 30 generated manifests were current against that snapshot: 10 manifests
  per profile with top-level Skill counts `recommended=23`, `full=30`, and
  `dev=163`. The three package commands produced the same 23/30/163 zip counts;
  installation validation covered 10 Skill roots, 2,160 built Skill
  directories, 28 platform Profile files, and 216 zips, while Profile
  validation confirmed all four static Profiles. The six focused source
  freshness tests passed at resolution time, including source mutation and
  stale package/install rejection. These values are retained only as historical
  provenance and are not current status.
- **Current freshness authority:** Each generated
  `.changeforge-build-manifest.json` is the single source of truth for its
  artifact's current source digest and build identity. The
  [installation-validation report](reports/installation-validation.json) is the
  single source of truth for the current installation-validation result.
  Governance does not copy a current digest or generated-artifact count.
- **Dependency:** None; final manifests must be rebuilt after RDS-001 through
  RDS-009 land.
- **Proof limit:** A digest and commit binding prove local input identity, not
  signed provenance, repository trust, real-host startup, or installed behavior.

### RDS-011 — Regenerate Semantic Evidence Last

- **Status:** `partially resolved`; deterministic Root/Reference authoring
  passes, but formal evidence currentness remains pending. This is not a formal
  release claim.
- **Sections:** authoritative final requirements §§1 and 16; post-content formal
  evidence, prior audit category: semantic-evidence freshness. This is not a
  §15 behavior-evaluation item.
- **Requirement:** Check selected evidence currentness before creating a panel.
  Refresh only a surface whose source, detector, binding, lifecycle, lineage,
  storage, or decision currentness fails. Authoring still requires deterministic
  Root structural strictness, completed semantic triage, zero unresolved
  candidates, and zero disposition errors.
- **Authoritative owner / scope:** `evals/expert-panel/`,
  `config/professionalism-release-review.yaml`,
  `scripts/audit-skill-content.py`, expert-panel tooling, and
  `scripts/validate-professionalism-regression.py`. The producer's sole
  machine-readable readiness authority is
  `reports/professionalism-regression-report.json`; Core Principles owns the
  complete ordered freshness run.
- **Acceptance:** Current selectors and their required lineage bind to the final
  source tree, are tracked and byte-equal to `HEAD`, and report no stale,
  corrected, or unresolved result. A new round is not required when existing
  evidence remains current.
- **Targeted validation:** the local Full Regression followed by
  `python3 scripts/eval-core-principles.py --gate formal-release`. Core is the
  unique complete formal orchestrator and requires the aggregate
  `professionalism-formal-release-ready` outcome; a direct producer run is a
  diagnostic, not a second formal gate.
- **Selected evidence and current state:** For selector identity only, the
  canonical projection is: Current static evidence selectors are r26
  Readability, r26 Semantic Disposition, r26 Root lifecycle, and r19 schema-3
  Professional Completeness for all 189 non-Control packages. “Current” in that
  projection identifies the configured selector set; it does not assert that
  each selected surface is current. Readability r26 and full-fresh Professional
  Completeness r19 have complete decisions for their recorded inputs.
  Readability r26 is historical evidence whose bound Skill detector is stale
  against the current detector. It has `source_current=false`, status
  `panel-majority-stale`, remains storage-pending, and is not accepted for formal
  release. R19 is historical full-fresh evidence whose bound Professional
  review contract is now stale against the current contract; it remains
  storage-pending, is not accepted for formal release, and cannot authorize
  carry across the contract change. The selected Semantic Disposition application
  is `invalid` because its packet is stale against the current audit. The Root
  lifecycle is `pending-changes`, with no current snapshot and no formal-release
  readiness. The sole JSON authority therefore reports
  `release_gate=release-not-ready`.
- **Next owning stage:** After final content and audit stabilization, the
  Semantic Disposition owner refreshes the stale decision/application and the
  Root lifecycle owner records the classified formal snapshot. Formal Release
  must create a new current schema-2 Readability review under the current Skill
  detector and a new schema-3 full-fresh Professional Completeness round for all
  189 current non-Control packages under the current review contract. R26 and
  r19 remain immutable historical evidence; neither can replace its required
  new review, and r19 cannot authorize carry. Current evidence must be tracked,
  byte-equal to `HEAD`, and clean before the formal gates are rerun.
- **Report projection and freshness:**
  `scripts/validate-professionalism-regression.py` is the only producer of the
  authoritative JSON. Core Principles requires that JSON to be refreshed by
  its declared producer run. Formal-release orchestration additionally requests
  `reports/professionalism-regression-report.md` as a release-only presentation
  projection; Markdown is not a second readiness authority and Core authoring
  does not refresh it. Productization validates the saved JSON's
  closed semantics without rerunning the producer.
- **Authoring/formal split:** These static selectors do not prove that the final
  formal gates or same-commit remote workflow passed. Stale or tampered Root,
  Semantic Disposition, Readability, or Professional Completeness evidence
  remains invalid and blocks formal release.
- **Dependency:** RDS-001 through RDS-010, final content stabilization, the
  Semantic Disposition and Root lifecycle refresh stages, and expert-evidence
  check-in.
- **Proof limit:** Static qualification claims and panel artifacts do not prove
  reviewer identity, credentials, real-host startup, wall-clock performance,
  production accuracy, or installed user experience.

### RDS-012 — Align Implementation Structure Reference Output Type

**Status:** `resolved`. **Requirement:** Reconcile `implementation-structure-design`’s
indexed `targeted` Reference with its currently incompatible `checklist-result`
required output without weakening global Reference type enforcement.
**Acceptance:** The root Targeted References projection and registry entry use
one supported type/output contract, direct consumers retain their expected
artifact, and capability plus registry validation pass without exceptions.
**Targeted validation:** `python3 scripts/validate-capabilities.py`, `python3
scripts/validate-registry.py`, `python3 scripts/sync-targeted-references.py`, and
the relevant Reference registry unit tests.
**Closure evidence:** The object/module decomposition Reference is restored to
the supported `targeted` output contract `decision-record, residual-risk` in
the Registry and its root projection. Both physical References are indexed and
existing with zero non-template orphans. The global type/output contract and
the three direct consumers are unchanged. The owner-specific regression,
Registry validation, and no-write projection synchronization pass; independent
review is `PASS`. RDS-011 owns subsequent semantic-evidence currentness.
**Proof limit:** Structural
compatibility does not prove the Reference’s professional completeness or
real-agent behavior.

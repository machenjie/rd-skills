# Validation

Every completion or release claim needs evidence from the final material edit.
Generated reports are derived evidence only when their producer ran against the
same current tree.

## Gate Paths

### Development Affected

Ordinary committed development validates only the changed-path projection from
one selected base and head. The affected Core runner requires a clean checkout
at the selected head because it executes tracked files from that commit in a
disposable tree:

```text
python3 scripts/eval-core-principles.py --gate affected --base <base> --head <head>
python3 scripts/run-ci-tests.py run --base <base> --head <head>
```

Use focused owner checks while a change is still uncommitted. They become
completion evidence only when followed by the affected commit check or the
local Full Regression required by the integration boundary.

### Formal Release

Formal local evaluation has one complete command on one clean final commit:

```bash
python3 scripts/eval-core-principles.py --gate formal-release
```

The Core evaluator loads `src/control-model/core-contracts.json` and is the
unique owner of complete producer ordering and freshness. Its formal graph runs
the professionalism producer once and requires
`professionalism-formal-release-ready`, whose aggregate predicate includes
`release_gate=release-ready`; the existing granular Root, readability,
professional-completeness, cost, and lifecycle outcomes remain required. Its
authoring gate refreshes the tracked ordinary JSON projections. `formal-release`
writes the professionalism and Core schema-4 JSON outcomes plus their Markdown
projections under `.rd-skills/formal-release/<captured-head>/reports/` without
changing the tracked projections. Its declared intermediate report graph writes
and reads only the sibling head-scoped `producer-reports/` staging directory;
the final `reports/` scene contains exactly the four canonical Core and
professionalism artifacts. Core validates that exact head-scoped scene and
binds it to the captured input `HEAD`. Formal Release is independent from both
Development Affected and local Full Regression.

## Local Full Regression

Run this command set once, in order, on the final material tree before an
integration handoff or release-candidate decision:

```bash
python3 scripts/eval-core-principles.py --gate authoring
python3 scripts/validate-examples.py
python3 scripts/generate-examples-showcase.py --out docs/SHOWCASE.md --check
python3 scripts/generate-marketplace-catalog.py --profile recommended --out docs/MARKETPLACE_CATALOG.md --check
python3 scripts/validate-marketplace-index.py --profile recommended
python3 scripts/validate-marketplace-index.py --profile full
python3 scripts/validate-marketplace-index.py --profile dev
python3 scripts/validate-productization-assets.py
python3 scripts/validate-open-source-readiness.py --require-pass
python3 scripts/run-ci-tests.py full --jobs 4 --timeout 900
python3 scripts/validate-codegen-benchmarks.py
python3 scripts/run-codegen-benchmarks.py --limit 3
python3 scripts/quickstart.py --agent codex --scope user --dry-run
python3 scripts/quickstart.py --agent claude --scope project --target /tmp/changeforge-quickstart-claude --dry-run
python3 scripts/quickstart.py --agent copilot --scope project --target /tmp/changeforge-quickstart-copilot --dry-run
python3 scripts/quickstart.py --agent openai-api --dry-run
```

Core authoring is the canonical full deterministic producer owner. The
remaining commands are artifact consumers or non-Core repository checks; they
must not replay a Core-owned producer merely to count a second pass.

Development Affected runs only the selected affected producer and owner-test
closure; it does not run the local Full Regression above. The
[`impact_graph_contract`](../src/control-model/core-contracts.json) is the sole
authority for changed-path classification, canonical producer dependency
closure, owner-test selection, fail-closed outcomes, isolation, and build-profile
projection;
[`scripts/impact_graph.py`](../scripts/impact_graph.py) is its resolver.
`scripts/run-ci-tests.py` and `eval-core-principles.py --gate affected --base
<base> --head <head>` are consumers. This document does not mirror the graph's
path rules, producer IDs, test mappings, or no-impact inventory. Inspect the
Core contract or use `--explain` for the selected IDs and dependency chains.
Ordinary affected selection does not regenerate Expert Panel evidence. Panel
implementation, lifecycle, release-review configuration, fixed-attestation,
and release-manifest metadata changes select focused contract or governance
tests and report `expert_panel_evidence.status=soft-stale`; documentation alone
does not stale that evidence. Only the explicit Professional semantic-contract
projection selects full Professional static validation. Skill Root, indexed
Reference, registry-entry, and material-binding changes remain package-scoped
and include their proven dependent closure. Readability and Semantic detector
or contract changes select their focused axis validators. None of these
affected rules weakens or replaces the independent full strict Formal Release
or causes an affected run to generate panel packets, ballots, or attestations.
Package changes project their base and head registry entries through the actual
`recommended`, `full`, and `dev` build graph; an unresolved package selects all
three profiles. Build and code-generation integration tests, plus the focused
quickstart unit test, are selected only for direct changes to their owners. The
runner preserves that one unsharded selected list, then runs each selected
module in an isolated subprocess with a distinct temporary directory and
disabled bytecode writes. `--jobs` bounds concurrent modules (default `2`);
`--jobs 1` keeps a sequential diagnostic path, and `--timeout` bounds each
module. Worker logs, durations, and status are emitted in module-path order
regardless of completion order. A test failure returns `1`; selection, startup,
timeout, interruption, abnormal-exit, or cleanup errors return `2`. After the
first non-pass result, no new module is started, already-running workers are
collected boundedly, and remaining modules are reported as `not-run`. The
runner neither caches results nor changes Core selection policy. Every worker
and discovery subprocess receives the same explicit Python import path in
repository-root, then `scripts/` order; inherited `PYTHONPATH` and user-site
packages cannot change that precedence. Runner-owned Python interpreters use
Python's `-P` option instead of exporting `PYTHONSAFEPATH`, so the runner and
workers reject an implicit current-directory import while a tested nested CLI
retains Python's standard sibling-import behavior from its own script directory.

The official Full unittest command above uses the isolated parallel runner.
To inspect its discovery manifest without executing tests, use:

```bash
python3 scripts/run-ci-tests.py full --list-tests
```

The `full` action discovers the same `tests` tree without executing test methods
while it builds its manifest, rejects duplicate modules or test IDs, and then
runs one module per subprocess. A test module may own a top-level literal
`FULL_TEST_RESOURCE_CLASS` declaration from the closed set `standard`, `heavy`,
`tokenizer`, or `heavy-tokenizer`; absence means `standard`. Duplicate,
non-literal, or unknown declarations fail discovery. The manifest exposes the
module-to-class map, including under `--list-tests`, so scheduling inputs remain
inspectable without a central path table. List and execution manifests identify
this official path with the stable machine reason `full-regression`.

The parallel-safe lane has weight capacity `4`: `standard` and `tokenizer`
weigh `1`, while `heavy` and `heavy-tokenizer` weigh `3`. `--jobs` remains the
worker-count ceiling. At most one heavy-class module and one tokenizer-class
module can be active, including their combined class, so at `--jobs 4` a heavy
module can overlap at most one standard module. Dispatch orders the heavy
critical path first, breaks equal-weight ties by module path, and uses
deterministic first-fit to fill a remaining slot while a second heavy module is
blocked. Results remain path-sorted, and the first observed non-pass stops all
new dispatch.

Modules that create repository-root temporary state, mutate a root path, or
launch a subprocess with the repository as its working directory use a serial
exclusive lane after every parallel-safe module passes. Resource weights never
move a module out of that lane. The classifier limits exclusive checks to exact
`ROOT` symbols and qualified `.ROOT` attributes at the relevant call argument
or mutation receiver; unrelated root-prefixed constants do not make a module
exclusive. Each worker and the discovery subprocess owns a dedicated POSIX
process group. Worker start,
registration, and pending-queue removal form one interruption-safe dispatch
transaction, so every requested module receives exactly one result even when a
signal arrives during startup. The Full action owns one interrupt lifecycle
across discovery, both execution lanes, and final aggregation; discovery and
worker scopes delegate handler ownership while retaining their cleanup duties.
On supported POSIX hosts, the Full CLI blocks `SIGINT` and `SIGTERM` before its
first handler change and owns both handlers for the rest of that isolated
process. It does not restore application handlers and return to a reusable
Python caller. After results and the candidate exit code are known, it blocks
both signals once more, consumes pending owned signals, irrevocably marks the
exit-code state, and only then restores the previous mask. A signal in that
final transition or before process exit therefore produces exit `2`, never a
false success or default-signal termination. The ordinary affected runner keeps
its reusable install-and-restore lifecycle; a signal in its final restore/unmask
window follows the restored application handler, including `SIG_DFL` semantics.
Any interrupted or exceptional discovery path cleans
and verifies its owned group before returning execution error `2`. A descendant
that outlives its leader is terminated, reported as an execution error, and
cannot overlap the exclusive lane or runner return. Platforms without both that
process-group ownership guarantee and an atomic POSIX signal-mask lifecycle fail
before Full discovery or worker dispatch; the ordinary affected runner keeps
its existing best-effort platform behavior and completed-leader behavior.

Worker PID and temporary directory are isolated. Full discovery and worker
stdout/stderr are concurrently drained through pipes while produced, retain at
most the first 1 MiB per stream, and stop with an execution error on overflow;
they are not accumulated in unbounded strings or log files. Concurrency and
per-module duration are also bounded. Results are reported in module-path order,
dispatch stops after the first observed non-pass, and no result cache is used.
`--list-tests` emits the module/test-ID manifest and does not run any tests.

This runner is the official unittest step in local Full Regression. Core
authoring and the unique Core formal gate retain their separate ordered
ownership.

Affected producer execution uses only the selected commit's tracked files in a
disposable tree, so selected builds and their consumers do not modify the caller
workspace. Because `dist/` is ignored and has no checked-in artifact authority,
Development Affected does not claim a byte-freshness comparison for it.
Local Full Regression and Formal Release remain explicit independent paths.

The Full Regression does not launch Core-owned producers a second time. Its
hookless architecture, evaluation, and build modules do not import another test
module or consume the tracked Core report. Architecture tests verify their
current source contracts directly. Evaluation tests load their owned artifacts
and apply the existing schema, status, count, error, and cross-report
invariants. Build consumers additionally compare each manifest's
`authoritative_build_inputs` snapshot with the current narrow build input set.
Mutating a consumed field, required file, authoritative build input, or expected
Skill count fails the owning consumer. Arbitrary extra fields that no consumer
reads are explicitly outside this proof. These checks do not replay producers
or rewrite reports, so independent modules can run in parallel without a global
Core-report prerequisite.

`reports/core-principles-outcomes.json` is a historical Core execution record,
not a current-tree readiness authority and not the professionalism readiness
authority. Ordinary schema-4 validation treats current-tree status as
`not-evaluated`: it validates the recorded pre/post/unchanged integrity,
canonical contract hash, producer and artifact identities, predicates,
outcomes, principles, and authorities without computing or comparing a current
whole-tree digest. Development Affected does not refresh this global artifact.
Formal `release_projection` evidence remains strict: it compares the captured
input tree with the current final tree and stays bound to the clean captured
`HEAD` in the ignored, head-scoped formal scene. Formal Release does not replace
or consume the tracked ordinary producer reports.

## Signal Ownership

| Signal | Canonical authority | Passing signal |
| --- | --- | --- |
| Core Principles | `src/control-model/core-contracts.json` and `eval-core-principles.py` | Selected gate passes with all required producer outcomes current. |
| Root, Reference, and expert-review lifecycle | [Skill content governance](SKILL_CONTENT_GOVERNANCE.md) | Strict source validators and required independent decisions are current; no blocking disposition remains. |
| Documentation | `validate-docs-consistency.py` and local-link checks | Required docs, managed Core projections and markers, commands, and links match current source; ordinary prose is not whole-document hash-bound. |
| Routing and professional quality | Registries, deterministic fixtures, and professionalism producers | Fresh actual routes cover 233 canonical entries and 62 capability entries. The 429 admissions are 105 Professional, 276 Foundation, and 48 Domain. The Foundation projection covers 141 unique Foundation Skills in the 163-entry Layer 3 catalog. Required coverage and professional obligations pass without forbidden behavior. |
| Capability coverage | `evals/capability-coverage/matrix.yaml` and deterministic coverage validators | All 125 entries classify as 81 covered, 39 partial, 0 missing, and 5 intentionally unsupported; covered means catalog/routing evidence, not Professional Completeness. |
| Build and installation | [Build profiles](BUILD_PROFILES.md) and [Installation](INSTALLATION.md) | Profiles contain 27, 40, and 190 top-level Skills; supported hosts include four Profiles; manifests and doctor checks match. |
| Code generation | [Benchmarks](BENCHMARKS.md) | Definitions, harnesses, and starter negative controls pass; candidate claims require an explicit candidate input. |
| Open-source publication | [Open-source readiness](OPEN_SOURCE_READINESS.md) | Root license, metadata, contribution, security, and publication checks pass together. |

`eval-core-principles.py` is the only complete orchestrator for its declared
producer graph. Individual producer commands diagnose a verified failure; their
aggregate manual success is not a substitute for orchestrator ordering,
timeouts, freshness, input-tree checks, and outcome evaluation.

`reports/professionalism-regression-report.json` is the sole machine-readable
professionalism readiness authority, and
`scripts/validate-professionalism-regression.py` is its only producer. Core
Principles owns the complete ordered freshness run. Productization is a static
semantic consumer of the saved JSON and does not rerun that producer. A formal
Core run instead emits schema-4 professionalism JSON and Markdown into
`.rd-skills/formal-release/<captured-head>/reports/`; authoring refreshes only
the tracked JSON, while formal intermediate producers and consumers use only
the sibling `producer-reports/` staging directory. No gate consumes Markdown as
readiness authority.

Schema-4 professionalism JSON adds `expert_panel_release_manifest` inside that
same authority. Ordinary authoring records only `not-evaluated`, `missing`,
`stale`, or `pending`; formal Core records `current` only for exactly the three
canonical accepted attestations when their bytes equal `HEAD`, their paths are
clean, and the manifest commit equals the current commit. The external hashes
and sizes are downstream release identity and are excluded from every panel
source and review-contract fingerprint. Legacy schema-3 saved reports remain
readable only as non-formal productization evidence.

Root and Reference detectors, disposition application, readability schema 2, and
Professional Completeness schema 3 are defined only in [Skill content
governance](SKILL_CONTENT_GOVERNANCE.md#validation). Validation operators use
their strict commands and reported blockers; this document does not redefine
packet, ballot, reviewer-assignment, carry, storage, or cost semantics.
Current Professional evidence uses the v3 review/carry contract: packets bind
one package material and one review unit per target, compact storage
deduplicates dependency materials in one catalog, and each finding names only
its dependency IDs. Package/source/review-binding aliases and earlier
Professional contract fingerprints are historical-only and never satisfy
currentness, carry, promotion, or Formal Release.
The Professional compact schema-2 file also has one physical
`professional-string-catalog-v1` encoding. Its routing fields stay literal;
all other repeated string values use canonical catalog references. The owner
decoder expands that representation before the unchanged semantic/currentness
validator and requires byte-stable reprojection. Bare current schema-2 JSON,
noncanonical or unused catalog entries, and changed references are invalid, not
stale compatibility inputs. This physical encoding is outside the Professional
review-contract projection; promotion still authenticates it by exact decision
reprojection and the fixed artifact is externally anchored by its tracked
SHA-256 and clean `HEAD` bytes.
For Professional fresh evidence, `origin_commit` is the clean stable `HEAD`
used for decision and current-binding reprojection. A repository at commit `C`
reattests and performs exact promotion validation at the same `C`; the later
commit that records the fixed artifact may be `P` while the authenticated
origin remains `C`. Currentness and Formal Release validate that preserved
origin authority and do not require `origin_commit == P`.

The Phase 2 inventory is current and final, so the formal target is all 189
non-Control packages. The tracked Expert Panel inventory is exactly
`evals/expert-panel/readability.json`,
`evals/expert-panel/semantic-disposition.json`, and
`evals/expert-panel/professional-completeness.json`. Each path contains one
current compact attestation and is replaced rather than appended. Full runtime
packets, templates, ballots, capsules, and decisions remain only under the
ignored `.rd-skills/expert-panel/<run-id>/` or an optional CI/Release artifact.
Canonical fixed-attestation paths, not Readability or Professional policy
config, select Expert Panel evidence; the formal target remains all 189
non-Control packages. A current Semantic Disposition application binds the
exact fixed-attestation bytes. Replace an attestation only when its strict
current validator reports source, detector, binding, or contract drift, then
rerun the Core formal gate. These fixed attestations do not prove that the final
local formal gate passed.

Readability compact schema 2 uses the manifest-v2 digest as its sole source
authority and one review-unit-binding-v3 digest per minimum target or finding
unit. Unit bindings cover identity and local manifest authority, never votes or
outcomes. `review_artifacts` retains the packet, three voter-keyed ballots, and
decision content SHA-256 values. Generation and promotion authenticate
conclusions by exact decision reprojection; direct parsing is not a replacement
for that artifact check. Once promoted, clean `HEAD` bytes and the formal release
manifest content SHA-256 provide the external anchor. Evidence created under a
prior Readability currentness, manifest, or unit-binding contract is stale and
requires a fresh review even though the compact schema number remains 2.

For a host-local comparison of complete fixed-storage currentness, run
`python3 tests/scripts/expert_panel_storage_benchmark.py --warmups 2
--repetitions 9` from each revision. The harness creates a temporary Git
repository and asserts current, stale, and tampered native compact-schema
controls before timing only the complete current path through
`_validate_current_expert_panel_storage(formal=False)`. Compare medians on the
same host. Schema revisions use different serialized bytes and may have
different target sets, so the result compares equivalent trust checks rather
than identical inputs and does not prove CI or production latency. Deterministic
single-build counters, not elapsed time, are the CI regression gate.

## Generated Freshness and Safety

- Run validation after the latest material edit and against one identified tree.
- Governed documentation binds managed sections, markers, paths, and rendered
  content to their owners. Ordinary prose outside those sections does not carry
  a whole-document digest and can change without cascading contract hashes.
- Prefer generator check mode when available. A stale or missing generated
  artifact is a failure, not permission to hand-edit status.
- Snapshot tracked, staged, and untracked paths around a check that may write.
  Stop on an unexpected mutation and identify its producer.
- A tracked generated artifact must be byte-equal to fresh canonical output.
  Passing content copied from another tree is not current evidence.
- Do not hide input-tree changes, preserve stale pass labels, or replace a
  requested command with a narrower diagnostic.
- Evidence artifacts follow the privacy and retention rules in [Quality
  Model](QUALITY_MODEL.md) and [Benchmarks](BENCHMARKS.md).

## Evidence Limits

Static checks prove declared structure. Deterministic and captured fixtures prove
their bounded fixture contracts. Code-generation defaults prove definition,
harness, and incomplete-starter rejection, not a generated candidate. Builds,
packages, quickstart dry runs, and simulated installation do not prove host
startup, host-enforced permissions, wall-clock performance, production
accuracy, provider behavior, or installed user experience.

Rendered-context evaluation counts deterministic built instruction surfaces and
fixture capsules. It excludes host system prompts, tool schemas, conversation
history, repository reads, diffs, dynamic command output, and unobserved host
injection. It is an instruction-envelope check, not an observed total request or
runtime trace.

Record every skipped or unavailable check, affected scope, proof limit, and
residual risk. A failed command remains failed until its cause is verified and
the relevant command passes after the final fix.

Run Calibration to a temporary report directory before canonical Conformance:

```bash
python3 scripts/eval-rendered-context-budget.py --mode calibration --reports-dir /private/tmp/rd-skills-budget-calibration
python3 scripts/eval-rendered-context-budget.py --mode conformance
```

Calibration measures the otherwise-valid population without using budget for
selection, frontier construction, rejection, or exit. Conformance applies the
Core-derived hard ceiling after complete context measurement and records soft
growth advisories separately.

## Rendered Context Budget Contract

<!-- BEGIN CHANGEFORGE CONTEXT BUDGET PROJECTION: validation-rendered-context-budget -->
Source: `src/control-model/core-contracts.json#/context_budget_contract`.

Budget taxonomy and all Runtime/Rendered limits are owned only by Core. Budget is a cost guardrail and never changes routing, required context, or correctness obligations.

Authoring Budget classes: Main Prompt, Control Skill, Professional Skill, Foundation, Domain.
Resident Runtime Budget classes: Main always-loaded.
Dispatch Composition Budget classes: Direct Task, Analyzed Task, Analysis, Review, Utility.
Runtime Dynamic Context classes: Repository Reads, Diff, Command Output, Tool System Prompt, Conversation History; observation-only, with host conversation compaction out of scope.

| Category | Context | Soft target | Hard ceiling | Calibration status |
| --- | --- | ---: | ---: | --- |
| Resident Runtime Budget | Main always-loaded | 2305 | 2650 | provisional-migration-value |
| Dispatch Composition Budget | Direct Task dispatch | 3000 | 3200 | provisional-migration-value |
| Dispatch Composition Budget | Analyzed Task dispatch | 6000 | 6500 | provisional-migration-value |
| Dispatch Composition Budget | Analysis dispatch | 4500 | 5000 | provisional-migration-value |
| Dispatch Composition Budget | Review dispatch | 3700 | 4000 | provisional-migration-value |
| Dispatch Composition Budget | Utility dispatch | 2000 | 2500 | provisional-migration-value |

Soft-target overage is a growth advisory; hard-ceiling overage fails Conformance. Calibration does not apply either limit to candidate selection or exit.
Required routing, Professional, Domain, Layer 3, Reference, Review, and Evidence context is never truncated to satisfy a budget.

Tokenizer: `o200k_base`. Exact duplicate-rule ratio gate: `0.03`.
<!-- END CHANGEFORGE CONTEXT BUDGET PROJECTION: validation-rendered-context-budget -->

## Release Gate

Ordinary committed development requires the Development Affected commands for
the selected base and head. Integration and release-candidate decisions require
the local Full Regression on the same final material tree. Formal release
additionally requires the single complete formal command above, current Root
and expert-review evidence under [Skill content
governance](SKILL_CONTENT_GOVERNANCE.md), and clean tracked evidence.
`authoring_gate=current-contract-pass` alone is not release readiness.

Use [Release](RELEASE.md) for lifecycle ordering, package commands, stop and
rollback conditions, derived-readiness handling, and the release checklist.

## Diagnostic Appendix

Run a producer below only to isolate a verified gate failure:

```bash
python3 scripts/validate-skills.py
python3 scripts/validate-capabilities.py
python3 scripts/validate-domain-extensions.py
python3 scripts/validate-registry.py
python3 scripts/validate-control-skills.py
python3 scripts/validate-control-plane-prompt.py
python3 scripts/validate-task-contracts.py
python3 scripts/validate-skill-routing.py
python3 scripts/validate-hookless-residue.py
python3 scripts/validate-src-invariants.py
python3 scripts/validate-skill-body-links.py
python3 scripts/validate-skill-content-size.py
python3 scripts/audit-skill-content.py --gate authoring
python3 scripts/validate-reference-content.py --strict
python3 scripts/validate-root-content.py --strict
python3 scripts/build.py --profile recommended
python3 scripts/build.py --profile full
python3 scripts/build.py --profile dev
python3 scripts/validate-agent-profiles.py
python3 scripts/validate-docs-consistency.py
python3 scripts/validate-built-skill-reference-links.py
python3 scripts/validate-installation.py
python3 scripts/eval-routing.py
python3 scripts/eval-skill-professionalism.py
python3 scripts/eval-professional-benchmarks.py
python3 scripts/validate-professional-routing-coverage.py
python3 scripts/eval-agent-lightweight.py
python3 scripts/eval-rendered-context-budget.py --mode conformance
python3 scripts/eval-context-control-plane.py
python3 scripts/eval-agent-behavior.py --format json --output-dir evals/agent-behavior/outputs
python3 scripts/eval-professional-agent-samples.py --promoted-only --strict
python3 scripts/eval-pressure-behavior.py --format json --output-dir evals/pressure/outputs
python3 scripts/validate-professionalism-regression.py --strict --report-only
```

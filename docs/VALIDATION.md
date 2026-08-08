# Validation

Every completion or release claim needs evidence from the final material edit.
Generated reports are derived evidence only when their producer ran against the
same current tree.

## Gate Paths

Run the ordinary authoring gate:

```bash
python3 scripts/eval-core-principles.py --gate authoring
```

Formal local evaluation requires both commands on the same final tree:

```bash
python3 scripts/eval-core-principles.py --gate formal-release
python3 scripts/validate-professionalism-regression.py --strict --require-expert-content-review
```

Both formal commands are mandatory. The Core evaluator loads
`src/control-model/core-contracts.json`; its selected gate changes exit policy,
not report content. The remote `Formal Release` workflow is separate evidence
and must pass for the same object ID as the locally validated final tree.

## Required Repository Execution

After the authoring gate, run this repository command set in order:

```bash
python3 scripts/validate-examples.py
python3 scripts/generate-examples-showcase.py --out docs/SHOWCASE.md --check
python3 scripts/generate-marketplace-catalog.py --profile recommended --out docs/MARKETPLACE_CATALOG.md --check
python3 scripts/validate-marketplace-index.py --profile recommended
python3 scripts/validate-marketplace-index.py --profile full
python3 scripts/validate-marketplace-index.py --profile dev
python3 scripts/validate-productization-assets.py
python3 scripts/validate-open-source-readiness.py --require-pass
python3 -m unittest discover -s tests
python3 scripts/validate-codegen-benchmarks.py
python3 scripts/run-codegen-benchmarks.py --limit 3
python3 scripts/quickstart.py --agent codex --scope user --dry-run
python3 scripts/quickstart.py --agent claude --scope project --target /tmp/changeforge-quickstart-claude --dry-run
python3 scripts/quickstart.py --agent copilot --scope project --target /tmp/changeforge-quickstart-copilot --dry-run
python3 scripts/quickstart.py --agent openai-api --dry-run
```

Ordinary pull-request CI runs the authoring path. Formal remote evidence comes
from `.github/workflows/formal-release.yml`, triggered manually or by a
`v*` tag. It adds the formal gate, independent expert-review gate, repository
execution set, and final generated-artifact diff check.

CI installs the project and declared dependencies from a `git archive` in a
temporary directory. Packaging metadata such as `*.egg-info` must not appear
in or be hidden from the validation checkout.

## Signal Ownership

| Signal | Canonical authority | Passing signal |
| --- | --- | --- |
| Core Principles | `src/control-model/core-contracts.json` and `eval-core-principles.py` | Selected gate passes with all required producer outcomes current. |
| Root, Reference, and expert-review lifecycle | [Skill content governance](SKILL_CONTENT_GOVERNANCE.md) | Strict source validators and required independent decisions are current; no blocking disposition remains. |
| Documentation | `validate-docs-consistency.py` and local-link checks | Required docs, Core projections, commands, links, and whole-document digests match current source. |
| Routing and professional quality | Registries, deterministic fixtures, and professionalism producers | Fresh actual routes cover 233 canonical entries and 62 capability entries. The 429 admissions are 105 Professional, 276 Foundation, and 48 Domain. The Foundation projection covers 141 unique Foundation Skills in the 163-entry Layer 3 catalog. Required coverage and professional obligations pass without forbidden behavior. |
| Capability coverage | `evals/capability-coverage/matrix.yaml` and deterministic coverage validators | All 125 entries classify as 81 covered, 39 partial, 0 missing, and 5 intentionally unsupported; covered means catalog/routing evidence, not Professional Completeness. |
| Build and installation | [Build profiles](BUILD_PROFILES.md) and [Installation](INSTALLATION.md) | Profiles contain 27, 40, and 190 top-level Skills; supported hosts include four Profiles; manifests and doctor checks match. |
| Code generation | [Benchmarks](BENCHMARKS.md) | Definitions, harnesses, and starter negative controls pass; candidate claims require an explicit candidate input. |
| Open-source publication | [Open-source readiness](OPEN_SOURCE_READINESS.md) | Root license, metadata, contribution, security, and publication checks pass together. |

`eval-core-principles.py` is the only complete orchestrator for its declared
producer graph. Individual producer commands diagnose a verified failure; their
aggregate manual success is not a substitute for orchestrator ordering,
timeouts, freshness, input-tree checks, and outcome evaluation.

Root and Reference detectors, disposition lifecycle, readability schema 2, and
Professional Completeness schema 3 are defined only in [Skill content
governance](SKILL_CONTENT_GOVERNANCE.md#validation). Validation operators use
their strict commands and reported blockers; this document does not redefine
packet, ballot, reviewer-assignment, carry, storage, or cost semantics.

The Phase 2 inventory is current and final, so the formal target is all 189
non-Control packages. Current static evidence selectors are r25 Readability,
r26 Semantic Disposition, r26 Root lifecycle, and r18 schema-3 Professional
Completeness for all 189 non-Control packages. These static selectors do not
prove that the final formal gates or same-commit remote workflow passed.

## Generated Freshness and Safety

- Run validation after the latest material edit and against one identified tree.
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

## Rendered Context Budget Contract

<!-- BEGIN CHANGEFORGE CONTEXT BUDGET PROJECTION: validation-rendered-context-budget -->
Source: `src/control-model/core-contracts.json#/context_budget_contract`.

`required reserve = ceil(capacity ceiling * minimum headroom ratio)`; `release target = capacity ceiling - required reserve`; `evolution target = release target - minimum release margin`.
Release and evolution targets are derived and are not stored as second authorities.

| Context | Capacity ceiling | Minimum headroom ratio | Required reserve | Release target | Minimum release margin | Evolution target |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Main always-loaded | 2200 | 0.10 | 220 | 1980 | 80 | 1900 |
| Direct Task dispatch | 3200 | 0.00 | 0 | 3200 | 0 | 3200 |
| Analyzed Task dispatch | 6500 | 0.00 | 0 | 6500 | 0 | 6500 |
| Analysis dispatch | 5000 | 0.00 | 0 | 5000 | 0 | 5000 |
| Review dispatch | 4000 | 0.00 | 0 | 4000 | 0 | 4000 |
| Utility dispatch | 2500 | 0.00 | 0 | 2500 | 0 | 2500 |

Tokenizer: `o200k_base`. Exact duplicate-rule ratio gate: `0.03`.
<!-- END CHANGEFORGE CONTEXT BUDGET PROJECTION: validation-rendered-context-budget -->

## Release Gate

An ordinary authoring decision requires the authoring evaluator and the complete
repository execution set on the same final tree. Formal release additionally
requires both mandatory formal commands above, current Root and expert-review
evidence under [Skill content governance](SKILL_CONTENT_GOVERNANCE.md), clean
tracked evidence, and the remote `Formal Release` workflow for the same object
ID.
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
python3 scripts/eval-rendered-context-budget.py
python3 scripts/eval-context-control-plane.py
python3 scripts/eval-agent-behavior.py --format json --output-dir evals/agent-behavior/outputs
python3 scripts/eval-professional-agent-samples.py --promoted-only --strict
python3 scripts/eval-pressure-behavior.py --format json --output-dir evals/pressure/outputs
python3 scripts/validate-professionalism-regression.py --strict --report-only
```

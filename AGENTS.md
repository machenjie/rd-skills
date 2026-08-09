# Agent Instructions

Codex must treat this repository as a ChangeForge Skill-authoring repository.

## Repository Purpose

This repository exists only to author, validate, build, package, install, upgrade, and uninstall ChangeForge Skills and Agent Profile artifacts. It is not a runtime user-specific content corpus and must not become one.

## Non-Negotiable Boundaries

- Do not add personal asset ingestion, scanning, indexing, summarization, mapping, packaging, or installation.
- Do not add toolbox mappings for user-specific technical archives.
- Do not assume a user-specific content corpus is available.
- Do not install `src/` or source registries directly.
- Do not add executable interception, an internal task state engine, private evidence storage, hidden Skill packaging, or a second workspace/sandbox manager.
- Keep the product architecture limited to the control prompt, four Agent Profiles, and three Skill layers.

## Change Discipline

Ordinary development uses the affected graph against one selected base and
head commit. The head checkout must be clean because the Core affected runner
executes only tracked files from that commit:

```text
python3 scripts/eval-core-principles.py --gate affected --base <base> --head <head>
python3 scripts/run-ci-tests.py run --base <base> --head <head>
```

Pull-request CI applies those two selectors in one unsharded `pr-ci` job. It is
pull-request-only and does not run the full repository regression set.

Run the local Full Regression once on the final material tree before an
integration handoff or release-candidate decision. Core authoring is the single
owner of its deterministic producer graph; the commands after it are consumers
or non-Core checks and must not replay Core-owned producers:

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
python3 -m unittest discover -s tests
python3 scripts/validate-codegen-benchmarks.py
python3 scripts/run-codegen-benchmarks.py --limit 3
python3 scripts/quickstart.py --agent codex --scope user --dry-run
python3 scripts/quickstart.py --agent claude --scope project --target /tmp/changeforge-quickstart-claude --dry-run
python3 scripts/quickstart.py --agent copilot --scope project --target /tmp/changeforge-quickstart-copilot --dry-run
python3 scripts/quickstart.py --agent openai-api --dry-run
```

Formal Release is independent from Development Affected and local Full
Regression. It requires the single Core command below on one clean final commit.
The independent `.github/workflows/formal-release.yml` workflow is remote
release evidence for that same object ID; it is not part of pull-request CI.

```bash
python3 scripts/eval-core-principles.py --gate formal-release
```

Core is the only complete formal orchestrator. It runs
`scripts/validate-professionalism-regression.py` once through its declared
producer graph and requires the aggregate
`professionalism-formal-release-ready` outcome, including
`release_gate=release-ready`. Run that producer directly only to diagnose a
verified Core failure; a second direct pass is not additional release evidence.

Release evidence is limited to static contracts, deterministic fixtures,
code-generation definitions and harness/negative-control checks, builds, and
simulated installation. It does not prove real-host Profile startup, wall-clock
performance, production accuracy, provider behavior, or the installed user
experience. State those limits in every release handoff.

If an affected selector or Full Regression command is intentionally replaced,
update this command discipline, `docs/VALIDATION.md`, the owning Core impact
graph, and the applicable workflow in the same change. Do not report success
from a stale generated report.

`scripts/audit-skill-content.py` is the single source collector for root Skill
content and indexed/physical Reference content. The required strict
`validate-reference-content.py` run reuses that collector, writes no report, and
gates every indexed Reference's effective type, load, and do-not-load contract.

## Built Content Rules

The source inventory is 1 Control, 26 Professional, 150 Foundation, and 13
Domain Skills: 190 total and 189 non-Control. Built Skills must be emitted into
`dist/`, and every installed Skill folder must contain `SKILL.md` at its root.
The `recommended`, `full`, and `dev` builds contain 27, 40, and 190 top-level
Skills respectively. Their delivery modes are 154/9, 141/9, and 0/0 targeted
companions/routing-only entries. All supported Codex, Claude, and Copilot
builds contain the four static Agent Profiles.

Foundation and Domain guidance is compiled into Professional Skill `references/` only when the Professional registry names it. The development build additionally exposes Layer 3 Skills for authoring. `references/` is loaded selectively; it is not a catalog to read in full.

## Agent Execution Discipline

Every agent-assisted change must obey these rules:

1. No evidence, no completion.
2. No verified cause, no diagnosis.
3. No repeated same-path retry after two failures.
4. No local fix without a same-pattern scan.
5. No new structure without reuse and placement rationale.
6. No handoff without risk, boundary, and validation results.

AI-readability and professional-completeness use separate schema-5
attestations. Readability uses schema-2 panel artifacts and exactly
three independent senior-agent reviewers with distinct voter, agent, and role
identities; every reviewer covers every target and cannot abstain. Retain its
immutable packet, three canonical ballots, and derived two-of-three decision
record. The schema-2 packet binds every advisory sentence to an independently
re-extracted logical document part, closed source selector, exact codepoint
span, and canonical sentence fingerprint. Each ballot decides every finding;
the reviewer supplies no document override. Any nested tightening derives that
reviewer's document disposition before the document majority. Professional
completeness formal evidence uses schema-3 incremental
artifacts. Its machine-derived review plan carries only an exactly unchanged
review-visible package binding from a direct depth-zero fresh origin; changed
packages and their affected dependencies receive fresh target-scoped capsules
and ballots. A fresh round uses a reviewer pool with unique voter and agent
identities. Each fresh ballot covers a non-empty assigned Skill subset, and
every fresh Skill receives exactly three independent votes: two domain
reviewers whose closed-set expertise tags cover that Skill and one reviewer
whose only panel expertise tag is `skill-reference-architecture`. An all-carry
round uses zero fresh reviewers, ballots, capsules, and input bytes. The
effective decision still contains three votes per Skill, with carried evidence
bound to its direct fresh-origin decision, packet, ballots, and capsules. The
aggregator derives fresh assignments from capsule-bound ballot subsets; the
packet does not contain reviewer pre-assignment. Maintainers do not select or
override dispositions. Readability also covers every weak
front-loaded-action target and formal release requires zero
`tracked-tightening`, unresolved `detector-false-positive`, and
`rewrite-required` decisions. Professional completeness decides each of its
four ordinary criteria independently by two-of-three criterion majority; the
overall ballot majority is audit-only. Any qualified domain
reviewer's defect on professional correctness, erroneous rules, material
omissions, failure modes, boundary conditions, or verification methods becomes
`unresolved-professional-disagreement`; schema 3 has no arbitration or
override. Its evidence binds
criterion-specific source anchors, examined failure and omission candidates,
independently ranked adjacent candidates, and proof limits. Schema-3 claims
also quote contiguous non-generic source phrases: each non-defect criterion,
failure, and omission assertion needs an anchor-local bigram, and each
non-defect adjacency rationale needs one from each package. The schema-3-only
phrase matcher cannot bridge generic tokens, lines, or anchors. Relaxed defect
and uniform-template guards are fingerprinted review contracts;
schema 1 and schema 2 semantics remain unchanged. Formal release also
requires all 189 non-Control Skill packages to be accepted with zero
professional corrections and zero unresolved professional disagreements.
Qualification claims are static declarations and do not prove reviewer identity,
credentials, or experience. Professional schema 1 and schema 2 remain
auditable but cannot satisfy formal release or authorize carry. The checked-in
schema-3 rounds form one unforked chain whose selected decision is the unique
head; direct-origin evidence, the full round chain, and the current artifacts
must be tracked, byte-equal to `HEAD`, and clean. Plan lineage is capped at
eight rounds before a full-fresh checkpoint. A review-contract change forces
all 189 packages fresh; a local binding change reopens only the package and its
machine-derived affected dependencies.

The Phase 2 inventory is the current and final inventory. Selected r26
Readability is immutable historical evidence, but its Skill detector binding is
stale against the current detector. It has `source_current=false`, status
`panel-majority-stale`, remains storage-pending, and is not accepted for formal
release. Formal Release requires a new current schema-2 Readability review under
the current Skill detector. Selected r19 schema-3 Professional Completeness is
immutable historical full-fresh evidence for all 189 non-Control packages, but
its bound Professional review contract is stale against the current contract.
It remains storage-pending and is not accepted for formal release. Because a
review-contract change forces every package fresh, Formal Release must create a
new schema-3 full-fresh round for all 189 current non-Control packages; r19
cannot authorize carry. The selected Semantic Disposition application is
invalid against the current audit and the Root lifecycle is `pending-changes`;
formal release remains blocked until those bindings are current and the
final-tree Core formal gate plus same-commit remote workflow pass.

Use the four Profile boundaries defined in `src/agent-profiles/role-agents.json`. The main agent dispatches only; analysis reads and searches; task agents implement bounded work; review agents perform independent non-modifying review. Shared-workspace writes are serial unless the host supplies isolated workspaces and the tasks have no dependency or shared write surface.

Do not add entertainment rhetoric, corporate-flavor narration, user-shaming language, private prompts, secrets, full command logs, personal archives, or user-specific mappings to generated artifacts.

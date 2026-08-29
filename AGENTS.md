# Agent Instructions

Codex must treat this repository as a rd-skills Skill-authoring repository.

## Repository Purpose

This repository exists only to author, validate, build, package, install, upgrade, and uninstall rd-skills Skills and Agent Profile artifacts. It is not a runtime user-specific content corpus and must not become one.

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

These two local selectors remain the complete Development Affected command
surface; they do not run the full repository regression set.

Run the local Full Regression once on the final material tree before an
integration handoff or release-candidate decision. Core authoring is the single
owner of its deterministic producer graph; the commands after it are consumers
or non-Core checks and must not replay Core-owned producers:

```bash
python3 scripts/eval-core-principles.py --gate authoring
python3 scripts/validate-examples.py
python3 scripts/generate-examples-showcase.py --out docs/SHOWCASE.md --check
python3 scripts/generate-marketplace-catalog.py --out docs/MARKETPLACE_CATALOG.md --check
python3 scripts/validate-marketplace-index.py
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

Formal Release is independent from Development Affected and local Full
Regression. It requires the single Core command below on one clean final commit.

```bash
python3 scripts/eval-core-principles.py --gate formal-release
```

Core is the only complete formal orchestrator. It runs
`scripts/validate-professionalism-regression.py` once through its declared
producer graph and requires the aggregate
`professionalism-formal-release-ready` outcome, including
`release_gate=release-ready`. Run that producer directly only to diagnose a
verified Core failure; a second direct pass is not additional release evidence.
The formal professionalism JSON embeds the downstream
`expert_panel_release_manifest`: the current commit plus external SHA-256,
size, review ID, verdict, and axis for exactly the three canonical fixed
attestations. The manifest is not a fourth tracked panel artifact and never
feeds Readability, Semantic Disposition, or Professional Completeness
fingerprints or currentness. Authoring reports only a non-blocking manifest
state; formal release requires current, accepted, clean, `HEAD`-equal artifacts
and Core verifies that the manifest commit equals the captured input `HEAD`.
Tracked Core and professionalism JSON reports are ordinary authoring
projections only. Formal Core writes both schema-4 JSON outcomes and their
Markdown projections to
`.rd-skills/formal-release/<captured-head>/reports/`; that directory is ignored,
bound to the captured input `HEAD`, validated locally, and contains exactly
those four canonical files. Every declared
intermediate report producer and consumer in the formal graph uses the sibling
`.rd-skills/formal-release/<captured-head>/producer-reports/` staging directory;
the formal run never reads or refreshes tracked `reports/` projections and must
leave the tracked tree clean.

Release evidence is limited to static contracts, deterministic fixtures,
code-generation definitions and harness/negative-control checks, builds, and
simulated installation. It does not prove real-host Profile startup, wall-clock
performance, production accuracy, provider behavior, or the installed user
experience. State those limits in every release handoff.

If an affected selector or Full Regression command is intentionally replaced,
update this command discipline, `docs/VALIDATION.md`, the owning Core impact
graph, and the applicable local command owner in the same change. Do not report
success from a stale generated report.

`scripts/audit-skill-content.py` is the single source collector for root Skill
content and indexed/physical Reference content. The required strict
`validate-reference-content.py` run reuses that collector, writes no report, and
gates every indexed Reference's effective type, load, and do-not-load contract.

## Built Content Rules

The source inventory is 1 Control, 26 Professional, 150 Foundation, and 13
Domain Skills: 190 total and 189 non-Control. Built Skills must be emitted into
`dist/`, and every installed Skill folder must contain `SKILL.md` at its root.
The single Runtime exposes 27 top-level Skills: 1 Control and 26 Professional.
Its delivery is 27/154/9 top-level/targeted/routing-only. The internal
`recommended` directory and manifest identity is retained only for
compatibility; `full` and `dev` are retired build, install, package, doctor, and
discovery surfaces. All supported Codex, Claude, and Copilot builds contain the
four static Agent Profiles; Runtime is not an Agent Profile dimension.

Foundation is a capability-modifier layer and Domain is `modifier-only`.
Neither may become a Runtime top-level Skill. Runtime selection remains Primary
Professional -> selector -> 0..3 Layer 3 -> required References. Task and Review
consume Main's Route Once result, do not rerun global routing, and load only
capsule-named Layer 3 and necessary Targeted References. Never load the complete
Foundation/Domain catalog.

Retiring the development Runtime does not retire its validation obligations.
Source/registry/selector/projection/nested-link completeness, routing and
context-budget regression, and expanded all-163 Layer 3 stress validation run
through internal validators and tests. Any complete Layer 3 projection must be
created only in cleaned temporary storage outside the repository, `dist/`,
installation packages, and Host discovery.

New knowledge is placed in this order: Targeted Reference, existing
Foundation/Domain, existing Professional, then new Professional. A framework,
library, protocol, platform sub-capability, scenario, or gotcha does not justify
a top-level Skill. Add a Professional Skill only for a stable independent
Primary Route with clear task ownership.

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
record for the duration of the review. The schema-2 packet binds every advisory
sentence to an independently
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
bound to the direct fresh origin recorded in the current attestation as its
origin review id, origin commit, origin verdict digest, and source fingerprint;
carry validation must not require a predecessor review file in `HEAD`. The
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
auditable but cannot satisfy formal release or authorize carry. After the
storage migration, the repository must track exactly one compact current
attestation for each panel at
`evals/expert-panel/readability.json`,
`evals/expert-panel/semantic-disposition.json`, and
`evals/expert-panel/professional-completeness.json`; a completed review replaces
the same panel's previous attestation. Full packets, ballots, capsules, temporary
decisions, and other regenerable review context remain only in the gitignored
`.rd-skills/expert-panel/<run-id>/` runtime directory or, when a complete release
audit scene is required, in a CI/Release artifact. They must not be tracked.
Current attestations retain only the verdict, findings, rationale, source and
review-contract fingerprints, reviewer/provenance metadata, and the compact
vote and criterion results needed to enforce the review contract. They must be
self-contained. Ordinary affected and authoring validation classifies a
well-formed fixed axis as `missing`, `stale`, or `pending` without treating it as
current or letting it authorize carry; malformed or unsafe evidence still fails
every mode.
Formal Release additionally requires every fixed attestation to be byte-equal to
`HEAD` and clean; Git history is the audit trail for replaced attestations.
Runtime plan lineage is capped at eight rounds before a full-fresh checkpoint. A
review-contract change forces all 189 packages fresh; a local binding change
reopens only the package and its machine-derived affected dependencies.

The Phase 2 inventory is the current and final inventory. Formal Release requires
each canonical fixed attestation to be current to its selected sources and
review contracts, byte-equal to `HEAD`, and clean. Stale evidence cannot satisfy
Formal Release and must be replaced in place after a fresh review. The
final-tree Core formal gate must pass.

Use the four Profile boundaries defined in `src/agent-profiles/role-agents.json`. The main agent dispatches only; analysis reads and searches; task agents implement bounded work; review agents perform independent non-modifying review. Shared-workspace writes are serial unless the host supplies isolated workspaces and the tasks have no dependency or shared write surface.

Do not add entertainment rhetoric, corporate-flavor narration, user-shaming language, private prompts, secrets, full command logs, personal archives, or user-specific mappings to generated artifacts.

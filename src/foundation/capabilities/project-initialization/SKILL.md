---
name: project-initialization
description: "`analysis-agent`/`task-agent`/`review-agent`: use for structure, workspace or package bootstrap, config, scripts, or quality gates; skip without an initialization decision."
---

# project-initialization

## Registry Trigger

**Use when**

- new repository or workspace needs initial ownership boundaries, source and generated layout, bootstrap commands, config surfaces, and clean-checkout proof

**Do not use when**

- existing repository structure and initialization contract are unchanged

## Skill Role

Define the initial repository scaffold, bootstrap contract, source/generated authority, clean-checkout behavior, and residual setup limits. Exclude architecture, dependency policy, runtime configuration, and pipeline enforcement.

## High-Value Rules

- Derive the scaffold from accepted product, runtime, deployment, ownership, and consumer boundaries.
- Do not import a template structure whose assumptions remain unverified.
- For affected authored or generated surfaces, identify source authority and committed-or-derived policy; add an explicit owner or dependency direction where ambiguity can change generation, cleanup, or delivery.
- Prove bootstrap from a clean checkout without ambient caches, unrecorded global tools, generated leftovers, local credentials, or oral setup knowledge. The documented failure path names required external services and their absence.
- Define toolchain and package-manager identity, lockfile ownership, workspace roots, entry points, and local/CI command parity without prescribing one runner or folder catalog. Hand dependency policy to `package-dependency-management` and vulnerability acceptance to `dependency-vulnerability-scanning`.
- Use non-secret placeholders and startup validation while leaving secret lifecycle and behavior-changing configuration policy to their owning Skills.
- Create boundaries for current owners and consumers without speculative directories, generic utility buckets, copied examples, or disposable abstractions.
- Treat setup documentation as a claim to verify. Run the relevant setup, build, test, lint, generated-drift, and secret checks after the final scaffold change and state what local proof cannot establish.

## Anti-Patterns

- An empty directory tree or familiar framework layout is not evidence that ownership, dependency direction, or generated-source policy is correct.
- A README command that was not run, or only works in a prepared workstation, is not clean-checkout evidence.
- `.gitignore` reduces accidental additions but does not revoke a committed secret or prove generated and sensitive files cannot enter source control.

## Stop Conditions

- Escalate unresolved service or module ownership, extraction from a live system, public package/SDK commitments, regulated-data boundaries, or bootstrap that requires production credentials or destructive external setup.
- Stop initialization closure when the clean-checkout environment, source-of-truth commands, generated policy, or residual unverified scope is unknown.

## Output Contract

- Return an initialization decision: define boundaries, source/generated policy, toolchain, workspace configuration, bootstrap, clean-checkout proof, and residual risk

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [checklist](references/checklist.md) | decision-checklist | new scaffold needs ownership config generated-output and command boundaries | existing repository initialization contract remains unchanged | task-agent, review-agent, analysis-agent | checklist-result, residual-risk |
| [clean checkout](references/clean-checkout.md) | evidence-pattern | closure claims bootstrap build or tests are independent of ambient workstation state | no clean-checkout or initialization reproducibility claim is made | task-agent, review-agent, analysis-agent | evidence-record, proof-limit, residual-risk |
| [evidence patterns](references/evidence-patterns.md) | evidence-pattern | structure secret generated package-manager handoff or clean-checkout claims need fresh proof | no initialization claim awaits validation | task-agent, review-agent, analysis-agent | evidence-record, proof-limit, residual-risk |

# Quality Model

ChangeForge skills must encode expert-grade engineering judgment. Each change receives a quality level from L1 through L5 based on blast radius, contract surface, data sensitivity, reversibility, and production risk.

## L1 Isolated Local Change

Scope: one isolated edit with no shared contract change, no persistence change, no external side effect, and no rollout dependency.

Reference loading: `SKILL.md` is loaded for the selected skill, but references are not read unless the task touches security, data, auth, external integration, performance, release, or irreversible behavior.

Required gates:

- Validate the touched skill, doc, script, or generated artifact locally.
- Run the narrow validator or syntax check that covers the touched file.
- Confirm no personal asset mapping, toolbox path, raw `src/registry`, or raw `src/` runtime content was introduced.

Required evidence:

- Command output for the narrow check.
- Changed file list.
- Completion criteria and skipped checks, if any.

## L2 Single-Module Change

Scope: one skill, validator, installer flow, registry file, or build path with limited callers and no cross-runtime contract change.

Reference loading: read `references/capabilities/index.md` and only capability files explicitly selected by `change-forge-router`.

Required gates:

- Pass L1.
- Run the module's direct validator, dry run, or command path.
- Review input validation, error messages, output contracts, and backward compatibility.
- Identify rollback steps when generated artifacts or installer behavior changes.

Required evidence:

- Direct validator or dry-run output.
- Compatibility note for fields, paths, profile behavior, or CLI flags.
- Rollback or recovery note.

## L3 Multi-Module Product Change

Scope: coordinated changes across validators, registries, build/package/install scripts, docs, or generated runtime artifacts.

Reference loading: read all selected capability references and `references/checklist.md` when present.

Required gates:

- Pass L2 for each touched module.
- Run all core validators:

```bash
python3 scripts/validate-skills.py
python3 scripts/validate-capabilities.py
python3 scripts/validate-registry.py
python3 scripts/eval-routing.py
python3 scripts/validate-codegen-benchmarks.py
python3 scripts/validate-installation.py
```

- Rebuild affected profiles and run relevant package, install, upgrade, uninstall, or doctor flows.
- Verify registry references resolve across professional skills, capabilities, domain extensions, and routing rules.
- Verify every runtime skill has a root `SKILL.md`.

Required evidence:

- Core validator output.
- Build output for affected profiles.
- Installer or packaging dry-run output when behavior changed.
- Profile count summary.

## L4 Product-Grade High-Risk Change

Scope: changes that alter public contracts, installation behavior, packaging semantics, runtime profile behavior, routing decisions, cross-agent compatibility, or release procedure.

Reference loading: read all selected capability references, `references/checklist.md` when present, and domain extension references when selected.

Required gates:

- Pass L3.
- Add or update regression checks for representative valid and invalid inputs.
- Verify deterministic output paths, archive structure, manifest contents, profile-specific runtime content, and duplicate conflict handling.
- Review failure modes for partial builds, missing registries, stale artifacts, broken handoffs, and uninstall safety.

Required evidence:

- Full build and validation transcript.
- Install/uninstall/upgrade or doctor smoke output.
- Archive shape evidence for OpenAI API zips.
- Handoff note with affected contracts, rollback path, and residual risk.

## L5 Regulated, Financial, Web3, AI, Migration, Or Production-Critical Change

Scope: regulated domains, financial or Web3 workflows, AI-agent side effects, data migration, security-sensitive tooling, production-critical install paths, or irreversible external effects.

Reference loading: use the L4 policy and require the route's `Required References` to preserve every selected capability, checklist, and domain extension reference.

Required gates:

- Pass L4.
- Require explicit risk escalation before implementation or release.
- Perform threat, data integrity, side-effect, and auditability review.
- Require human approval for destructive, externally visible, credential-bearing, or production-affecting actions.
- Preserve rollback or recovery instructions and document release blockers.

Required evidence:

- Threat or safety review summary.
- Data integrity and rollback evidence.
- Approval record or explicit block.
- Release decision with stop conditions.

## Production Readiness

A ChangeForge release is production-ready only when source validators pass, routing and code generation benchmark validators pass, all intended profiles build, runtime installation validation passes, OpenAI API zips are profile-scoped and structurally valid, install dry runs pass for supported agents, smoke install/uninstall/reinstall succeeds without removing unrelated files, doctor reports no critical issue for smoke targets, and unresolved assumptions are documented.

Language capabilities are professional engineering rules, not language tutorials or personal technical asset mappings.

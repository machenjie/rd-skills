# Pull Request

## Result

- 

## Scope

- Affected Skill layers, Profiles, registries, docs, installers, scripts, tests, or evals:
- Build profiles affected: `recommended` / `full` / `dev` / none
- Agent hosts affected: `codex` / `claude` / `copilot` / `cline` / `openai-api` / none
- Non-goals:

## Architecture Boundary

- [ ] Preserves one control prompt, four Agent Profiles, and three Skill layers.
- [ ] Does not install `src/` or source registries.
- [ ] Does not add executable interception, internal task/evidence state, hidden Skill packaging, or a second sandbox/workspace manager.
- [ ] Does not add personal-content ingestion or toolbox mappings.
- [ ] Routes one primary Professional Skill per task and only triggered Layer 3 guidance.

## Validation

Paste commands and results:

```text

```

Required for Skill-system changes:

- [ ] Development Affected selected the expected producer/test closure for this base and head.
- [ ] The single PR-only `CI / pr-ci` affected check passed for the current head.
- [ ] If this is an integration handoff or release candidate, the local Full Regression in `docs/VALIDATION.md` ran once on the final material tree.
- [ ] Generated artifacts required by the selected path are fresh and the working tree contains only intended changes.

Required only when this PR claims formal-release readiness:

- [ ] `python3 scripts/eval-core-principles.py --gate formal-release`
- [ ] Core reports `professionalism-formal-release-ready=pass` and the sole professionalism JSON reports `release_gate=release-ready`; no direct producer rerun is counted as separate evidence.
- [ ] Semantic Disposition application is current to the fixed attestation bytes.
- [ ] The tracked Expert Panel inventory is exactly `evals/expert-panel/readability.json`, `evals/expert-panel/semantic-disposition.json`, and `evals/expert-panel/professional-completeness.json`; each compact attestation is current, at most 4 MiB, byte-equal to `HEAD`, and clean.
- [ ] Full packets, templates, ballots, capsules, and decisions remained only under ignored `.rd-skills/expert-panel/<run-id>/` or an optional CI/Release artifact.
- [ ] Readability schema-2 review is current, covers all actionability targets, and has zero tracked tightening, unresolved detector false positives, or required rewrites.
- [ ] Professional-completeness schema-3 review is current: exact carry uses authenticated direct fresh origins, fresh Skills receive two qualified domain votes plus one architecture vote, all 189 effective packages are accepted, correction/unresolved counts are zero, and contract/plan/bindings/provenance/storage/cost are current.
- [ ] The `Formal Release` workflow passed for the current commit or tag.

## Evidence Scope and Review

- Read/inspection evidence:
- Validation after the final material edit:
- Evidence scope and limitations:
- Independent review scope and findings:
- Repair/re-review result:
- Unverified scope:
- Residual risk:
- Reference structural strict / semantic triage / legacy strict status:
- Root structural strict / semantic triage / strict status:
- Readability review status, artifact schema, source fingerprints, actionability coverage, zero-tightening/false-positive/rewrite counts, and clean evidence:
- Professional-completeness status, schema-3 contract/plan/binding fingerprints, fresh/carry partition, reviewer-pool size, authenticated direct-origin closure, input-byte proxy/ratio, 189/189 effective coverage, zero-correction/unresolved counts, and clean compact evidence:
- Aggregate content readiness axes:

Canonical fixed-attestation paths, not Readability or Professional policy config, select Expert Panel evidence; the formal target remains all 189 non-Control packages. These fixed attestations do not prove that the final formal gates or same-commit remote workflow passed.

## Release Notes

- Compatibility or migration impact:
- Rollback path:
- Documentation updated:
- Unresolved decisions:

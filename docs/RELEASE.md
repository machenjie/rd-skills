# Release

Release only from authored source, current evidence, generated build output,
package validation, simulated installation, and the remote `Formal Release`
workflow for the same commit.

[Skill content governance](SKILL_CONTENT_GOVERNANCE.md#validation) owns Root,
Semantic Disposition, Readability, and Professional Completeness evidence
semantics. This page owns only operator order and stop conditions.

## Build And Ordinary Validation

Build the final tree through [Installation](INSTALLATION.md#build).
[Build profiles](BUILD_PROFILES.md) owns profile composition and the generated
manifest contract.

Run the complete ordinary authoring path in [Validation](VALIDATION.md) once,
after the last material edit. Do not duplicate individual producers before a
failure identifies them as the diagnostic owner.

## Efficient Formal Release Flow

1. **Freeze one candidate commit.** Batch known source, documentation, fixture,
   and generated-output repairs first. Require a clean tree and current tracked
   artifacts before formal validation.

2. **Run the ordinary authoring path once.** A failure selects a targeted
   diagnostic. Repair the verified cause, rerun its targeted check, then rerun
   the complete ordinary path once after the final repair.

3. **Check current formal evidence before creating anything.** Check the four
   selected evidence surfaces before creating review artifacts. Run both formal
   gates on the frozen commit:

```bash
python3 scripts/eval-core-principles.py --gate formal-release
python3 scripts/validate-professionalism-regression.py --strict --require-expert-content-review
```

   If all four surfaces are current, create no expert panel. Continue only when
   both commands pass. A failing command must name the stale or invalid surface;
   do not infer that every surface needs replacement.

4. **Refresh only diagnosed evidence.** Refresh only the stale surface. Batch
   every diagnosed repair for that surface, complete its independent review,
   and return to step 1. Do not run a second unchanged attempt after two
   same-path failures.

5. **Run remote evidence once.** Trigger the `Formal Release` workflow for the
   exact locally validated commit or release tag. Package and publish only when
   that workflow passes for the same object ID.

This flow has one ordinary pass and one formal pass on a successful candidate.
A repair invalidates only evidence affected by that repair. The final complete
passes still run once after the last material edit.

Current static evidence selectors are r21 Readability, r24 Semantic
Disposition, r25 Root lifecycle, and r16 schema-3 Professional Completeness for
all 189 non-Control packages. These static selectors do not prove that the
final formal gates or same-commit remote workflow passed.

## Conditional Evidence Refresh

Use this section only after a formal diagnostic identifies a stale surface.
The commands below are usage notation. Replace every placeholder before
execution; they are not copy-paste shell blocks.

### Root lifecycle

When only an authoring bootstrap snapshot is stale:

```text
python3 scripts/audit-skill-content.py --gate authoring --refresh-root-disposition-bootstrap REVIEWER RATIONALE
```

This never satisfies formal release.

When the formal Root lifecycle is stale or has an unclassified comparison:

```text
python3 scripts/audit-skill-content.py --gate formal-release --record-root-disposition-release RELEASE_ID --released-on YYYY-MM-DD [review arguments required by the diagnosed comparison]
```

The recorder derives fingerprints and lineage. Stop on rejected review,
concurrent source/configuration drift, or an unclassified change. Never
hand-edit the managed lifecycle block.

### Semantic Disposition

Create a Semantic Disposition review only when its application binding is stale
or the formal diagnostic reopens a semantic target:

```text
python3 scripts/expert_panel_review.py build-packet --panel-kind semantic-disposition --audit FRESH_AUDIT.json --review-id REVIEW_ID --created-on YYYY-MM-DD --out evals/expert-panel/REVIEW_ID/packet.json
```

### Readability

Create a Readability review only when source, detector, target, or selected
panel currentness fails:

```text
python3 scripts/expert_panel_review.py prepare --panel-kind readability --review-id READABILITY_ID --created-on YYYY-MM-DD --out evals/expert-panel/READABILITY_ID/packet.json
```

### Professional Completeness

Create a schema-3 round only when package, binding, review-contract, selected
decision, lineage, or storage currentness fails:

```text
python3 scripts/expert_panel_review.py prepare --panel-kind professional-completeness --schema-version 3 --review-id COMPLETENESS_ID --created-on YYYY-MM-DD --baseline-decision evals/expert-panel/PRIOR_COMPLETENESS_ID/panel/decision.json --out evals/expert-panel/COMPLETENESS_ID/packet.json
```

Use the machine-derived plan. Changed packages and affected dependencies receive
fresh assigned review. Unchanged packages may carry only from valid direct fresh
origins. An all-carry Professional Completeness round creates no fresh reviewer
artifacts: zero fresh reviewers, ballots, capsules, and input bytes. Maintainers
do not select or override dispositions.

Reviewer manifests and unfilled templates remain outside the repository.
Materialize ballots only through the bounded command and transport contract in
[Skill content governance](SKILL_CONTENT_GOVERNANCE.md#targeted-references).
Never overwrite an accepted ballot or predecessor.

## Stop And Recovery

Stop on a failed command, dirty or stale required artifact, unexpected write,
unclassified Root change, Readability blocker, professional correction,
unresolved professional disagreement, invalid carry, or missing independent
review.

Do not weaken a validator, edit a generated readiness decision, or create
replacement panels without a diagnosed stale surface. Correct the owning source
or review input. Before publication, discard only verified new uncommitted
release output; never remove unrelated files or accepted evidence. Installed
artifact recovery is documented in [Installation](INSTALLATION.md#upgrade).

## Package

After local and remote formal evidence passes for the same commit:

```bash
python3 scripts/package.py --profile recommended
python3 scripts/package.py --profile full
python3 scripts/package.py --profile dev
```

Package only generated profile content under `dist/`. Never package `src/`,
source registries, reports, reviewer input manifests, personal mappings, or
obsolete runtime artifacts. The build manifest is the package inventory
authority.

## Documentation And Scorecard

Regenerate only artifacts with a named generator. The
[Scorecard](SCORECARD.md) is a handwritten expectations table, not generated
status and not a current-tree pass report. Release status comes from current
producer output and tracked evidence. The handoff records commands, the source
commit, freshness, skipped checks, Unverified scope, and Residual risk.

## Evidence Scope

Release evidence covers static contracts, deterministic routing and behavior
fixtures, professional-quality checks, code-generation definitions and
harness/negative controls, builds, package structure, and simulated
installation. It does not prove real-host Profile startup, host enforcement,
wall-clock performance, production accuracy, provider behavior, official
marketplace publication, or installed user experience.

## Release Checklist

- [ ] The candidate is one clean commit with current generated artifacts.
- [ ] The complete ordinary path passed after the final material edit.
- [ ] Both local formal commands passed for that commit.
- [ ] Root, Semantic Disposition, Readability, and Professional Completeness
      selectors are current, tracked, byte-equal to `HEAD`, and clean.
- [ ] Professional Completeness accepts all 189 packages with required fresh or
      valid carried votes and no correction or unresolved disagreement.
- [ ] Readability has no tracked tightening, unresolved detector false positive,
      or rewrite requirement.
- [ ] All three profiles build and package through their generated manifests.
- [ ] The remote `Formal Release` workflow passed for the same object ID.
- [ ] The handoff states evidence limits, skipped checks, Unverified scope, and
      Residual risk.

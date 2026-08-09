# Release

Release only from authored source, current evidence, generated build output,
package validation, simulated installation, and the remote `Formal Release`
workflow for the same commit.

[Skill content governance](SKILL_CONTENT_GOVERNANCE.md#validation) owns Root,
Semantic Disposition, Readability, and Professional Completeness evidence
semantics. This page owns only operator order and stop conditions.

## Build And Local Full Regression

Build the final tree through [Installation](INSTALLATION.md#build).
[Build profiles](BUILD_PROFILES.md) owns profile composition and the generated
manifest contract.

Run the [local Full Regression](VALIDATION.md#local-full-regression) once after
the last material edit. Core authoring owns its deterministic producer graph;
do not duplicate individual producers before a failure identifies them as the
diagnostic owner.

## Efficient Formal Release Flow

1. **Freeze one candidate commit.** Batch known source, documentation, fixture,
   and generated-output repairs first. Require a clean tree and current tracked
   artifacts before formal validation.

2. **Run the local Full Regression once.** A failure selects a targeted
   diagnostic. Repair the verified cause, rerun its targeted check, then rerun
   the Full Regression once after the final repair.

3. **Check current formal evidence before creating anything.** Check the four
   selected evidence surfaces before creating review artifacts. Run the Core
   formal gate on the frozen commit:

```bash
python3 scripts/eval-core-principles.py --gate formal-release
```

   If all four surfaces are current, create no expert panel. This is a
   conditional operator rule, not a statement of present status. Continue only
   when Core's formal outcomes pass, including
   `professionalism-formal-release-ready`. A failing outcome must name the stale or invalid
   surface; do not infer that every surface needs replacement.

4. **Refresh only diagnosed evidence.** Refresh only the stale surface. Batch
   every diagnosed repair for that surface, complete its independent review,
   and return to step 1. Do not run a second unchanged attempt after two
   same-path failures.

5. **Run remote evidence once.** Trigger the `Formal Release` workflow for the
   exact locally validated commit or release tag. Package and publish only when
   that workflow passes for the same object ID.

This flow has one local Full Regression and one formal pass on a successful candidate.
A repair invalidates only evidence affected by that repair. The final complete
passes still run once after the last material edit.

For selector identity only, the canonical projection is: Current static
evidence selectors are r26 Readability, r26 Semantic Disposition, r26 Root
lifecycle, and r19 schema-3 Professional Completeness for all 189 non-Control
packages. “Current” in that projection names the configured selector set; it
does not attest the four surfaces' currentness. Readability r26 and full-fresh
Professional Completeness r19 have complete decisions for their recorded
inputs. Readability r26 is historical evidence with no recorded tracked
tightening, detector false positive, or rewrite requirement under its bound
Skill detector, but that detector is now stale against the current detector. R26 has
`source_current=false`, status `panel-majority-stale`, remains storage-pending,
and is not accepted for formal release. R19 is historical full-fresh evidence
with no professional correction or unresolved professional disagreement under
its bound contract, but that contract is now stale against the current
Professional review contract. R19 remains storage-pending, is not accepted for
formal release, and cannot authorize carry across the contract change. The
Semantic Disposition application is `invalid` because its packet is stale
against the current audit. Root lifecycle is
`pending-changes`, with `snapshot_current=false` and no formal-release
readiness. These static selectors do not prove that the final formal gates or
same-commit remote workflow passed.

The later owning refresh stages are [Semantic Disposition](#semantic-disposition)
after the final audit and [Root lifecycle](#root-lifecycle) after the final
content tree stabilizes. Formal Release requires a new current schema-2
Readability review under the current Skill detector and a new schema-3
full-fresh Professional Completeness round for all 189 current non-Control
packages under the current review contract. Preserve r26 and r19 as immutable
historical evidence; neither can satisfy its required new review, and r19
cannot authorize carry. Until those stages complete, the professionalism JSON
correctly reports `release_gate=release-not-ready`.

`reports/professionalism-regression-report.json` is the sole machine-readable
professionalism readiness authority. Its only producer is
`scripts/validate-professionalism-regression.py`, which the Core Principles
orchestrator runs and freshness-checks in dependency order. The formal-release
Core run also requests `reports/professionalism-regression-report.md` as a
release-only presentation projection. That Markdown is not an input or a
second authority, and the authoring gate does not refresh it. Productization
validates the saved JSON semantically without rerunning the producer.

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
producer JSON and tracked evidence; the release-only Markdown is a human
projection of that result. The handoff records commands, the source commit,
freshness, skipped checks, Unverified scope, and Residual risk.

## Evidence Scope

Release evidence covers static contracts, deterministic routing and behavior
fixtures, professional-quality checks, code-generation definitions and
harness/negative controls, builds, package structure, and simulated
installation. It does not prove real-host Profile startup, host enforcement,
wall-clock performance, production accuracy, provider behavior, official
marketplace publication, or installed user experience.

## Release Checklist

- [ ] The candidate is one clean commit with current generated artifacts.
- [ ] The local Full Regression passed after the final material edit.
- [ ] The local Core formal gate and its aggregate professionalism readiness
      outcome passed for that commit.
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

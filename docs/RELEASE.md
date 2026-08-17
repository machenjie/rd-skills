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

The post-migration tracked Expert Panel inventory must be exactly
`evals/expert-panel/readability.json`,
`evals/expert-panel/semantic-disposition.json`, and
`evals/expert-panel/professional-completeness.json`. Each fixed path contains one
current compact attestation, is at most 4 MiB, and is replaced rather than
appended. Full packets, templates, ballots, capsules, and decisions remain only
under ignored `.rd-skills/expert-panel/<run-id>/` or an optional CI/Release
artifact. Git history audits replaced attestations; do not retain dated, `rN`,
or last-N copies in the tracked tree.

Canonical fixed-attestation paths, not Readability or Professional policy
config, select Expert Panel evidence; the formal target remains all 189
non-Control packages. Formal release requires a current Semantic Disposition
application bound to the exact fixed-attestation bytes. Reuse each current
attestation while its strict current validator passes; create and promote a
replacement only after its source, detector, binding, or review contract
becomes stale. These fixed attestations do not prove that the final formal gates or
same-commit remote workflow passed.

`reports/professionalism-regression-report.json` is the sole machine-readable
professionalism readiness authority. Its only producer is
`scripts/validate-professionalism-regression.py`, which the Core Principles
orchestrator runs and freshness-checks in dependency order. The formal-release
Core run writes the professionalism and Core schema-4 JSON outcomes plus their
Markdown projections under
`.rd-skills/formal-release/<captured-head>/reports/`. The ignored scene is bound
to the captured input `HEAD` and contains exactly those four canonical files;
it is not an input or a second tracked authority. The complete formal producer
graph writes and reads intermediate reports only in the sibling
`producer-reports/` staging directory. Authoring refreshes only the tracked
ordinary JSON, and Productization validates that saved JSON semantically
without rerunning the producer.
On a formal Core run that JSON also owns the downstream
`expert_panel_release_manifest`. It binds the release commit to external
SHA-256 and byte size, review ID, verdict, axis, and canonical path for exactly
the three fixed attestations; it creates no fourth tracked file and is excluded
from all panel currentness fingerprints. The remote workflow independently
compares the manifest commit with the release object ID.

## Conditional Evidence Refresh

Use this section only after a formal diagnostic identifies a stale surface.
The commands below are usage notation. Replace every placeholder before
execution; they are not copy-paste shell blocks.

### Semantic Disposition

Create a Semantic Disposition review only when its application binding is stale
or the formal diagnostic reopens a semantic target:

```text
python3 scripts/expert_panel_review.py prepare --panel-kind semantic-disposition --audit reports/skill-content-audit.json --review-id REVIEW_ID --created-on YYYY-MM-DD --semantic-re-review-axis root --semantic-re-review-axis reference --reviewer VOTER_1 AGENT_1 ROLE_1 EXPERTISE_1 --reviewer VOTER_2 AGENT_2 ROLE_2 EXPERTISE_2 --reviewer VOTER_3 AGENT_3 ROLE_3 EXPERTISE_3 --out .rd-skills/expert-panel/REVIEW_ID/packet.json
```

### Readability

Create a Readability review only when source, detector, target, or selected
panel currentness fails:

```text
python3 scripts/expert_panel_review.py prepare --panel-kind readability --review-id READABILITY_ID --created-on YYYY-MM-DD --out .rd-skills/expert-panel/READABILITY_ID/packet.json
```

### Professional Completeness

Create a schema-3 review only when package, binding, review-contract, provenance,
or current-attestation storage fails:

```text
python3 scripts/expert_panel_review.py prepare --panel-kind professional-completeness --schema-version 3 --review-id COMPLETENESS_ID --created-on YYYY-MM-DD --out .rd-skills/expert-panel/COMPLETENESS_ID/packet.json
```

Use the machine-derived plan. Changed packages and affected dependencies receive
fresh assigned review. Unchanged packages may carry only from valid direct fresh
origins. An all-carry Professional Completeness round creates no fresh reviewer
artifacts: zero fresh reviewers, ballots, capsules, and input bytes. Maintainers
do not select or override dispositions.

The current schema-3 contract uses one package-material binding and one review
unit per packet target, one shared dependency-material catalog in compact
storage, and dependency IDs in each finding. It rejects legacy
source/package/review-binding aliases. A Professional review-contract change
invalidates every package; earlier schema-3 contracts are audit-only and require
a new full-fresh round before release or carry.
The fixed Professional compact schema-2 bytes additionally use the physical
`professional-string-catalog-v1` codec: routing identity remains literal and
all other repeated string values are canonical catalog references. This does
not change reviewer-visible authority or the review-contract fingerprint.
Validation expands the codec through the shared attestation owner before
semantic currentness checks and rejects bare current schema-2 or alternative
catalog encodings. Promotion must reproduce the exact encoded source bytes from
the authenticated decision before compare-and-swap.
Generate the Professional attestation only on one clean stable commit `C`.
Fresh `origin_commit` records that projection commit after the decision and
current package/review/dependency bindings validate; it does not claim when
reviewers executed or when the decision file was created. Run exact promotion
validation on the same `C`. The later fixed-artifact commit `P` retains origin
`C`; currentness and Formal Release do not rewrite it or require `C == P`.

For exact carry, add `--baseline-attestation
evals/expert-panel/professional-completeness.json`; the current attestation is
self-contained and no predecessor decision path is required. Reviewer manifests
and unfilled templates remain outside the repository.
Materialize ballots only through the bounded command and transport contract in
[Skill content governance](SKILL_CONTENT_GOVERNANCE.md#targeted-references).
After validating the runtime decision, build and promote one replacement
attestation. Promotion writes only the panel kind's fixed path and requires the
expected current SHA-256, or `absent` for the first tracked attestation.

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

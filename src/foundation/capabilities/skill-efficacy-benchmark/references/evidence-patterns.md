# Skill Efficacy Benchmark Evidence Patterns

Use this reference when closure depends on current source, a baseline/treatment comparison, validation freshness, generated reports, build-profile output, privacy boundaries, or explicit proof limits.

## Evidence Classification

| Evidence source | Use as | Reject as |
| --- | --- | --- |
| Current source and diff | Treatment artifact and changed-path input. | Proof that behavior improved without a case. |
| Generated report | Structural evidence from its generating command. | Live agent performance or user productivity proof. |
| Prior task note | Lead to a recurring failure or stale validation risk. | Current truth without source confirmation. |
| Observable action sequence | Order of edits, validations, failures, repairs, and re-runs. | Fresh proof when validation predates the last edit. |
| Baseline artifact | Comparison point for old behavior. | A representative population unless sampling is defined. |
| Validator output | Evidence for the validator's declared scope after the final edit. | Evidence for unrun commands, external CI, or production behavior. |

## Freshness And Build Profile Map

| Changed item | Freshness trigger | Required validation evidence |
| --- | --- | --- |
| Skill `SKILL.md` | Body, trigger, output, stop condition, or loading rule changes. | Body links, content size, professionalism evaluation, and audit as applicable. |
| Targeted reference | File added, renamed, linked, or materially changed. | Authored links, content size, build, and built-Skill reference validation. |
| Registry or router | Role support, trigger, anti-trigger, candidates, or route fixture changes. | Registry, deterministic routing, and routing coverage validation. |
| Agent Profile or control prompt | Permission boundary, responsibility, dispatch, progress, or closure behavior changes. | Profile validation, control-prompt validation, observable action sequence fixtures, and behavior samples. |
| Benchmark fixture or evaluator | Case, expected result, assertion, report shape, or promoted sample changes. | Fixture validator and matching evaluation command. |
| Generated report or `dist/` output | Source or generator changes after generation. | Fresh generator/evaluation/build command plus installation or built-reference validation. |

## Current Evidence Reconciliation

- Confirm every prior note against current source, registries, reports, or validator output before using it as evidence.
- Mark validation stale when any material source, reference, registry, Profile prompt, fixture, report, build output, or owner decision changes after the command.
- Preserve repaired failures as evidence only when a later validator covers the failed scope.
- Treat a summary of prior validation as a locator; confirm the current result or rerun the command.

## Proof Limits

| Claim | Required wording |
| --- | --- |
| Static validator passed | The validator passed for the checked fixture or report scope. |
| Score improved | The score improved only for the evaluator dimensions measured by this report. |
| Built references valid | Built profile Markdown links are valid after the current build. |
| Agent behavior improved | Allowed only with representative agent-run evidence, sampling limits, and caveats. |
| Efficiency improved | Requires measured token, turn, or elapsed-time comparison; otherwise use `not_collected`. |
| Safer closure | Requires a negative baseline or forbidden behavior that the treatment catches. |

- If approved external measurement or connector lookup, use the approved account/data boundary, redaction, and retention rule.
- If destructive cleanup or deployment, treat it as outside ordinary skill benchmarking; requires explicit authority and rollback.

## Result Decisions

- Missing comparable baseline yields evidence class `structural-only`, final verdict `not_enough_evidence`, and no empirical-improvement score.
- Return `not_enough_evidence` when treatment, metrics, validation, or caveat is missing.
- Return `unknown` when evidence is valid but does not distinguish old and new behavior.
- Return `improved` only when the treatment is better on a named metric and proof limits are explicit.

# Skill Efficacy Benchmark Decision Checklist

Dev/evaluation-only checklist; do not load it for ordinary product work.

1. Name the case, changed Skill/Profile/route/reference/evaluation surface, and concrete behavior claim.
2. Define the bounded task and why a benchmark is needed instead of prose or a validator alone.
3. Identify baseline and treatment artifacts plus the reason any comparable baseline is unavailable.
4. Hold task, Host, Model, Profile, repository state, evidence boundary, evaluator, expected definition, source-vs-dist boundary, fixtures, and metric definitions constant.
5. Keep the opaque agent packet, evaluator oracle, observations, verifier-owned captures, and post-capture OLD/NEW reveal physically separate; reject semantic answer leakage, copied/fake capture bindings, or early reveal.
6. Map each claim to Core-derived routing, Review, evidence, defect catch, freshness, over-routing, under-routing, token, turn, or elapsed evidence.
7. Record token, turn, and elapsed values only as measured or `not_collected`.
8. Record selected and skipped references/Skills with task-specific reasons and context-cost limits.
9. Include both a trivial/out-of-scope over-routing guard and a hidden-risk under-routing guard.
10. Classify evidence as `structural-only` when representative live runs or comparable live evidence are absent.
11. Use `not_enough_evidence`, not `structural-only`, as the missing-live-evidence verdict.
12. Reject a lower-cost treatment when any routing, Review, or code-quality metric regresses in any case; partial NEW success and suite averages cannot hide it.
13. Inspect current source, registry/routing, reports, diff, built boundary, and action evidence; treat prior notes as leads until fresh confirmation.
14. For a surface changed by the current authoring task, run mapped validation after the final material edit or name the stale/not-run gap and residual owner.
15. Enforce bounded/redacted fixture privacy, state what the case proves and does not prove, and name rollback, residual owner, and next step.

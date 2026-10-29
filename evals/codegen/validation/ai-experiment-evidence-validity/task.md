# Evidence Contract

Implement pure functions in `evidence_checks.py`. Inputs are fixed observations and explicit plans. Return issue sets; do not call a model, provider, database, or statistical service.

## RAG

`evaluate_rag(record)` compares relevant, retrieved, required-claim, answered-claim, and authoritative claim-support sets. Missing relevant documents produce `retrieval-miss`. Missing required claims produce `answer-omission`. An answer support set must be nonempty, retrieved, and contained in that claim's authoritative evidence set; otherwise report `unsupported-claim`. Certain answers without any fresh relevant evidence report `unsupported-certainty`. Used documents expired at `as_of` report `stale-evidence`; used documents with conflicting used identities report `conflicting-evidence`. An explicit abstention with no claims is valid when no answer evidence exists.

## Trials

`evaluate_trials(records, plan)` counts unique trial identities and successful actual terminal states. Compare the success claim with `success_terminal`; report `success-claim-mismatch` on disagreement. Report duplicate identities, insufficient trial count, tuning/heldout intersection, and quality, maximum latency, or total cost outside the explicit plan. Return trial count, actual successes, success ratio, issues, and `eligible_for_acceptance`. Eligibility requires no issue. No sample, quality, latency, or cost threshold is universal.

## Training

`validate_training(record)` checks sample overlap across splits, entity overlap only under an entity split, and prediction times around an explicit temporal cutoff. A feature available after prediction time is `future-feature`. A training label unavailable at the training cutoff is `immature-training-label`. Future prediction targets themselves are legitimate when their labels have matured by training. Preprocessing may fit training sample identities only. Final test identities cannot be tuning inputs. Required resume components must be present. Loaded model/preprocessor/tokenizer/adapter identities must match the authoritative model manifest. Return distinct issue codes exercised in the tests.

## Experiments

`validate_experiment(record)` checks the declared assignment and analysis units. Cross-unit analysis requires the declared clustered handling. Compute Pearson allocation discrepancy from observed assignment counts and declared allocation weights; compare it with the supplied `srm_statistic_limit`. Check explicit minimum units and preregistration time. Fixed-sample stopping on an effect before its target, or after repeated decision looks, is invalid. Sequential monitoring must use the predeclared supported method and stay within look and alpha budgets. Hypothesis count and multiplicity handling must follow the declared plan.

The supported fixture method labels are `alpha-spending` and `always-valid`. Recognizing a label does not mathematically validate that method. Empty issues means these record checks passed, not that a real causal or scientific conclusion has been established.

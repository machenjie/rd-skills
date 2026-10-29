# ML Training and Experiment Engineering

**Reference type:** targeted
**Load when:** Model training or fine-tuning changes data splits, experiments, checkpoints, or the deployable model package.
**Do not load when:** The task only integrates a model API, ordinary RAG, or a data pipeline without model-training behavior.
**Required by:** analysis-agent, task-agent, review-agent
**Required output:** decision-record, validation-plan, proof-limit

## Experiment Decisions

- Define the prediction target, evaluation population, and baseline before choosing a training change.
- Split by time, entity, group, or sample according to the dependency structure and intended prediction setting.
- Check duplicate and related examples across splits. Row-level separation can still leak the same entity or future information.
- Fit preprocessing on the training partition for the current split or fold. Apply the fitted transformation to held-out data.
- Inspect label provenance, disagreement, missingness, and timing. A label unavailable at prediction time can encode leakage.
- Separate hyperparameter selection from final retained evaluation. Repeatedly optimizing against the final set converts it into development data.
- Record data, code, configuration, environment, and randomness state needed to interpret or reproduce the experiment.
- Compare model changes against the baseline on required product outcomes and cohorts. Lower training loss does not establish product value.

## Recovery and Delivery

- Distinguish inference weights from a resumable training checkpoint. Resume can depend on optimizer, scheduler, scaler, RNG, sampler, and input-cursor state.
- Select required checkpoint state from the actual training loop.
- Prove recovery against the next batch and update under stated reproducibility limits.
- Bind features, preprocessing, model, tokenizer, and adapter versions into one compatible delivery contract.
- Validate training-serving parity for feature ordering, missing values, tokenization, normalization, and output interpretation.
- Test checkpoint compatibility and partial-write recovery before relying on interrupted training continuation.
- Keep exact replay claims bounded by hardware, kernels, libraries, parallel reduction, and deterministic settings actually exercised.

## Distinguishing Cases

| Case | Required check |
| --- | --- |
| One entity appears in train and test under different rows | Group separation matches the intended generalization claim |
| Preprocessing was fitted before splitting | Held-out information is removed from fitted parameters |
| Resume restores weights but omits optimizer state | Next update exposes the incomplete recovery state |
| Tokenizer or adapter does not match the saved model | Package compatibility fails before interpreting inference results |
| Final retained set drives repeated tuning | A new independent evaluation is needed for the original claim |
| Training loss improves while the target cohort worsens | Product acceptance remains unsatisfied |

Return split and leakage evidence, baseline comparisons, recovery state, deployment bindings, and reproducibility limits.

## Sources and Limits

- Check [preprocessing leakage](https://scikit-learn.org/stable/common_pitfalls.html) and [split strategies](https://scikit-learn.org/stable/modules/cross_validation.html) against the target data dependencies.
- Distinguish weights from [resumable PyTorch checkpoints](https://docs.pytorch.org/tutorials/beginner/saving_loading_models.html#saving-loading-a-general-checkpoint-for-inference-and-or-resuming-training).
- Derive additional recovery state from the actual loop; the checkpoint example does not prove arbitrary scheduler or distributed recovery behavior.

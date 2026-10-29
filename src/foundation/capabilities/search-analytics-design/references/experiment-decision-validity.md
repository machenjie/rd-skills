# Experiment Decision Validity

**Reference type:** targeted
**Load when:** A randomized product experiment needs sample planning, statistical interpretation, or a rollout decision from outcome data.
**Do not load when:** The task only renames telemetry fields or changes established instrumentation without an experiment-inference decision.
**Required by:** analysis-agent, task-agent, review-agent
**Required output:** decision-record, validation-plan, proof-limit

## Inference Decisions

- Bind eligibility, assignment, exposure, and outcome definitions before calculating treatment effects.
- Match the analysis unit and dependence model to randomization. Events from one randomized user are not automatically independent observations.
- Account for clustering, repeated observations, and spillover when they affect variance or treatment contamination.
- Select the target effect, minimum detectable effect, sample budget, and observation horizon from the product decision and plausible variability.
- Choose fixed-sample or a justified sequential method before using a stopping rule. Repeated fixed-sample significance checks can inflate false positives.
- Check the assumptions of the selected sequential method. Looking repeatedly is not validated by calling a test sequential.
- Define the family of metrics, cohorts, and variants subject to multiple comparisons. Exploratory findings need appropriately qualified follow-up.
- Investigate sample-ratio mismatch before claiming the randomized comparison is valid. Assignment, exposure, logging, or selection defects can invalidate inference.
- Reconcile denominators, deduplication, missing outcomes, late events, and treatment-dependent instrumentation against the existing metric contract.
- Report effect estimates, uncertainty, and consequential guardrails together. Statistical detectability and business value answer different questions.
- Separate an inconclusive estimate from evidence of no meaningful effect. Insufficient power can leave the important difference unresolved.
- Bind rollout decisions to the product's benefit, harm, uncertainty, and operational constraints. Avoid a universal significance or release threshold.

## Distinguishing Cases

| Case | Required interpretation |
| --- | --- |
| Inspect conversion daily and stop at the first lead | Fixed-sample inference does not support that unplanned stopping rule |
| Randomize users but treat their events as independent samples | Dependence and analysis-unit mismatch undermine uncertainty estimates |
| Sample-ratio mismatch remains unexplained | Causal acceptance remains unsupported |
| Many metrics are searched for one positive result | Multiplicity and exploratory selection change the claim |
| Small sample yields a wide interval spanning material effects | The decision is uncertain, not proof of equivalence |
| Metric improves through changed event loss or denominator | Measurement behavior can explain the apparent treatment effect |

Return randomization and analysis units, stopping method, sample adequacy, validity checks, and bounded decision conclusions.
Fixed records validate interpretation rules; they do not establish a live experiment's causal effect.

## Method Sources

- Check [metric interpretation pitfalls](https://www.microsoft.com/en-us/research/wp-content/uploads/2020/08/2017-08-KDDMetricInterpretationPitfalls.pdf) when denominators or instrumentation influence the conclusion.
- Use [sequential inference under its stated assumptions](https://pubsonline.informs.org/doi/10.1287/opre.2021.2135), not ordinary significance checks with opportunistic stopping.

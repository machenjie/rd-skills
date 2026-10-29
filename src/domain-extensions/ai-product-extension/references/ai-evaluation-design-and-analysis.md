# AI Evaluation Design and Analysis

**Reference type:** targeted
**Load when:** An AI product needs evaluation tasks, trial design, graders, or interpretation of a model or agent change.
**Do not load when:** The task has no AI behavior comparison or concerns the repository's static Skill-validation machinery alone.
**Required by:** analysis-agent, task-agent, review-agent
**Required output:** decision-record, validation-plan, proof-limit

## Evaluation Decisions

- Define a task through its inputs, environment, allowed actions, and observable success conditions.
- Separate the task from a trial. Repeated executions of the same task can produce different outcomes.
- Reset or intentionally carry environment state between trials. Hidden state from earlier runs can invalidate comparisons.
- Bind model, prompt, tools, data, grader, and environment versions to the compared results.
- Prefer deterministic graders for observable states and exact contracts they can judge correctly.
- Use model or human grading for judgments that require it. Calibrate the rubric against independently examined successes and failures.
- Distinguish the agent's success claim from the environment's terminal state. Inspect the actual artifact, transaction, or user-visible outcome.
- Separate development, tuning, and retained evaluation sets. Prior evaluation outputs can contaminate later model or prompt decisions.
- Allocate repeated trials according to variability and decision consequence. A single success does not establish reliable behavior.
- Compare baseline and change on matched task populations.
- Report uncertainty and sample counts alongside aggregate results and consequential groups.
- Investigate grader disagreement and systematic preference, including verbosity, style, order, and recognizable model identity where applicable.
- Examine failures by mechanism before adding more examples. Distinguish retrieval, planning, tool use, state recovery, and grading defects.
- Apply required quality and consequential-outcome constraints before selecting a cheaper or faster configuration.

## Distinguishing Cases

| Case | Required interpretation |
| --- | --- |
| Agent announces completion but the target artifact is missing | Task failure despite a persuasive final message |
| One lucky trial succeeds while repetitions fail | Variable performance with a bounded reliability estimate |
| Judge rewards verbosity while human-checked answers omit a requirement | Grader defect or calibration gap |
| Mean quality rises while a consequential group regresses | Separate group evidence and the violated acceptance condition |
| A small sample shows a minor improvement | Uncertainty can leave the comparison inconclusive |
| Prompt tuning repeatedly uses the retained set | Independence is lost; the set no longer supports the original claim |

Return task and trial definitions, grader validity, outcome distributions, consequential slices, and unresolved evidence.
Deterministic fixtures test the evaluation contract; they do not establish actual model performance.

## Method Source

- Use [task, trial, grader, and environment distinctions](https://www.anthropic.com/research/demystifying-evals-for-ai-agents) when designing agent evaluations.
- Treat provider examples as method illustrations, not universal product thresholds or grader defaults.

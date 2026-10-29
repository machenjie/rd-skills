# Feasibility Experiment Design

- Rewrite uncertainty as a falsifiable question with an observable failure outcome.
- Compare each candidate with a baseline under equivalent inputs and constraints.
- Select the smallest real boundary that could invalidate the approach.
- Fix inputs, dependency versions, environment, workload, and measurement method.
- Set task-specific time, cost, and resource budgets before execution.
- Define success, inconclusive results, and stop conditions independently of the candidate's output.
- Assign mutating prototype work to an authorized implementation owner.
- Preserve enough observations to reproduce the conclusion without retaining unnecessary temporary data.
- Decide whether to discard, retain as evidence, or harden the prototype.
- List production properties the experiment did not exercise.

| Question | Discriminating experiment | Unsupported inference |
|---|---|---|
| Can a streaming consumer tolerate cancellation? | Cancel across a resource-owning boundary and inspect cleanup | One successful happy-path demo proves recovery |
| Does a candidate meet the workload budget? | Compare a pinned baseline under the same arrival pattern | Lower toy-input latency proves production capacity |
| Can old and new consumers coexist? | Exercise both against the intended shared contract | Compilation proves mixed-version behavior |

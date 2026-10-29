# Load Model and Capacity Evidence

**Reference type:** evidence-pattern
**Load when:** A load test or capacity claim depends on arrival rate, concurrency, saturation, overload, or recovery evidence.
**Do not load when:** The task only sets a performance budget or profiles a bottleneck without designing or interpreting a load experiment.
**Required by:** analysis-agent, task-agent, review-agent
**Required output:** evidence-record, validation-plan, proof-limit

## Workload Decisions

- Bind the required workload to arrivals, operation mix, payload distribution, session behavior, and relevant burst patterns.
- Use an open model when arrivals are scheduled independently of completion.
- Use a closed model when a bounded population waits before continuing.
- Check whether fixed concurrency reduces offered work as responses slow. Such self-throttling cannot establish a required fixed arrival rate.
- Record intended arrivals, actual starts, completions, and work the driver delayed or left unsent separately.
- Measure queueing from the relevant arrival boundary. Starting the clock only after admission can hide user-visible waiting.
- Check for coordinated omission when measurement or workload generation pauses during slow service. A latency histogram can exclude the missing arrivals.
- Verify driver headroom, clocks, connection limits, client queues, and network capacity before attributing saturation to the target.
- Preserve rejection, timeout, cancellation, and unfinished work as outcomes. A latency sample limited to successes biases the capacity conclusion.
- Observe steady state, overload, and recovery as distinct phases. A recovered success rate can still hide an undrained backlog.
- Relate throughput and latency to the actual workload shape. Do not compare unlike payloads, arrival patterns, cache states, or success definitions.
- Evaluate capacity acceptance against the required quality, correctness, and throughput conditions together.
- Report the observed sustainable region and uncertainty against the specified objective.
- Derive acceptance thresholds from that objective rather than universal defaults.

## Evidence Ledger

| Boundary | Record |
| --- | --- |
| Offered work | Intended arrivals, actual starts, delayed starts, and unsent or dropped work |
| Admission and queueing | Accepted and rejected work, queue delay, queue size, and outstanding work |
| Completion | Success, application failure, timeout, cancellation, and unfinished work at observation end |
| Generator | Resource saturation, connection constraints, clock basis, and scheduling limitations |
| Phases | Steady-state interval, overload onset, recovery behavior, and backlog disposition |
| Interpretation | Actual traffic shape, latency denominator, objective, uncertainty, and excluded environments |

## Counterexample

Reject a fixed-arrival capacity claim when the test uses fixed concurrency and arrivals fall as service slows.
Compare the intended schedule with actual starts, including omitted work.
A successful-request percentile cannot compensate for dropped arrivals or unfinished requests.

Return the workload model, outcome accounting, measured limits, and conditions under which the claim holds.
Static timelines and deterministic fixtures validate interpretation rules; they do not prove production capacity.

## Tool-Specific Sources

- With k6, check [open and closed models](https://grafana.com/docs/k6/latest/using-k6/scenarios/concepts/open-vs-closed/) against available virtual-user capacity.
- Classify [dropped iterations](https://grafana.com/docs/k6/latest/using-k6/scenarios/concepts/dropped-iterations/) as work without a start, separately from server rejection or completed failures.
- Map [arrival-rate iterations](https://grafana.com/docs/k6/latest/using-k6/scenarios/executors/constant-arrival-rate/) to requests before claiming an HTTP request rate.

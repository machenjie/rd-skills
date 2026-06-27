# Architecture Tradeoff Evidence Patterns

Load this reference only when a decision depends on current repository graph, project memory, execution trajectory, validation freshness, or a decision-to-validation map. Do not load it for quick routing or low-risk local choices.

## Evidence Surfaces

| Surface | Accept as evidence when | Reject or downgrade when |
| --- | --- | --- |
| Repository graph | Source paths, imports, callers, tests, generated artifacts, owners, and deploy/config edges are current for the decision boundary. | Graph output is old, generated-only, missing owners, or not tied to affected source paths. |
| Project memory | Prior ADRs, incidents, benchmark notes, and team decisions have date, scope, owner, and unchanged constraints. | Memory is undated, copied from a summary, conflicts with current source, or substitutes for inspection. |
| Execution trajectory | Commands, probes, prototypes, failed attempts, and repair steps explain why assumptions were accepted or rejected. | Only final success is reported, repeated failures are hidden, or validation predates the final decision. |
| Validation broker | Changed boundaries map to narrow, module, or full validators with parsed outcome, exit code, and freshness. | Validation is partial, stale, lacks exit code, or proves a different boundary than the decision affects. |
| Telemetry or operations | Metrics, traces, logs, alerts, incident data, or cost reports match the environment and scale named in the forces. | Production-only claims lack source, metric definition, time window, owner, or environment match. |

## Graph Coupling

Use graph evidence to keep architecture choices tied to the current system shape:

- Record affected modules, services, deploy units, data owners, generated contracts, and test owners.
- Identify new or removed edges: imports, API calls, events, queues, schema ownership, config ownership, and operational dependencies.
- Mark generated artifacts as evidence of consumers, not as source of truth, unless the generator contract is the decision target.
- State graph freshness: command, graph artifact, source date, or not-inspected boundary.
- Reject boundary moves that create cycles, private-surface dependencies, duplicate ownership, or unowned release/test blast radius.

## Memory Freshness

Project memory is a lead, not proof. Use it this way:

- Accept memory only when date, scope, owner, and unchanged constraints are stated.
- Compare old ADR assumptions with current scale, team ownership, vendor risk, compliance scope, and incident history.
- Keep accepted memory in the decision context; keep rejected memory in evidence limits with the reason it no longer closes the decision.
- Set an expiry condition when the memory depends on scale, team size, spend, vendor posture, or regulatory context.
- Keep decision evidence bounded to reviewed source paths, artifacts, metrics, and owner-approved records; exclude private content and credentials.

## Execution And Validation Coupling

Architecture decisions must connect to execution evidence before release:

- Map every decisive force to a proof type: prototype, benchmark, test, contract check, migration rehearsal, cost model, threat review, or operational metric.
- Map every high or medium residual risk to an owner, mitigation, validator, monitoring signal, and review date.
- Record failed probes and rejected options when they changed the matrix; do not hide them as noise.
- Re-run or downgrade validation when source, config, generated artifacts, migrations, or test fixtures change after the evidence was captured.
- Use `validation-broker` when changed paths or generated consumers make validator selection non-obvious.

## Decision-To-Validation Map Pattern

Use this compact shape inside the ADR-ready output:

| Decision element | Proof artifact | Freshness rule | Release consequence |
| --- | --- | --- | --- |
| Heaviest force | Benchmark, prototype, test suite, cost model, or owner-approved constraint. | Fresh after final source/config/schema change. | Blocks acceptance if missing for Type 1 decisions. |
| Rejected alternative | Disqualifying constraint, spike result, consumer impact, or exit-cost estimate. | Valid until the rejected constraint changes. | Reopen decision if constraint no longer applies. |
| Residual risk | Mitigation task, monitor, alert, runbook, specialist gate, or review owner. | Review at trigger or expiry date. | Cannot close without named owner. |
| Reassessment trigger | Metric threshold, date, vendor event, team scale, incident, or cost ceiling. | Must be measurable from an owned source. | Supersede or renew ADR when triggered. |

## Efficiency Guardrail

Keep the main `SKILL.md` concise. Put only durable routing rules, non-negotiables, output fields, and quality gates there. Put detailed matrices, benchmark catalogs, example wording, and edge-case evidence patterns in references. If a reference does not change a decision, validation map, risk owner, or loading choice, do not load it.

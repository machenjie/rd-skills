# Technology Stack Benchmarks And Patterns

Use this reference when a stack decision needs candidate matrices, decision rubric depth, validation mapping, managed-vs-self-managed economics, reversibility classes, or anti-pattern review. Keep `SKILL.md` focused on routing, evidence, and quality gates.

## Candidate Fit Matrix

This matrix is a starting point, not approval evidence. Current product constraints, repository graph, support policy, and workload validation decide the outcome.

| Decision axis | Strong evidence | Reject or defer when |
| --- | --- | --- |
| Constraint fit | Candidate satisfies hard latency, data residency, compliance, deployment, offline, and integration constraints. | A hard constraint is unverified or requires unowned mitigation. |
| Existing-stack sufficiency | Approved stack inventory shows an existing option can meet the requirement within accepted cost and risk. | Novel stack is chosen before proving existing stack insufficiency. |
| Maturity and support | 3+ years production use at comparable scale, 2+ maintainers or vendor SLA, CVE disclosure, current support policy. | Pre-1.0, single maintainer, unsupported version, unclear EOL, or abandoned issue tracker. |
| Operational ownership | Named team accepts on-call, upgrades, incident debugging, and security patching. | Ownership is assumed, deferred, or assigned to a team that has not accepted it. |
| Security and supply chain | License, package integrity, vulnerability process, OpenSSF/SLSA/Scorecard or equivalent posture reviewed. | Install scripts, weak provenance, critical CVEs, or license risks lack owner approval. |
| TCO and hiring | 3-year cost covers managed/license fees, engineer-FTE operational tax, hiring or upskilling, and migration. | Cost model ignores on-call, upgrades, telemetry, incident training, or exit cost. |
| Reversibility | Exit path, migration/coexistence plan, rollback trigger, and re-evaluation date are explicit. | Switch cost is unknown or rollback is really a rewrite. |

## Decision Rubric Depth

Apply in order and stop when a hard gate fails:

1. Name product constraints and hard disqualifiers.
2. Inventory existing approved stacks and decide whether a boring option is sufficient.
3. Score 2-3 candidates with explicit weights tied to product priorities.
4. Check maturity, support horizon, supply-chain posture, and official lifecycle sources.
5. Name operational, upgrade, security, and incident owners.
6. Estimate 3-year TCO and exit cost in engineer-quarters.
7. Map accepted risks to validation and specialist gates.
8. Record rejected options with the specific cost or constraint that rejected them.

## Stack-To-Validation Map

| Accepted risk | Minimum validation | Typical next gate |
| --- | --- | --- |
| New runtime or language | workload classification, build lane, deploy artifact, owner, support policy | `language-runtime-selection` |
| New package ecosystem | lockfile policy, vulnerability/license scan, package integrity, transitive risk | `package-dependency-management` |
| New datastore, queue, cache, or search engine | migration/coexistence plan, load profile, failure-mode test, rollback trigger | `data-middleware-change-builder` |
| Managed service adoption | unit cost, quota/limit review, outage mode, export/exit path, owner | `reliability-observability-gate` |
| New deploy or container substrate | CI command, artifact shape, rendered config, rollback plan | `delivery-release-gate` |
| Security or trust-boundary shift | threat boundary, data classification, dependency posture, denied/abuse case | `security-privacy-gate` |
| Irreversible or high-exit-cost choice | ADR, exit budget, migration window, re-evaluation trigger, accountable owner | `architecture-tradeoff-analysis` |

## Managed vs Self-Managed Calculation

Compare managed cost against loaded operational cost:

- loaded engineer hourly cost times weekly operations, upgrades, security patching, incident response, and observability work;
- managed service bill, quota risk, egress/storage growth, support tier, and vendor lock-in;
- failure cost for outage, data loss, migration, and rollback;
- hiring and training cost when the stack is rare.

Managed is often cheaper when the team lacks deep operating expertise or when monthly cost is below the loaded cost of even fractional on-call and patching work. Self-managed may be justified when scale, regulatory constraints, or unit economics outweigh the operational burden and the owner accepts it.

## Reversibility Classes

| Class | Meaning | Required evidence |
| --- | --- | --- |
| Reversible | Can switch by config, adapter, feature flag, or small migration without customer-visible window. | Rollback command, owner, and validation command. |
| Conditionally reversible | Exit requires data migration, client migration, or coexistence window but is feasible within months. | Migration plan, compatibility window, rollback trigger, and data owner. |
| Irreversible | Exit is a rewrite, cloud/platform move, or long customer migration. | ADR, 2x exit budget, accountable owner, sunset or re-evaluation plan. |

## Anti-Pattern Review

- Stack selected from fashion, resume value, or generic reputation without current constraints.
- Existing approved stack inventory skipped.
- Public benchmark cited without matching workload, version, data size, or topology.
- Owner acceptance deferred until after the stack enters production.
- Managed-vs-self-managed decision ignores loaded engineer cost.
- "Cloud-agnostic" wrapper built without a plausible exit trigger.
- Project memory or old ADR used after support policy, workload, or repository graph changed.
- Rejected alternatives say "worse" instead of naming cost, constraint, or risk.

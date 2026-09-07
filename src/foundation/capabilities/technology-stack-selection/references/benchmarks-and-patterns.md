# Stack Commitment Comparison

This matrix compares technology commitments against current system facts, owned operating obligations, and a credible migration and exit path.

## Commitment Decision Matrix

| Stack facet | Facts that distinguish candidates | Rejection or residual signal |
| --- | --- | --- |
| Hard compatibility | Product behavior, data model and residency, protocols, identity, compliance, target platforms, offline mode, integrations, and recovery | A required surface is unsupported or depends on an unowned adapter or exception |
| Existing-stack fit | Current approved components, reusable capabilities, known failure modes, operating evidence, and integration evidence | A new stack is preferred before the known option's concrete mismatch is shown |
| Operational ownership | Deploy, observe, debug, upgrade, patch, back up, restore, scale, and retire responsibilities | A team is named without accepting the incident and lifecycle work |
| Lifecycle and supply chain | Supported versions, release policy, end-of-life signals, continuity, provenance, license, vulnerability handling, install behavior, and transitive exposure | Support or integrity claims lack a current source, date, owner, or mitigation |
| Total-change cost | Implementation, migration, coexistence, operation, incidents, upgrades, usage growth, exit, and sensitivity to uncertain assumptions | Cost is a point estimate or excludes transition, recurring, and exit work |
| Migration and coexistence | Data and protocol conversion, old/new consumers, generated artifacts, build/deploy lanes, observability, rollback, and recovery sequencing | Cutover depends on a flag while durable state or consumers cannot move back |
| Reversibility and proof | Exit unit, switching cost, information loss, staged feasibility evidence, representative workload, and unproved boundaries | Prototype or public benchmark scope is treated as production or long-horizon proof |

## Decision Rules

- Screen candidates against hard product, data, protocol, identity, compliance, deployment, offline, integration, and recovery constraints before comparing preferences.
- Treat an approved existing stack as a candidate with known integration and operating evidence, not as an automatic winner; a new stack states the concrete gap it closes.
- Before commitment, name owners for the deployment, on-call diagnosis, upgrade, security-response, recovery, capacity, and retirement duties that the selected stack actually creates.
- Inspect stack-level support, end-of-life, continuity, and supply-chain exposure using dated findings from the named package-mechanics and package-risk owners.
- Compare total-change cost across the accepted decision horizon using dated assumptions, ranges, and sensitivity for implementation, migration, coexistence, operation, incidents, upgrades, and exit.
- Define migration and coexistence across data, protocols, generated artifacts, package managers, build/deploy lanes, observability, rollback, and old/new consumer compatibility.
- Classify reversibility from the actual exit unit and information movement; prototypes and public benchmarks establish scoped feasibility rather than production readiness.

## Decision Limits

- Use hard constraints as gates; scoring can organize remaining tradeoffs but does not compensate for a failed gate.
- Date support, pricing, vulnerability, ecosystem, and capacity inputs, and state the condition that makes each volatile assumption stale.
- Route language/runtime, packages, build, configuration, architecture, and release mechanics to their specialist owners before closing the stack decision.

## Anti-Patterns

- A weighted score lets a hard compatibility, security, ownership, or migration gap disappear inside a total.
- Fashion or generic reputation substitutes for current constraints and workload evidence.
- Entry price excludes on-call, upgrade, incident, coexistence, data movement, or exit work.
- A prototype or vendor benchmark is extrapolated across different scale, topology, failure modes, versions, or data shapes.

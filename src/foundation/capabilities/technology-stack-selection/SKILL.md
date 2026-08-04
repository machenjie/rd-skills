---
name: technology-stack-selection
description: "`analysis-agent`/`task-agent`/`review-agent`: use when a framework, platform, infrastructure, or managed service creates a commitment; skip package, runtime, or fixed-stack work."
---

# technology-stack-selection

## Registry Trigger

**Use when**

- A new or replaced framework, platform, datastore class, infrastructure component, or managed service changes system compatibility, operation, migration, or exit.
- Existing and new stack options remain feasible under product, deployment, security, ownership, or lifecycle constraints.

**Do not use when**

- The open decision is a programming language/runtime, individual package, build-tool, or runtime-configuration choice.
- Architecture or policy already fixes the stack and the task introduces no new technology commitment or migration decision.

## Skill Role

Select a technology-stack commitment from compatibility, operational ownership, lifecycle and supply-chain exposure, total-change cost, migration, coexistence, and exit risk. Exclude language, package, build, and runtime-configuration decisions.

## High-Value Rules

- Screen candidates against hard product, data, protocol, identity, compliance, deployment, offline, integration, and recovery constraints before comparing preferences.
- Treat an approved existing stack as a candidate with known integration and operating evidence, not as an automatic winner; a new stack states the concrete gap it closes.
- Before commitment, name owners for the deployment, on-call diagnosis, upgrade, security-response, recovery, capacity, and retirement duties that the selected stack actually creates.
- Inspect stack-level support, end-of-life, continuity, and supply-chain exposure using dated findings from the named package-mechanics and package-risk owners.
- Compare total-change cost across the accepted decision horizon using dated assumptions, ranges, and sensitivity for implementation, migration, coexistence, operation, incidents, upgrades, and exit.
- Define migration and coexistence across data, protocols, generated artifacts, package managers, build/deploy lanes, observability, rollback, and old/new consumer compatibility.
- Classify reversibility from the actual exit unit and information movement; prototypes and public benchmarks establish scoped feasibility rather than production readiness.

## Anti-Patterns

- A weighted score lets a hard compatibility, security, ownership, or migration gap disappear inside a total.
- Fashion or generic reputation substitutes for current constraints and workload evidence.
- Entry price excludes on-call, upgrade, incident, coexistence, data movement, or exit work.
- A prototype or vendor benchmark is extrapolated across different scale, topology, failure modes, versions, or data shapes.

## Stop Conditions

- Route architecture-wide boundary or ADR work to `architecture-tradeoff-analysis`, language changes to `language-runtime-selection`, and broader option comparison to `solution-optimality-evaluation`.
- Route package resolution, lockfile, and install mechanics to `package-dependency-management`.
- Route vulnerability reachability, malicious-package, and license-exception acceptance to `dependency-vulnerability-scanning`.
- Route build lanes to `build-tool-professional-usage`, runtime policy to `configuration-runtime-policy`, and rollout or coexistence to `delivery-release-gate`.

## Output Contract

- technology-stack decision with hard-constraint fit existing-stack comparison ownership lifecycle supply chain total-change cost migration coexistence exit proof limits and residual risk

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [benchmarks and patterns](references/benchmarks-and-patterns.md) | benchmark-pattern | Competing technology-stack commitments require compatibility ownership supply-chain migration cost or exit comparison | Current architecture and policy fix the technology stack and no new commitment or migration is proposed | analysis-agent, task-agent, review-agent | option-comparison, selected-approach |

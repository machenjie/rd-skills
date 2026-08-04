---
name: cloud-platform-extension
description: Use when a selected Professional decision materially depends on confirmed cloud-provider policy, ownership, or behavior.
---

# cloud-platform-extension

## Role

This focused Layer 3 Domain Skill modifies a selected Professional Skill for `analysis-agent`, `task-agent`, and `review-agent`. It is never a Professional owner. `platform-infrastructure-change-builder` owns cloud and infrastructure-as-code source changes; backend, security, or reliability Professionals may load it when cloud policy materially changes their decision. A `review-agent` must load it.

## When To Use

- Use when confirmed cloud ownership, service, location, identity, network, capacity, key, cost, or provider API policy changes the decision.
- Use only within the Professional workflow.

## Do Not Use

- Do not use for unknown cloud scope, provider-name-only or language-only work, local Kubernetes, generic backend work without a cloud control-plane dependency, or release authorization.
- Do not create provider-specific top-level Skills or duplicate infrastructure-as-code state, plan, drift, identity, or recovery workflow.

## Required Inputs

- Record provider, account/project/subscription, environment, owners, region/zone, plane operations, and source authority.
- Record identity trust, network, service responsibility, capacity/consistency, key authority, versions, and non-production evidence.

## Professional Decision Rules

- Bind every resource to its account/project/subscription, hierarchy, billing owner, environment, and inherited policy boundary.
- Classify runtime and recovery operations by service-specific control or data plane; minimize dependence on impaired management operations.
- Model principal, issuer, audience, trust side, resource side, cross-boundary policy, credential lifetime, and workload identity without assuming federation proves least privilege.
- Prove route, DNS, endpoint, filtering, egress, shared-network ownership, and transitivity; hierarchy separation alone proves no connectivity outcome.
- State actual region, zone, replication, residency, and failure-domain behavior; treat multi-region and managed-service guarantees as service-specific.
- Query live effective quota, throttle headers, propagation state, key status, provider registration, API support, and current cost when those conditions can invalidate the decision.
- Define bounded retry, idempotency, unknown-result, and pending-state behavior per operation; publish no universal propagation or convergence promise.
- Keep provider and customer managed-service authority explicit.
- Route production apply, rollout, release, and rollback to `delivery-release-gate`.

## High-Value Gotchas

- A hierarchy can inherit broad IAM while providing no network or runtime isolation.
- A documented quota, requested increase, budget, or regional label can be mistaken for live capacity, a hard cost cap, or failover proof.
- A key replica, alias, provider version, or managed service can hide independent policy, lifecycle, or customer obligations.
- Layered retries can amplify throttling and repeat non-idempotent operations after an unknown result.

## Execution Checklist

- Load only the active decision family's Reference and preserve the selected Professional owner's acceptance.
- Verify normal, denied, throttled, pending, degraded, cross-boundary, and recovery behavior against the exact environment.
- Report source freshness, live checks performed, unverified provider state, non-inferences, and residual risk.

## Stop / Escalation Conditions

- Stop when account/project/subscription, resource owner, authority, region, plane, or decision-critical live provider state remains unresolved.
- Keep production mutation and release authority outside this modifier.

## Output Contract

Return the selected Professional owner, cloud boundary decision, rejected alternative, authority and resource owners, normal and failure behavior, live-state evidence, and validation plan. Include source freshness, proof limits, and residual risk.

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [resource control and data plane boundaries](references/resource-control-and-data-plane-boundaries.md) | targeted | hierarchy ownership billing inherited policy control-plane or data-plane classification affects the decision | ownership and plane authority are accepted and cannot change recovery or runtime behavior | analysis-agent, task-agent, review-agent | boundary-decision, decision-record, proof-limit |
| [iam workload identity and network contracts](references/iam-workload-identity-and-network-contracts.md) | targeted | IAM federation cross-boundary trust VPC VNet subnet route DNS endpoint or shared-network behavior changes | no identity trust authorization or cloud network boundary changes | analysis-agent, task-agent, review-agent | boundary-decision, failure-decision, validation-plan |
| [region failure domain consistency and quota contracts](references/region-failure-domain-consistency-and-quota-contracts.md) | targeted | region zone replication residency quota throttle retry propagation or failover behavior affects acceptance | no location capacity propagation retry or failure-domain decision changes | analysis-agent, task-agent, review-agent | decision-record, proof-limit, validation-plan |
| [encryption kms and cost contracts](references/encryption-kms-and-cost-contracts.md) | targeted | key authority location rotation replication deletion recovery budget or cost blast radius changes | no cloud key lifecycle encryption cost owner or material resource-spend dimension changes | analysis-agent, task-agent, review-agent | boundary-decision, failure-decision, residual-risk |
| [provider api and managed service authority](references/provider-api-and-managed-service-authority.md) | targeted | provider SDK service API version lifecycle managed-service responsibility or customer authority changes | no provider compatibility managed-service authority or operational ownership decision changes | analysis-agent, task-agent, review-agent | decision-record, proof-limit, validation-plan |

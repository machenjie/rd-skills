---
name: cloud-platform-extension
description: Use when a selected Professional decision materially depends on confirmed cloud-provider policy, ownership, or behavior.
---

# cloud-platform-extension

## Role

This focused Layer 3 Domain Skill modifies the selected Professional decision
for `analysis-agent`, `task-agent`, and `review-agent` with confirmed cloud
authority; it never becomes the Professional owner. Infrastructure source
remains with `platform-infrastructure-change-builder`.

## When To Use

- confirmed cloud ownership, service, location, identity, network, capacity, key, cost, or provider API policy changes the Professional decision

## Do Not Use

- unknown cloud scope, provider-name/language-only work, local Kubernetes, generic backend work without cloud authority, or release authorization
- never create provider-specific top-level Skills or duplicate infrastructure state, plan, drift, identity, or recovery ownership

## Required Inputs

- provider, account/project/subscription, environment, owner, region/zone, plane, source authority
- identity, network, service, and capacity facts
- evidence-backed key-lifecycle facts
- evidence-backed provider-version facts

## Professional Decision Rules

- Preserve the selected Professional as decision owner.
- Bind the active cloud resource, plane, identity, network, location, capacity, key, cost, provider API, and managed-service authority to the exact environment.
- Load only the active decision family's Reference.

## High-Value Gotchas

- Hierarchy, quota, region, key alias, managed-service label, or layered retry is not live isolation, capacity, recovery, authority, or safe replay proof.

## Execution Checklist

1. Confirm the cloud owner, environment, plane, and active decision family.
2. Load only that family's Reference and preserve the selected Professional.
3. Report live evidence, proof limits, validation, and residual risk.

## Stop / Escalation Conditions

- Stop when account/project/subscription, resource owner, authority, region, plane, or decision-critical live state remains unresolved; keep production mutation and release authority outside this modifier.

## Output Contract

- selected Professional, cloud decision, rejected alternative, owners, normal/failure behavior, live evidence, validation, freshness, proof limits, residual risk

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [resource control and data plane boundaries](references/resource-control-and-data-plane-boundaries.md) | targeted | hierarchy ownership billing inherited policy control-plane or data-plane classification affects the decision | ownership and plane authority are accepted and cannot change recovery or runtime behavior | analysis-agent, task-agent, review-agent | boundary-decision, decision-record, proof-limit |
| [iam workload identity and network contracts](references/iam-workload-identity-and-network-contracts.md) | targeted | IAM federation cross-boundary trust VPC VNet subnet route DNS endpoint or shared-network behavior changes | no identity trust authorization or cloud network boundary changes | analysis-agent, task-agent, review-agent | boundary-decision, failure-decision, validation-plan |
| [region failure domain consistency and quota contracts](references/region-failure-domain-consistency-and-quota-contracts.md) | targeted | region zone replication residency quota throttle retry propagation or failover behavior affects acceptance | no location capacity propagation retry or failure-domain decision changes | analysis-agent, task-agent, review-agent | decision-record, proof-limit, validation-plan |
| [encryption kms and cost contracts](references/encryption-kms-and-cost-contracts.md) | targeted | key authority location rotation replication deletion recovery budget or cost blast radius changes | no cloud key lifecycle encryption cost owner or material resource-spend dimension changes | analysis-agent, task-agent, review-agent | boundary-decision, failure-decision, residual-risk |
| [provider api and managed service authority](references/provider-api-and-managed-service-authority.md) | targeted | provider SDK service API version lifecycle managed-service responsibility or customer authority changes | no provider compatibility managed-service authority or operational ownership decision changes | analysis-agent, task-agent, review-agent | decision-record, proof-limit, validation-plan |

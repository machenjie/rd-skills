# IAM, Workload Identity, and Network Contracts

Load this Reference only when cloud authorization, federation, cross-boundary
trust, routing, filtering, DNS, endpoint, or shared-network behavior changes.

Official AWS, Azure, and Google Cloud documentation below was accessed on
2026-07-24.

## Identity Boundary

- Record principal, issuer, audience, subject or attributes, trust side,
  resource side, inherited policy, conditions, and session lifetime.
- Prefer short-lived workload federation over embedded long-lived credentials;
  federation alone proves neither least privilege nor resource authorization.
- Verify both caller and resource policy for cross-boundary access.

## Network Boundary

- Trace address, route, propagation and transitivity, filter, DNS, public or
  private endpoint, egress, service attachment, and shared-network owner.
- Do not infer reachability from a shared hierarchy or isolation from separate
  accounts, projects, or subscriptions.
- Prove intended allow and deny paths from the real workload identity and path.

## Required Record

Return the trust graph, credential lifecycle, both-side authorization, complete
network path, ownership, denial proof, unverified live state, and residual risk.

## Primary Sources

- [AWS cross-account policy evaluation](https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_policies_evaluation-logic-cross-account.html)
- [AWS VPC operation](https://docs.aws.amazon.com/vpc/latest/userguide/how-it-works.html)
- [Azure Workload ID](https://learn.microsoft.com/en-us/azure/aks/workload-identity-overview)
- [Azure virtual networks and subnets](https://learn.microsoft.com/en-us/azure/networking/design-guide/vnets-subnets)
- [Google Cloud Workload Identity Federation](https://docs.cloud.google.com/iam/docs/workload-identity-federation)
- [Google Cloud VPC](https://docs.cloud.google.com/vpc/docs/vpc)

## Source Limits

Identity and network products differ by service and version. These pages prove
neither live grants, credential state, route propagation, DNS, endpoint policy,
reachability, transitivity, nor least privilege.

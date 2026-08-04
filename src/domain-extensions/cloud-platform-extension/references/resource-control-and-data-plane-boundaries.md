# Resource, Control, and Data Plane Boundaries

Load this Reference only when cloud hierarchy, ownership, inherited policy,
billing, or control/data-plane classification changes the decision.

Official AWS, Azure, and Google Cloud documentation below was accessed on
2026-07-24.

## Resource Boundary

- Record the owning AWS account, Azure subscription and management group, or
  Google Cloud organization, folder, and project for each resource.
- Separate hierarchy, inherited governance, billing, environment, application,
  failure, and network boundaries; one does not prove another.
- Name the resource owner, policy owner, cost owner, and cross-boundary grant.

## Plane Boundary

- Classify every operation by its service-specific control or data plane.
- Keep runtime and recovery paths usable when avoidable management mutations,
  discovery, IAM, DNS, or scaling operations are impaired.
- Determine the plane from the exact action, not its tool name or HTTP verb.

## Required Record

Return the hierarchy and ownership map, inherited policy and billing boundary,
operation-by-plane matrix, unavailable-plane behavior, and residual risk.

## Primary Sources

- [AWS multi-account governance](https://docs.aws.amazon.com/wellarchitected/latest/management-and-governance-guide/manage-and-govern-with-a-multi-account-point-of-view.html)
- [AWS control planes and data planes](https://docs.aws.amazon.com/whitepapers/latest/aws-fault-isolation-boundaries/control-planes-and-data-planes.html)
- [Azure subscriptions as management units](https://learn.microsoft.com/en-us/azure/cloud-adoption-framework/ready/landing-zone/design-principles)
- [Azure control plane and data plane](https://learn.microsoft.com/en-us/azure/azure-resource-manager/management/control-plane-and-data-plane)
- [Google Cloud resource hierarchy](https://docs.cloud.google.com/resource-manager/docs/cloud-platform-resource-hierarchy)

## Source Limits

Architecture guidance does not prove a deployed topology, inherited policy,
network isolation, billing owner, service plane, or current authority. Inspect
the exact environment and operation.

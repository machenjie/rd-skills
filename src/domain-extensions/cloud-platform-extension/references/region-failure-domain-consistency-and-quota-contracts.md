# Region, Failure Domain, Consistency, and Quota Contracts

Load this Reference only when location, replication, failover, quota,
throttling, retry, or propagation behavior affects the decision.

Official AWS, Azure, and Google Cloud documentation below was accessed on
2026-07-24.

## Location and Capacity

- Record resource location, region, zone, actual replication, residency,
  failure domain, service support, and failover authority.
- Query the live effective quota for the exact account/project/subscription,
  region, resource, and service; distinguish default, applied, adjustable,
  fixed, and requested values.
- Obtain capacity evidence before depending on scale or failover.

## Consistency and Retry

- Treat create, update, IAM, and failover state as pending until observable
  through the required read and use path.
- Retry only service-classified retryable and idempotent operations with bounded
  exponential backoff, jitter, and a retry budget.
- Handle unknown results and retry an entire read-modify-write transaction when
  its service contract requires it.

## Required Record

Return the location and failure-domain model, live quota lookup, pending-state
oracle, retry and idempotency decision, failover evidence, and residual risk.

## Primary Sources

- [AWS Regions and Availability Zones](https://docs.aws.amazon.com/global-infrastructure/latest/regions/aws-regions-availability-zones.html)
- [AWS Service Quotas](https://docs.aws.amazon.com/servicequotas/latest/userguide/intro.html)
- [AWS SDK retry behavior](https://docs.aws.amazon.com/sdkref/latest/guide/feature-retry-behavior.html)
- [Azure availability zones](https://learn.microsoft.com/en-us/azure/reliability/availability-zones-overview)
- [Azure subscription and service limits](https://learn.microsoft.com/en-us/azure/azure-resource-manager/management/azure-subscription-service-limits)
- [Google Cloud regions and zones](https://docs.cloud.google.com/docs/geography-and-regions)
- [Google Cloud quotas](https://docs.cloud.google.com/docs/quotas/overview)

## Source Limits

Support, quotas, propagation, retry classifications, capacity, and availability
are service-, account-, location-, and time-specific. Publish no universal
sleep, convergence, failover, multi-region, or capacity guarantee.

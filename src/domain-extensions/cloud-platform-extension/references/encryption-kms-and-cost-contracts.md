# Encryption, KMS, and Cost Contracts

Load this Reference only when cloud key lifecycle, encryption authority, or
material resource and failure cost changes the decision.

Official AWS, Azure, and Google Cloud documentation below was accessed on
2026-07-24.

## Key Boundary

- Record vault, HSM, key ring, key-material and policy owners, location, alias,
  grants, and current enabled and primary state.
- Record rotation, decrypt compatibility, replication lag, deletion,
  soft-delete, recovery, and audit paths.
- Treat replica policy and state as provider-specific; verify the live key and
  recovery path before changing encrypted data or state.
- Prove old and new ciphertext recovery across rotation and rollback.

## Cost Boundary

- Quantify resources, replicas/regions, storage, telemetry, traffic/egress,
  retry amplification, managed-service tier, and failure demand.
- Assign a cost owner and inspect current prices, discounts, capacity, forecast,
  budget scope, and alert delay.
- Treat budgets as observation unless the exact service proves enforcement;
  never infer a hard cap or safe automated shutdown.

## Required Record

Return key authority and lifecycle, decrypt and recovery proof, cost dimensions,
live estimate owner, budget limitations, unverified state, and residual risk.

## Primary Sources

- [AWS KMS multi-Region keys](https://docs.aws.amazon.com/kms/latest/developerguide/multi-region-keys-overview.html)
- [AWS Budgets](https://docs.aws.amazon.com/cost-management/latest/userguide/budgets-managing-costs.html)
- [Azure Managed HSM multi-region replication](https://learn.microsoft.com/en-us/azure/key-vault/managed-hsm/multi-region-replication)
- [Azure budgets](https://learn.microsoft.com/en-us/azure/cost-management-billing/costs/tutorial-acm-create-budgets)
- [Google Cloud KMS locations](https://docs.cloud.google.com/kms/docs/locations)
- [Google Cloud budgets](https://docs.cloud.google.com/billing/docs/how-to/budgets)

## Source Limits

Static documentation proves no live key state, replication completion, price,
discount, capacity, forecast, spend, alert timing, or recovery. Provider and
service semantics must not be unified into a generic guarantee.

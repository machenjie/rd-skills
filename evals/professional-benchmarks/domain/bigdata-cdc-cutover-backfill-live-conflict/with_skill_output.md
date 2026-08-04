# Distributed Data Review

Primary Professional Skill: `data-middleware-change-builder`  
Selected Domain Skill: `bigdata-product-extension`

## Hidden risks

- snapshot-to-CDC cutover can omit or duplicate transactions
- resumed backfill can overwrite a newer live correction
- late corrections can publish inconsistent downstream totals

## Required evidence

- cutover position and transaction-order fixture
- overlapping backfill and live-writer conflict test
- authoritative-total reconciliation after late correction

## Handoff

- source of truth and writer ownership
- cutover checkpoint resume and replay contract
- reconciliation results proof limits and residual owner

Block promotion until snapshot and log positions form one ordered handoff, live and historical writers have explicit serialization or precedence, resume is idempotent, and consumer-visible totals reconcile after delayed corrections.

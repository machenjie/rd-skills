# Completeness, Identity, And Time

**Load when:** Audit coverage, actor/service fidelity, time uncertainty, ordering, correlation, or causality remains unresolved.

**Do not load when:** Work only selects record placement/schema, or current reconciliation proves complete attribution for the bounded audit question.

**Required by:** `analysis-agent`, `task-agent`, `review-agent`

**Required output:** `decision-record`, `boundary-decision`, `proof-limit`

## Root-Relocated Coverage Rules

- Define the audit question, critical outcomes and sources, expected records, time window, and completeness reconciliation.
- Preserve authoritative human/service identity, effective actor, delegation, session, tenant, purpose, and stable causation/correlation identities.
- Record occurrence, commit, and receipt time with source, offset, sync health, precision, uncertainty, and no unsupported global order.
- A critical event is missing without a coverage alarm.
- Shared actor identity hides who acted.
- Clock skew is misrepresented as reliable order.
- Broken correlation severs cause from outcome.
- Generate normal, denied, failed, delegated, administrative, and partial paths; reconcile expected records.

## Coverage And Attribution Decision

Bind question/exclusions, record/source/schema identity, actor/delegation/tenant, clocks/uncertainty, supported order, causal/retry/effect identities, and late/duplicate/gap reconciliation with owner/deadline.

## Verification, Sources, And Limits

Exercise scoped outcomes, reconcile delivery, skew clocks, and substitute attribution/correlation. Sources: [NIST 800-53](https://csrc.nist.gov/pubs/sp/800/53/r5/upd1/final), [NIST 800-92](https://csrc.nist.gov/pubs/sp/800/92/final), [RFC 8633](https://www.rfc-editor.org/rfc/rfc8633.html), [CloudTrail records](https://docs.aws.amazon.com/awscloudtrail/latest/userguide/cloudtrail-event-reference-record-contents.html), and [CloudTrail ordering](https://docs.aws.amazon.com/awscloudtrail/latest/userguide/cloudtrail-events.html), accessed 2026-07-26. They do not prove configured coverage, identity truth, delivery or global order; defaults remain product-specific.

# Architecture Option Check

**Load when:** an architecture decision adds or moves a module, service, data owner, runtime boundary, dependency direction, or operational responsibility and a material alternative remains.

**Do not load when:** the change is owner-internal with no structural impact, or placement is already established by current repository evidence.

Derive thresholds from the current repository baseline, representative workload, user/business objective, platform policy, and measured evidence; candidate topologies and governance mechanisms are not defaults.

## Decision Questions

1. Which present ownership, change-locality, deployment, scale, or consistency constraint requires the proposed boundary, and can an existing module or smaller local change meet it?
2. How do public or indirect consumers, authoritative data ownership, and effective dependency edges change, and what current source/contract evidence bounds that impact?
3. If runtime topology changes, what failure, latency, capacity, availability, and operational-ownership consequence follows under the actual platform and workload?
4. How can the decision be removed, migrated, or contained, and does current policy or impact justify automated enforcement or an ADR rather than source evidence alone?
5. If multiple architecture-wide tradeoffs remain unresolved, record broader tradeoff analysis as unresolved scope with its evidence need and decision owner.

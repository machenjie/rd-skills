# Command Risk Classification Checklist

Classify each field as supported or unresolved from current task-local evidence.

| Field | Evidence question |
| --- | --- |
| Exact target | Which paths, resources, records, services, or recipients can the operation reach? |
| Mutation surface | Which direct or indirect state changes, generated outputs, subprocesses, or callbacks can occur? |
| Reversibility | Can the original state be restored without assuming an unverified backup or compensating action? |
| Recovery | Which tested restore, rollback, rebuild, retry-safe, or compensation mechanism applies? |
| External effects | Which remote calls, messages, disclosures, charges, or durable service changes can occur? |
| Capability facts | Which current execution capabilities are established by their existing owner? |
| Authorization facts | Which current grants and scope limits are established by their existing owner? |
| Unresolved ambiguity | Which expansion, dynamic target, transitive tool, hook, callback, or missing fact prevents a complete classification? |

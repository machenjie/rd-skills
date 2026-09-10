# Data Migration Design Checklist

- Define migration goal, affected data, and estimated volume.
- Select expand, migrate, contract, or cleanup phases from actual version skew, consumer control, and recovery needs.
- Define each selected phase's exit.
- Define code and schema deployment order.
- Make migration repeatable or guarded with checkpoints.
- Define batching, rate limits, locks, and runtime limits.
- Define observability for progress, failures, duration, and validation counts.
- Define interruption and resume behavior.
- Define rollback, compensation, backup, or containment plan.
- Define cleanup criteria and owner signoff.

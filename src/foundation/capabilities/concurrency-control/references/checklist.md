# Concurrency Control Checklist

- Map each shared resource to actors, invariant, current source path, transaction or queue boundary, and overlapping execution scenario.
- Choose the narrowest control from atomic statements, optimistic versions, constraints, compare-and-swap, scoped locks, queue partitioning, outcome storage, leases, or fencing based on the actual invariant and platform guarantees.
- Record rejected mechanisms and why they were too broad, too weak, too slow, or owned by another capability.
- For each actor that can encounter a concurrency conflict, define the applicable detection and caller-visible terminal outcome; specify retry/backoff or timeout behavior when that actor can retry or wait.
- When equivalent submissions or workers can overlap, select a control from the actual overlap window, business identity, in-flight behavior, winning-effect authority, loser outcome, result reuse, effect semantics, and storage guarantees.
- Analyze lock ordering, duration, I/O while held, deadlock paths, hot resources, contention evidence, and cleanup on partial acquisition.
- When cancellation, timeout, or lease expiry ends ownership, stop renewal, verify current ownership before release, and fence later side effects from the expired owner; define cleanup when renewal, cancellation, and completion race.
- When an event follows a state change, bind publication to committed state with a storage- and topology-supported mechanism. Expose and recover the crash window without allowing rolled-back state to produce a consumer-visible event.
- For any version, pointer, slot, or ownership value that can wrap or be reused, test ABA and stale-observer paths. Choose a generation, epoch, token identity, or equivalent non-reuse proof from lifetime and storage guarantees.
- When scheduling or contention can starve an actor or invert priority, define accepted degradation, mitigation authority, and terminal outcome from representative wait, queue, and priority-interaction measurements.
- Select deterministic overlap, stress, race, redelivery, cancellation, expiry, and starvation evidence from reachable risks; name command, outcome, exit status, and artifact or report when executed.
- When ownership, expiry, or ordering depends on time, identify the authoritative lease or token state and relevant platform clock behavior. Require current ownership evidence before effects instead of inferring ownership from wall-clock order alone.

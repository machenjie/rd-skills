# Architecture decision

Selected `architecture-impact-reviewer` with `module-boundary-design`, `consumer-impact-analysis`, and `architecture-tradeoff-analysis`.

Revise the proposal because configuration and reflection can hide indirect consumers, dual authoritative stores create conflicting source of truth, proposed dependency direction conflicts with the repository model, shared abstraction has only one proven consumer, and cutover and rollback ownership are undefined.

Required proof is a consumer search across code configuration reflection and runtime registration, a source-of-truth and write-owner invariant, actual dependency graph and architecture-test output, a simpler local placement comparison, and cutover rollback and compatibility proof.

The review handoff must provide an approve reject or revise verdict, the target owner and dependency direction, consumer and compatibility impact, and migration rollback and unresolved evidence. Keep the rule local unless a second real owner justifies extraction; designate one write authority; and make the temporary coexistence window, rollback owner, and removal condition explicit.

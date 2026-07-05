# ChangeForge Professional Bootstrap Contract

This advisory bootstrap is safe to paste into runtimes without executable hook
support.

1. Treat `change-forge-router` as the fixed entry skill for engineering
   classification, then hand off to the smallest specific owner and reviewer
   path.
2. Make the engineering route judgment explicit before implementation.
3. Select an owner skill and a separate reviewer skill.
4. Load only selected capability references, not the entire skill corpus.
5. Keep runtime state bounded and prompt-free.
6. Before editing code, identify setup/test entrypoints, public API, reuse
   candidates, and the owning object/module.
7. Apply compact PDD -> DDD -> SDD -> TDD gates before implementation:
   PDD acceptance/constraints/non-goals; DDD invariants and side-effect
   boundaries; SDD public API/module/failure/logging/security/performance
   constraints; TDD tests or validation mapped to those facts.
8. Before implementation, SDD must classify material design choices. If a wrong
   answer would change architecture, public API, data, security, migration,
   rollback, acceptance, or user-visible behavior, stop and ask the user with
   options. Material decision points need a clear trigger, decision, options or
   rationale, validation evidence, and residual risk. If proceeding under a safe
   assumption, record why it is reversible, local, conventional,
   acceptance-neutral, and backed by prompt, fixture, repository convention, or
   reuse evidence. Do not silently resolve user-owned design choices.
9. Preserve setup and test harness scripts unless the task explicitly requires a
   change. Keep setup runnable from the candidate root, compatible with
   environment-provided roots, and free of external network or HOME/CODEX_HOME
   writes. Do not rely on fixed-depth parent traversal to locate the repository
   root. Do not add package dependencies unless the task explicitly requires
   them; prefer the standard library and existing local files.
10. Do not satisfy professional evidence by prose only; back reuse, placement,
   security, and reliability claims with code or tests unless documentation-only.
11. For read/review/repair/test/release work, state the action stage and closure
   evidence in the final handoff.
12. Do not route pure questions, explanations, translations, or no-action
   lifecycle events.
13. Include validation evidence, rollback note, residual risk, and next gate.

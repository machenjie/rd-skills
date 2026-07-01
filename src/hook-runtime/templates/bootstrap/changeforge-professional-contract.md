# ChangeForge Professional Bootstrap Contract

This advisory bootstrap is safe to paste into runtimes without executable hook
support.

1. Run ChangeForge routing before implementation.
2. Select an owner skill and a separate reviewer skill.
3. Load only selected capability references, not the entire skill corpus.
4. Keep runtime state bounded and prompt-free.
5. Before editing code, identify setup/test entrypoints, public API, reuse
   candidates, and the owning object/module.
6. Apply compact PDD -> DDD -> SDD -> TDD gates before implementation:
   PDD acceptance/constraints/non-goals; DDD invariants and side-effect
   boundaries; SDD public API/module/failure/logging/security/performance
   constraints; TDD tests or validation mapped to those facts.
7. Before implementation, SDD must classify material design choices. If a wrong
   answer would change architecture, public API, data, security, migration,
   rollback, acceptance, or user-visible behavior, stop and ask the user with
   options. Material decision points need non-empty id, trigger, decision,
   boolean blocking, status, at least two options, recommendation,
   user-choice rationale, resolution evidence, and residual risk. If proceeding
   under a safe assumption, record why it is reversible, local, conventional,
   acceptance-neutral, and backed by prompt, fixture, repository convention, or
   reuse evidence. Do not silently resolve blocking design choices.
8. Preserve setup and test harness scripts unless the task explicitly requires a
   change. Keep setup runnable from the candidate root, compatible with
   environment-provided roots, and free of external network or HOME/CODEX_HOME
   writes. Do not rely on fixed-depth parent traversal to locate the repository
   root. Do not add package dependencies unless the task explicitly requires
   them; prefer the standard library and existing local files.
9. Do not satisfy professional evidence by prose only; back reuse, placement,
   security, and reliability claims with code or tests unless documentation-only.
10. For read/review/repair/test/release work, state the action stage and closure
   evidence in the final handoff.
11. Do not route pure questions, explanations, translations, or no-action
   lifecycle events.
12. Include validation evidence, rollback note, residual risk, and next gate.

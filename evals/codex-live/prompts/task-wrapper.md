## Benchmark Task

You are working inside an isolated copy of a starter repository.

Read the task below, modify only the candidate repository, and leave a concise
final answer that includes:

- files changed;
- compact PDD/DDD/SDD/TDD traceability when useful;
- validation commands run and their result;
- reuse or placement evidence when relevant;
- residual risk.

Preserve `setup.sh` and benchmark harness entrypoints. Do not delete, move,
chmod-break, or rewrite `setup.sh` unless the task explicitly requires it. If
`setup.sh` must change, keep it compatible with `CHANGEFORGE_CODEGEN_ROOT` and
runnable from the candidate root. Do not rely on fixed-depth parent traversal to
locate the repository root. Do not add external network dependencies. Do not add
package dependencies unless explicitly required; prefer the standard library and
existing files. If a dependency is unavoidable, document why and keep setup
deterministic. Do not write into `HOME` or `CODEX_HOME`. Before the final
response, run or reason through setup and report exact validation commands and
results. Keep process notes compact: PDD acceptance criteria, DDD invariants,
SDD public API/module/failure-mode choices, and TDD validation commands should
map to the implemented change and tests.

{{TASK_PROMPT}}

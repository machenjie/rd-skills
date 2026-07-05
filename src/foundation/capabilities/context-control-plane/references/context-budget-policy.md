# Context Budget Policy

## Budget Modes

- `minimal`: one direct task, one primary professional skill, and only direct source reads needed to act.
- `single-stage`: one stage dominates and selected companion references are needed for risk coverage.
- `staged-plan`: multiple stages, registries, hook runtime, evals, generated artifacts, or validation boundaries interact.
- `full`: exceptional route where omitting broader context would likely hide security, data loss, release, or systemic skill-regression risk.

## Budget Profiles

- `authoring`: default profile for skill-authoring and repository work where the pack may carry enough source evidence for review and handoff.
- `runtime`: tighter profile for route, hook, and active-context injection where the pack should act as a selector plus JIT read plan instead of carrying a broad source payload.

Runtime packs use lower file, symbol, and token ceilings. They must preserve source truth through targeted reads, deferred reads, forbidden reads, validation candidates, and residual risk rather than by expanding active context.

## Required Fields

Record `budget_mode`, `budget_profile`, `budget_rationale`, `context_budget_tokens`, selected counts, skipped counts, over-budget reason when applicable, and residual context risk. TaskContextPack v3 records these in `context_control`.

For context packs, record:

- selected file count and omitted file count;
- selected symbol count;
- selected graph node count and skipped graph node count;
- signal-density rationale explaining why the pack is sufficient;
- JIT retrieval plan for reads that were selected, deferred, or forbidden.

## Escalation

Escalate from `minimal` only when a named risk trigger, changed-path blast radius, stage transition, or validation dependency requires it. Do not escalate merely because more related references exist.

Do not solve context pressure by pasting graph output, full test logs, full command output, or generated artifacts into active context. Use artifact references, bounded summaries, and read slices.

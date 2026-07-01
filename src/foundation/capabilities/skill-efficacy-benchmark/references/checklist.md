# Skill Efficacy Benchmark Checklist

Use this checklist when drafting or reviewing a concrete skill efficacy case, routing/reference budget benchmark, score-improvement claim, or report-supported handoff.

## Case Definition

- Name the `case_id`, changed skill/capability/route/hook/eval surface, and behavior claim.
- State the bounded task and why the benchmark is needed instead of prose.
- Identify baseline artifact, treatment artifact, and any unavailable baseline reason.
- Keep the same task, route risk, source-vs-dist boundary, and runtime profile for baseline and treatment.

## Metric And Guard Checks

- Map each claim to routing correctness, evidence completeness, defect catch, validation freshness, over-routing, under-routing, token overhead, or turn overhead.
- Record token and turn fields as measured values or `not_collected`.
- Include selected/skipped reference counts and skipped-reference rationale.
- Add an over-routing guard for trivial or out-of-scope cases.
- Add an under-routing guard for hidden-risk cases.
- Mark structural-only evidence when no representative live agent run exists.

## Evidence Freshness

- Inspect current source, registry/routing, generated reports, validation output, graph, memory, and execution trajectory relevant to the case.
- Classify graph and memory evidence as accepted, rejected, stale, partial, or not verified.
- Confirm validation ran after the final material edit or mark it stale/not-run.
- Map each changed skill body, reference, registry rule, hook prompt, eval fixture, report, or runtime output to a validator or residual-risk owner.

## Privacy And Boundary

- Reject raw prompts, secrets, environment values, private archives, unbounded source corpora, and full command output.
- Retain only bounded structural facts, redacted fixture inputs, command status, and artifact paths.
- State what the benchmark proves and what it does not prove.
- Include rollback note, residual risk owner, and next gate.

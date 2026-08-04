# Architecture Enforcement Tooling Evidence Patterns

Use this reference when closure depends on rule-to-validation freshness, prior source or task evidence claims, tool permission boundaries, supply-chain review, or proof limits. Keep it as an evidence map, not a second tool catalog.

## Rule-Claim-To-Validation Map

| Enforcement claim | Minimum evidence | What it proves | What it does not prove |
| --- | --- | --- | --- |
| Rule maps to accepted architecture decision | Rule source, owner, affected graph edge, allowed and forbidden examples, and replacement path | The enforced rule is not arbitrary tooling | The architecture rule itself is optimal |
| Tool expresses the rule | Tool config, representative failing example, command, and rejected alternatives | The inspected command can catch the named violation | All future dynamic or generated paths are covered |
| Exceptions are narrow | Generated/runtime/framework path, source-of-truth, owner, scope, reason, expiry, and drift check | Obvious false positives are contained | Every exception remains safe after future codegen changes |
| Existing violations are governed | Violation count, block/report decision, suppression owner, cleanup issue, and ratchet threshold | Existing debt has an owner and path | Cleanup will finish on schedule |
| CI or report-only evidence is fresh | CI job or local command, report path, exit code, covered paths, final edit scope, and freshness | The final inspected state ran through the mapped gate | Release readiness or all affected tests are proven |
| Public export gate preserves consumers | Export diff, consumer search, known/unknown consumers, compatibility plan, and rollback | Obvious consumer breakage was considered | External usage outside search scope is impossible |
| Tool output is safe and reproducible | Action class, permission state, dependency/license/install review, artifact path, redaction rule, and reproducible command | Evidence collection avoids obvious supply-chain and output risks | Every future tool version or CI runner is safe |

## Current Evidence And Freshness

- Treat repository inspection, prior task evidence, prior drift incidents, generated reports, CI history, and old suppressions as selectors until current source, config, generated outputs, and command results confirm them.
- Accept prior "graph is acyclic", "rule is enforced", "suppression is safe", or "public export is unused" only when current graph, imports, exports, generated paths, CI config, and validation still match.
- Mark evidence stale after edits to imports, exports, package graph, generated sources, CI jobs, lockfiles, lint/type configs, suppressions, baselines, build cache inputs, or affected-test rules.
- Map every enforced rule, exception, suppression, baseline, failing example, CI command, tool dependency, public export, and residual unenforced rule to fresh evidence or explicit residual risk.

- If new dependency, plugin, action, binary, or image, record dependency review, lockfile impact, reproducible install, rollback, and owner.
- If CI gate mutation or release-blocking policy, record pipeline owner, rollout mode, unblock path, rollback, and communication path.

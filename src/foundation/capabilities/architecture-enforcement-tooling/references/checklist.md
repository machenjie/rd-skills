# Architecture Enforcement Tooling Checklist

- Name the accepted architecture, module, import, layer, export, generated-code, type, lint, complexity, affected-test, or cache rule being enforced.
- Confirm the rule source: ADR, module-boundary decision, owner review, existing CI policy, or accepted review finding.
- Inspect package/module graph, imports, exports, generated paths, scripts, CI jobs, tool configs, tests, and current violations.
- Choose the smallest existing command or tool that can express the rule; document rejected existing commands before adding a dependency.
- Define generated, reflection, framework, migration, CLI, test, or runtime-registration exceptions with owner, scope, reason, and expiry or review trigger.
- Include at least one representative failing example and the intended replacement path.
- Decide block-now, report-only baseline, suppress-with-owner, or cleanup route for existing violations.
- Hand changed build-graph, generated-authority, cache/action-identity, or affected-test decisions and proof to `build-tool-professional-usage`.
- Keep accepted-rule diagnostics, exceptions, baselines, and gate behavior within this capability.
- Record dependency, license, install-script, reproducible-install, and CI cost review when a new package, plugin, binary, action, or image is introduced.
- Attach command, report path, exit code or manual result, covered paths, uncovered paths, freshness after final edit, and evidence limits.
- Name pipeline owner, rule owner, cleanup owner, rollback or unblock path, residual unenforced rules, and recommended next step.

# Documentation Generation Benchmarks And Patterns

Use this reference only when the root `SKILL.md` needs deeper support for source/doc evidence mapping, generated documentation validation, graph/memory/execution coupling, command safety, no-docs proof, or stale-doc failure review. Keep examples small, use safe placeholders, and do not include secrets, private topology, real user data, or exploit detail beyond audience need.

## Documentation Evidence Matrix

| Surface | Inspect | Validation Evidence | Common False Proof |
| --- | --- | --- | --- |
| User or contributor guide | Source behavior, setup scripts, CLI help, tests, existing docs. | Command/example run, link check, reviewed source path, or not-verified marker. | Copying an old README section because the feature name still matches. |
| API/config/contract docs | OpenAPI/AsyncAPI/protobuf/schema, env/config definitions, generated clients, error tests. | Schema diff, generated spec, contract test, config validation output. | Handwritten example that looks plausible but is not generated or tested. |
| Migration/release docs | Migration files, feature flags, compatibility branches, changelog, release plan. | Forward/rollback validation, old/new compatibility check, release owner signoff. | Release note says "breaking change" without upgrade order or rollback path. |
| Operational/runbook docs | Alerts, dashboards, logs, SLOs, deployment manifests, support workflow. | Expected output, failure signal, escalation owner, drill or manual review. | Runbook action exists but lacks success/failure criteria. |
| ADR/compliance/handoff evidence | Decision records, approvals, exception records, validation logs, retention owner. | Evidence owner, freshness date, retention location, risk acceptance. | Agent summary claims validation without artifact, timestamp, or scope. |
| Generated docs | Generator config, source inputs, checked-in output, CI job, changed paths. | Regeneration diff, generator exit code, link/spec check after final edit. | Generator ran before final source change or with stale inputs. |

## Graph, Memory, And Execution Coupling

- Repository graph selects source files, schema/config owners, generated docs, examples, tests, build steps, release notes, runbooks, and likely stale siblings; inspect those current files before making factual claims.
- Project memory can identify prior doc drift, fragile setup commands, accepted wording, or release-debt decisions, but memory is only a selector until current source and validation confirm it.
- Execution trajectory decides whether docs validation ran after the final material source/doc edit and whether a generated artifact, link check, or command example is stale.
- Validation broker maps each documentation claim to a source path, generator, link checker, schema diff, test command, manual review, owner response, or explicit residual risk.
- Agent-tool permission/sandbox evidence is required before documenting or running commands that mutate files, data, infrastructure, credentials, release state, or operator-visible systems.

## Documentation Claim Validation Map

| Claim Type | Evidence Pattern | What It Proves | What It Does Not Prove |
| --- | --- | --- | --- |
| Command or setup step works | Run with project config in a bounded environment and record exit/output summary. | The command worked for the inspected environment and inputs. | Other OSes, missing optional services, or future dependency resolver behavior. |
| API example is current | Generate or validate against schema and integration/contract tests. | Example fields and error semantics match selected source/spec. | All consumers understand or have migrated to the contract. |
| Migration guide is safe | Forward/rollback or forward-fix evidence plus compatibility window. | The documented order is valid for tested representative state. | Production data skew, long-running consumers, or untested rollback timing. |
| Runbook action is executable | Expected output, failure signal, escalation, and reviewed command boundary. | On-call has a visible success/failure decision path. | The action will always remediate production incidents. |
| No docs are required | Changed-path scan, audience/artifact matrix, existing-doc search. | Inspected durable artifacts do not need an update for the named change. | Unsearched downstream docs, customer enablement material, or private support notes. |

## Failure Pattern Review

- Check whether a generated artifact changed only because of formatting while the source contract actually changed elsewhere.
- Check whether a changelog or release note hides migration, rollback, support, or operator impact behind a generic label.
- Check whether a command snippet assumes local credentials, HOME state, production network access, or an unbounded working directory.
- Check whether "validated" means a link checker ran, a schema was regenerated, a command executed, or only a human read the page.
- Check whether stale docs survive in sibling README, examples, SDK notes, troubleshooting, changelog, generated specs, or support runbooks.

## Anti-Patterns To Reject

- Treating fluent prose, agent memory, or previous handoff text as evidence of current behavior.
- Publishing public examples with token-shaped values, internal hostnames, private topology, or real user data.
- Marking docs "not required" without naming audiences, artifacts searched, and behavior surfaces ruled out.
- Accepting generated documentation without recording input sources, generator command, diff/result, and freshness after the final edit.
- Documenting rollback, cleanup, migration, or troubleshooting commands without preconditions, dry-run/revert path, expected output, and owner.

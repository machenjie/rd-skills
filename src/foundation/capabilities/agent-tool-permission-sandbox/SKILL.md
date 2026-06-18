---
name: agent-tool-permission-sandbox
description: Classifies agent tool, command, edit, permission, sandbox, destructive-action, secret-exposure, and external-side-effect risks before execution and handoff.
license: MIT
changeforge_kind: foundation-capability
changeforge_capability_id: "120"
changeforge_version: 0.1.0
---

# Agent Tool Permission Sandbox

## Mission
Classify the risk of agent tools, shell commands, file edits, MCP actions, permission prompts, and sandbox boundaries before execution. The capability makes destructive operations, external side effects, secret exposure, untrusted tools, and missing rollback evidence explicit while keeping hook/runtime behavior deterministic, bounded, and fail-open unless a maintainer enables stricter policy.

## When To Use
- Before running shell commands, permission requests, tool calls, apply patches, install/build scripts, deploy commands, migrations, or cleanup commands.
- When a command can delete, overwrite, move, publish, deploy, push, install, change permissions, access secrets, or affect external systems.
- When sandbox mode, approval policy, network access, or MCP tool trust is relevant to the action.
- When a hook or runtime should warn about risky command/edit patterns without storing raw commands or prompts.

## Do Not Use When
- The work is read-only and uses ordinary file reads or searches with no secret or external system exposure.
- The command is a deterministic local validation command with no writes beyond normal test/build caches.
- A higher-level release or security gate already produced an equivalent command permission and rollback record for the current action.

## Non-Negotiable Rules
- Classify the tool or command before execution by write scope, destructive potential, external side effect, secret exposure, network behavior, privilege, and rollback need.
- Do not store raw prompts, secrets, environment values, full command arguments, or full command output in state or telemetry.
- Use least-privilege execution and existing sandbox controls; do not bypass the approval policy.
- Destructive commands require target confirmation, rollback or restore path, dry-run or preview when available, and explicit residual risk.
- External side effects such as deploy, push, publish, send, migrate, rotate, or delete require owner and release/security gate evidence.
- Untrusted MCP tools or connectors require data access boundary, action scope, and allowed operation review.
- Hook runtime warnings must be deterministic and fail open unless stricter mode is explicitly configured by maintainers.

## Industry Benchmarks
- **Principle of least privilege**: Run tools with the narrowest permissions needed.
- **Change management approval**: Destructive and external actions require accountable approval and rollback evidence.
- **NIST SSDF**: Protect credentials, verify tools, and avoid exposing secrets in logs or automation.
- **SRE release safety**: Validate rollout and rollback commands before production changes.
- **Supply-chain security**: Treat new tooling and connector access as trusted computing base expansion.

## Selection Rules
- Select this capability for permission events, risky pre-tool warnings, release commands, destructive cleanup, migrations, install scripts, or external writes.
- Select it with `security-privacy-gate` when secrets, credentials, permissions, user data, prompt/tool output, or connector data are involved.
- Select it with `delivery-release-gate` when deploy, push, publish, migration, build artifact, or install behavior is involved.
- Select it with `reliability-observability-gate` when commands affect production reliability, telemetry, cost, capacity, or incident response.
- Select it with `agent-execution-discipline` when tool use must appear in final closure evidence.

## Risk Escalation Rules
- Escalate when a command includes delete, remove, overwrite, reset, clean, force, migrate, apply, deploy, push, publish, chmod, chown, sudo, secret, token, key, credential, or live endpoint signals.
- Escalate when sandboxing is disabled or insufficient for a command that writes outside the intended repository boundary.
- Escalate when command output or arguments may contain secrets or regulated data.
- Escalate when a tool can mutate external services, email, issue trackers, source control, package registries, cloud resources, databases, or production systems.
- Escalate when a third-party or MCP tool is requested without clear data access boundary and operation scope.

## Critical Details
- Shell command risk depends on both the executable and arguments; telemetry records only bounded facts such as program name and classification.
- File edits can be risky even without shell commands when they touch registries, hooks, release scripts, secrets, or generated/runtime artifacts.
- "Dry run available" is not the same as "dry run executed"; evidence must say which happened.
- Approval does not prove correctness. It only authorizes a class of action; validation and rollback still matter.
- Fail-open runtime warnings must still provide useful advisory context and never mutate project source.

## Failure Modes
- **Destructive command without target proof**: A cleanup command removes files outside intended scope.
- **Secret exposure**: Full command output or env values are stored in telemetry or final notes.
- **Approval bypass**: A tool runs an external write after the policy denied or did not request permission.
- **Untrusted connector overreach**: A broad connector action reads or writes data outside the user-intended boundary.
- **Rollback gap**: A migration or deploy command runs with no tested rollback path.

## Output Contract
Return a `tool_permission_sandbox_record` with:
- **Action summary**: tool or command program, not full arguments when they may contain secrets.
- **Risk class**: read-only, local-write, destructive-local, external-read, external-write, privileged, secret-sensitive, release-affecting, or production-affecting.
- **Sandbox and approval state**: sandbox mode, approval policy, permission result, and any missing permission evidence.
- **Target boundary**: intended files, directories, services, data classes, or external systems.
- **Side-effect inventory**: filesystem, network, database, source control, deploy, package, email, connector, or cloud effects.
- **Safety controls**: dry run, preview, backup, rollback, idempotency, rate limit, and owner confirmation.
- **Telemetry boundary**: bounded facts recorded and sensitive facts excluded.
- **Residual risk**: unverified rollback, untrusted tool, missing dry run, broad scope, or not-run disclosure.
- **Next gate**: security, release, reliability, test, or no-next-gate rationale.

## Quality Gate
1. Risk class is explicit before execution or handoff.
2. Sandbox and approval state are stated without bypassing policy.
3. Destructive or external-write actions have target confirmation and rollback.
4. Secret-sensitive commands do not expose raw secrets, env values, full arguments, or full output.
5. Untrusted tools have data access and action scope boundaries.
6. Telemetry contains only bounded facts.
7. Final handoff states any command that was not run, failed, or ran with residual risk.

## Used By
- `change-forge-router`
- `security-privacy-gate`
- `delivery-release-gate`
- `reliability-observability-gate`
- `quality-test-gate`
- `ai-code-review-refactor`
- `skill-authoring-expert`
- `agent-execution-discipline`

## Handoff
Hand off the permission and sandbox record with any risky command, tool call, edit, release, cleanup, migration, connector, or hook runtime change. If the action is unsafe or insufficiently bounded, hand off to the relevant security, release, or reliability gate before execution.

## Completion Criteria
The capability is complete when tool risk, sandbox and approval state, side effects, secret boundaries, rollback controls, telemetry limits, validation status, and residual risk are explicit enough for an independent reviewer to approve or block the action.

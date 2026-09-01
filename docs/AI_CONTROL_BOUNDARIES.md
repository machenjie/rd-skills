# AI Control Boundaries

This document defines the authority, permission, evidence, and context boundaries
between the hookless concept and the detailed execution model.

## Control Authority

The `main-control-agent` classifies, dispatches, schedules, reports progress,
routes repair or re-review, and closes. It does not inspect target code, define
source-backed acceptance or placement, edit, execute, or review. Analysis owns
read-only engineering preparation; task execution owns bounded writes and fresh
validation; review owns independent findings without repair authority.

A user request authorizes only the bounded internal work needed for that request.
Material scope or behavior choices, destructive or production operations,
permission elevation, irreversible data change, and otherwise unknowable
requirements remain user decisions. Detailed role capabilities and handoffs are
canonical in the [Subagent model](SUBAGENT_MODEL.md).

## Permission and Host Enforcement

Host tool configuration declares the tools and enforcement supplied to each
role. The source matrix is `src/agent-profiles/host-enforcement.json`; its closed statuses are
`native-enforced`, `sandbox-enforced`, `prompt-enforced`, and `unsupported`.
Build and install manifests bind that matrix and its digest, while doctor reports
the resulting configuration. A Task Agent invokes the delivered
`read`/`search`/`edit`/`execute` tool directly within its Semantic Role and Task
Contract scope. There is no runtime capability preflight or Host Executor
fallback inference. Only a tool-unavailable, permission-denied, sandbox-denied,
or required-artifact-unavailable result from the actual operation blocks. The
visible blocker is `EXECUTION_BLOCKED task=<Task ID>;
operation=<read|edit|execute>; observed=<actual host/tool failure>`. Retry keeps
the same real Task ID and the complete unchanged Task Contract. Before the Host
call, a pure scope preflight normalizes explicit targets against the workspace
and Allowed Read/Write Scope, rejects traversal or symlink escape, and invokes
no Host tool when blocked. Execute checks only explicit write targets; unknown
side effects remain enforced by the Host sandbox. The actual Host/tool
invocation event and raw output are the sole failure proof. A static mapping or
canonical blocker formatter validates syntax only and cannot prove a failure.

Copilot CLI, Copilot VS Code, and Copilot Coding Agent remain independent
declared Host Surfaces under one compatible delivery family. Their static
delivery metadata does not become a probabilistic runtime state machine.

When a host cannot express a fine-grained restriction, the generated Profile
states the limit as prompt-enforced. rd-skills does not add an executable
interceptor or second sandbox. Current supported hosts declare isolated
workspaces unsupported, so read-only work may be parallel but writes are serial.
No-edit utilities are prompt-enforced and fail if their before/after workspace
change sets differ or are unavailable.

## Evidence Boundary

Task evidence is visible in scoped Markdown contracts and handoffs. Validation
must follow the latest material edit, and implementation review uses the actual
diff and every changed file. Older-scope evidence cannot authorize closure.
For supplied-artifact hosts, actual evidence is delivered unified-diff content,
not a digest, summary, filename, command output, or opaque identifier. For a
native host, the reference counts only after the Host actually dereferences it
and binds the exact read content to the assigned reviewer, current generation,
and exact paths. A `readable` self-report or nonexistent reference cannot
satisfy the static readiness helper. Main verifies the bound content is
actually readable for this handoff, and Review never exports its own evidence.
rd-skills does not persist private runtime ledgers, prompt transcripts, or an
internal task-state database. The exact artifact and completion flow is owned by
the [Operating model](OPERATING_MODEL.md).

## Skill and Context Boundary

Each task receives one primary Professional Skill, only concretely triggered
Layer 3 guidance, and its review route. The Runtime never exposes Foundation or
Domain items as Host top-level Skills. It opens each capsule-named compiled item
directly behind the Professional selector and only the necessary Targeted
References. Agent Profiles do not preload catalogs, scan Layer 3 directories,
rerun global routing, or gain target-repository authority merely because a
host-native Skill loader is available.

Use the [Operating model](OPERATING_MODEL.md) for runtime artifact, state, and
evidence flow. Use the [Subagent model](SUBAGENT_MODEL.md) for the four Profiles,
context isolation, parallelism, completion, and review separation.

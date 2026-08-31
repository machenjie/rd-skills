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

Host tool configuration declares a static capability ceiling. The source matrix is
`src/agent-profiles/host-enforcement.json`; its closed statuses are
`native-enforced`, `sandbox-enforced`, `prompt-enforced`, and `unsupported`.
Build and install manifests bind that matrix and its digest, while doctor reports
the resulting configuration. Configuration and `rendered_tools` are not
invocation truth. Dispatch uses only invocation-scoped effective runtime facts;
missing, stale, unrecognized, or `unknown` facts are unavailable.
For each executor, current invocation facts outrank verifiable current Host
Surface session evidence; a same-session mismatch is negative evidence that
excludes that executor or executor class from fallback. Otherwise capability is
unknown. No observation is written back to the static matrix.

Semantic Role remains one of the four Profiles even when the Host Executor
changes. A proven replacement executor receives the complete original Task
Contract unchanged; without one, Main blocks rather than implementing. A worker
with a capability mismatch returns the canonical zero-edit
`CAPABILITY_MISMATCH` only and never reroutes. Copilot CLI, Copilot VS Code, and
Copilot Coding Agent are independent declared Host Surfaces under the compatible
Copilot delivery family; none of those declarations proves a live invocation.
The static `workspace-mutation` ceiling additionally requires supported delivery,
a task-agent write-semantic tool, and non-unsupported task-agent enforcement
surfaces. It is still only a ceiling, never edit authorization.

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
native host, the assigned reviewer must be able to read the delivered current
reference bound to the assigned reviewer, current generation, exact paths, and
readable delivered instance. Host support is only a capability ceiling; Main proves accessibility
for this handoff, and Review never exports its own evidence.
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

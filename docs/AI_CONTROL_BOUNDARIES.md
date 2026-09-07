# AI Control Boundaries

This document defines the authority, permission, evidence, and context boundaries
between the hookless concept and the detailed execution model.

## Control Authority

The `main-control-agent` selects expertise, dispatches, coordinates results,
and closes. It does not inspect target code, define source-backed acceptance or
placement, edit, execute, or review. Task execution owns local discovery, bounded
writes, and fresh validation. Analysis resolves concrete questions when needed;
independent Review owns findings without repair authority when selected.

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
the resulting configuration. A Task Agent invokes delivered read/search/edit/execute tools directly.
Ordinary repository discovery may expand to locate owners, callers and tests;
explicit write targets must remain inside authorized scope after path and symlink
normalization. Destructive, production, privilege, sensitive external-data and
irreversible effects remain subject to authorization and Host enforcement.
Unknown command effects remain Host-enforced; no second sandbox is introduced.

Only an actual tool, permission, sandbox or required-artifact failure proves an
execution blocker. Report the operation and observed output against the same real
task identity. Prior authorization remains effective across retries; after two
same-path failures another attempt needs a changed hypothesis, material or gap.

## Evidence Boundary

Current source, actual tool output and post-final-edit validation support
completion. Summaries, precise paths and hashes do not substitute for inspected
content or prove complete coverage. When independent Review is selected, provide
the actual current diff or artifact, source, validation and proof limits. Formal
handoffs are optional unless a real consumer or boundary requires them.

Build and package fingerprints protect source-to-dist freshness and real
cross-boundary provenance. Ordinary tasks need no signature, readiness record,
private evidence ledger or internal task-state database. The [Operating
model](OPERATING_MODEL.md) describes the evidence and completion behavior.

## Skill and Context Boundary

Each task receives one primary Professional Skill, only concretely triggered
Layer 3 guidance. Independent Review receives its own expertise only when selected. The Runtime never exposes Foundation or
Domain items as Host top-level Skills. It opens each capsule-named compiled item
directly behind the Professional selector and only the necessary Targeted
References. Agent Profiles do not preload catalogs, scan Layer 3 directories,
rerun global routing, or gain target-repository authority merely because a
host-native Skill loader is available.

Use the [Operating model](OPERATING_MODEL.md) for runtime delivery, coordination,
and evidence. Use the [Subagent model](SUBAGENT_MODEL.md) for the four Profiles,
context isolation, parallelism, completion, and review separation.

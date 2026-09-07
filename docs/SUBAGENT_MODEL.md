# Subagent and Review Model

## Profiles

| Profile | Responsibility | Tools |
| --- | --- | --- |
| main-control-agent | Select expertise, dispatch, coordinate results | Dispatch only |
| analysis-agent | Resolve evidence-backed questions, diagnosis, or requested design | Read, search, and conditional external-source-read |
| task-agent | Inspect, implement, self-check, and validate bounded work | Read, search, edit, execute |
| review-agent | Independent non-modifying assessment when selected | Read, search, and execute-read-only |

The four Profile boundaries are defined in
`src/agent-profiles/role-agents.json`. A task-agent can inspect unknown local
owners and tests before editing. This does not require another agent or a
capability self-proof. Actual Host failures and permission boundaries remain
visible; a declaration of capability does not grant authority.

Analysis uses external-source-read only after local evidence leaves a material
question unresolved, with minimal public information and within Host boundaries.
Review may execute read-only checks within those boundaries; it cannot edit,
repair, or perform independent external-source-read.

## Context and Coordination

Main selects one Primary Professional and zero to three authorized Layer 3
Skills for an assignment. Workers receive the goal, necessary constraints,
write scope, validation expectations, and selected expertise. Read locations
are starting points for discovery. Ordinary single-agent work needs no complete
Brief, Task Contract, handoff form, or readiness record.

Use deeper Analysis for an explicit request or a concrete unresolved decision
that can change implementation. Use a short Engineering Brief only when stable
cross-agent decisions are necessary. Decompose around real dependencies and
owners. Keep shared-workspace writes serial; parallel writes require actual
Host isolation and no shared write surface or dependency. Supported Hosts do
not currently declare isolated write workspaces.

## Independent Review

Independent Review is optional for ordinary implementation. A user request,
source-backed semantic uncertainty, or important failure mechanism poorly
covered by local tests can justify it. File count, task boundaries, and edit
count do not. Main selects a separate Professional and Layer 3 assignment for
the needed Review. The reviewer consumes that assignment without rerouting or
copying the implementation's Layer 3 selection.

When selected, the reviewer inspects the current artifact or diff, affected
source, and relevant consumers. It returns concrete defects with evidence,
reachable failure mechanisms, and required actions, plus proof limits. It does
not modify source or grant production authority.

Repair findings within the established direction and run fresh validation.
Changed design assumptions can require deeper reasoning; an ordinary defect
does not. Repeated judgment needs new evidence. There is no mandatory cycle of
review, repair, and re-review.

## Completion and Proof Limits

Complete the requested behavior with truthful evidence after the final material
edit. Local self-check and targeted validation may be sufficient. State which
checks ran and any unresolved limitations. Bounded observations return facts
and actual tool failures without creating hidden state or broadening authority.

Static source checks, deterministic fixtures, builds, and simulated installation
do not prove real-host startup, wall-clock performance, production accuracy,
provider behavior, or installed user experience.

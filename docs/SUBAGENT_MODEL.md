# Subagent and Review Model

## Profiles

| Profile | Responsibility | Tools |
| --- | --- | --- |
| main-control-agent | Select expertise, dispatch, coordinate results | Dispatch only |
| analysis-agent | Resolve evidence-backed questions, diagnosis, or requested design | Read, search, and conditional external-source-read |
| task-agent | Inspect, implement, self-check, and validate bounded work | Read, search, edit, execute |
| review-agent | Independent non-modifying assessment when selected | Read, search, and execute-read-only |

The four Profile boundaries are defined in
`src/agent-profiles/role-agents.json`. Task owns ordinary discovery:
candidate owner → current-source read → bounded competing-owner scan when
signaled → minimum affected consumers → confirmed owner(s) → edit. A user path,
first search hit, test, doc, caller or generated output provides a locator or
evidence; it cannot establish ownership alone. Confirm authority from current
behavior and invariants, writes, registration/DI/factory bindings, public/shared
contracts, generator inputs and dependency direction. Inspect alternative
definitions, siblings, bindings, writers or source/generated boundaries only
when evidence points there. Multiple necessary enforcement points can be owners.

Task closes relevant callers/consumers, affected tests and changed
contract/config/generated surfaces within the task's impact. This reuses the
discovery and impact principles of `repository-context-map` and
`repository-impact-inspection` without requiring either full Skill on ordinary
tasks, a checklist, or a recorded owner-decision artifact. Bounded read/search
handles normal file/owner/test/caller location; only unresolved competing owners,
contradicted invariants or other uncertainty that can change implementation
justify deeper Analysis. An ordinary resolved task stays **Task → validation →
done**, without fixed Analysis or Review. Actual Host failures and permission boundaries remain
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

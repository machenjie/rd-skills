# Utility Capsule

Use this contract only for `validation-only/no-edit` or `diff-export/no-edit`.
The task-agent loads no Professional Skill or Layer 3 guidance, does not use the
Implementation Handoff, and must not edit, repair, access the network, fetch, or
contact remotes. Runtime capability facts are not an execution preflight. Invoke
the capsule-named local operation directly. Only an actual Host/tool failure
blocks the utility, and the blocker preserves the current real Task ID. The
Host/tool invocation event and raw output are the failure proof; static mapping
or blocker formatting establishes syntax only.
Capture a pre-operation workspace change set with one adjacent ordered check group, exactly
one allowed operation, then the identical adjacent check group. Preserve user changes. A
`changed` or `unavailable` check invalidates the Utility
Return and forbids review or closure. Never auto-clean pre-existing user changes; route
only proven utility-created writes through a normal repair task. The assignment and return
contain exactly the ordered sections below.

# Utility Assignment

## Status

`in_progress`

## Task ID

## Owner

Exactly `task-agent`.

## Mode

Exactly `validation-only/no-edit` or `diff-export/no-edit`.

## No-edit Enforcement

Record the semantic no-edit boundary and the Host sandbox or tool enforcement
that applies. This is not a runtime capability state.

## Goal

## Allowed Scope

Name the repository or workspace root and every allowed path or target.

## Inputs

For diff export, name the local base, head, ref, or artifact path. For validation,
name the validation targets.

## Workspace Baseline

Record the pre-operation tracked, staged, and untracked workspace change set and rerun
the identical read-only check afterward. Fingerprint untracked content when
it exists or mark the check unavailable. A dirty baseline is allowed and must remain unchanged.

## Commands Allowed

Allow only capsule-named local/offline non-mutating pre/post checks through the
workspace state observation operation. `diff-export/no-edit` additionally runs
one exact change evidence export operation. Invoke the current Host tool
directly; do not infer permission from a capability name. Return output as supplied content or a host-native
artifact, never a new workspace file; do not validate or review.
For validation, additionally allow only capsule-named
non-modifying checks; do not repair or review.
An actual tool/permission/sandbox/required-artifact failure returns
`EXECUTION_BLOCKED task=<Task ID>; operation=<read|edit|execute>; observed=<actual host/tool failure>`;
the Host/tool invocation event and raw output are the sole proof, and
`task=unspecified` is forbidden.

## Expected Evidence

## Stop Conditions

# Utility Return

## Status

Exactly `blocked`, `partial`, or `completed`.

## Task ID

## Owner

## Mode

## No-edit Enforcement

## Artifact or Check Outcomes

## Commands Run

## Workspace Diff Check

Exactly `unchanged`, `changed`, or `unavailable`, with the pre/post change-set evidence.
Only `unchanged` is a valid Utility result.

## Evidence Ledger

| Claim | Owner | Artifact | Command | Result | Freshness | Scope | Proof Limit | State |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |

Allowed `State` values are `current`, `superseded`, and `invalid`. A changed
or unavailable workspace check invalidates the utility claim.

## Unverified Scope

## Residual Risk

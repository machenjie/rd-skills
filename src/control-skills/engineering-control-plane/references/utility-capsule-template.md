# Utility Capsule

Use this contract only for `validation-only/no-edit` or `diff-export/no-edit`.
The task-agent loads no Professional Skill or Layer 3 guidance, does not use the
Implementation Handoff, and must not edit, repair, access the network, fetch, or
contact remotes. Injected capability facts, not a host/tool/command name,
decide whether the operation is supported. An unsupported required capability
blocks the utility before operation.
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

Record the injected no-edit enforcement capability state. This is a behavioral
contract, not a runtime write block.

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
workspace state observation capability. `diff-export/no-edit` additionally
requires an exact change evidence export capability. The host adapter may name
its native tool or command, but generic control logic must not depend on that
identifier or spelling. Return output as supplied content or a host-native
artifact, never a new workspace file; do not validate or review.
For validation, additionally allow only capsule-named
non-modifying checks; do not repair or review.

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

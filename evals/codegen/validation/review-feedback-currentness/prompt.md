# Benchmark Prompt

## Task

Implement the deterministic review-evidence adapters in `subject.py`. Produce local decision and permission records only. Do not access Git hosting or perform edits, replies, thread resolution, or review requests.

## Context

A fictional quantity validator accepts integers exactly when `units >= minimum`. Feedback records declare their kind and proposed minimum. Source snapshots and probes supply evidence. This harness validates structured feedback; it does not infer intent from natural-language comments.

## Requirements

- `triage(head, sources, findings, proofs, decisions)` returns records keyed by finding ID. Retain the origin commit. Bind decisions to `head` and an exact current path, line, and anchor.
- Accept proof only when its commit and complete source match the current snapshot. Require unique Boolean observations at minimum minus one, minimum, and minimum plus one. Compare observed behavior with the supplied acceptance predicate.
- An old comment commit remains usable after current revalidation. A missing file is obsolete. A changed anchor needs an explicit current relocation. Current observations satisfying the rule mean resolved; no edit follows automatically.
- Detect duplicate verified claims for one subject and minimum. Different minimums for the same exact acceptance predicate conflict, even when current code satisfies one claim. Do not apply either conflicting proposal.
- Keep defect, suggestion, preference, question, and out-of-scope distinct. Questions need answers. Preferences need a project decision. Neither establishes a defect by itself.
- Accept or propose an alternative only with a concrete reason, one current line edit, a boundary validation plan, and remaining risk. Reject decisions need a concrete reason. Missing proof, decisions, or plans remain explicit pending states.
- `action_permissions(role, grants, disposition)` returns separate records for judge, edit, reply, resolve, and request-rereview. Each needs its own grant. Analysis and Review remain read-only. An edit also needs an accepted or alternative plan.
- External permission records indicate authority only, not readiness or completion. A fix, valid finding, or resolved defect grants no external action. Retain positive cases for each individually granted Task action.
- Keep inputs unchanged. Reject duplicate IDs and unknown kinds, roles, or grants.

## Constraints

Use standard-library Python and fixed in-memory evidence. Treat supplied commits and source snapshots as fixture identity, not cryptographically authenticated Git history. Probe provenance, arbitrary code semantics, reviewer identity, and provider authorization require separate evidence.

## Deliverables

Implement both callable interfaces. Return concrete reasons, bounded plans, and proof limits. Add no runtime workflow engine or external communication.

## Completion Evidence

Run passing assertions and reject the incomplete starter plus the stale-comment rejection control. Cover current, reverified old, obsolete, fixed, duplicate, conflicting, and unauthorized-effect records.

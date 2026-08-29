# Professional Skill Authoring Standard

This standard extends the [base standard](SKILL_AUTHORING_BASE_STANDARD.md).

## Role

A Professional Skill owns complete professional judgment for one task type. It tells an analysis, task, or review agent what to inspect, how to choose the correct owner and minimal design, which failure modes matter, when to stop, how to validate, and what to return.

It is not a human training article, a catalog router, a phase workflow, or a container for all adjacent Foundation knowledge.

Each Professional registry entry declares sorted, closed-set
`required_expertise_tags` for its complete decision surface. A formal
Professional Completeness review needs two domain reviewers covering every
declared tag for this Skill and one separate Skill/Reference architecture
reviewer. Those three reviewers are selected per Skill from the round-wide
reviewer pool; one fixed domain pair need not cover the entire catalog.

Formal Professional Completeness evidence uses schema 3. Fresh Skills receive
target-scoped immutable discovery capsules, explicit candidate requests, final
review capsules, and the 2+1 votes above. Discovery exposes the complete ranking
and lightweight candidate boundaries; requested additions receive complete
source only in the final capsule, and ballots bind only that final artifact. A
Skill may carry only when its
complete review-visible binding and dependency materials are exact and the
decision points directly to a depth-zero fresh origin; schema 1/2 evidence is
audit-only. The current contract, machine-derived plan, bindings, provenance,
unique unforked chain head, storage closure, and recomputed review-cost evidence
must all be current. An all-carry round has zero fresh reviewers, ballots,
capsule-chain artifacts, and canonical input bytes.
The current contract stores one package-material binding and one review-unit
binding per target, deduplicates dependency materials in one compact catalog,
and stores only dependency IDs per finding. Legacy source/package/review-binding
aliases and earlier schema-3 contract fingerprints are audit-only; a contract
change requires a full-fresh 189-Skill review.

## Required Design

- Demonstrate a stable independent Primary Route and distinct task ownership;
  otherwise extend an existing owner.
- Name one primary consuming Profile or a tightly bounded set of roles.
- Define positive and negative routing conditions.
- Require source-backed facts rather than guessed ownership or behavior.
- State owner, invariant, placement, failure, side-effect, and validation rules relevant to the work type.
- Include gotchas that change implementation or review decisions.
- Stop when scope, authority, risk, or validation leaves the Skill's boundary.
- Return changed/inspected scope, commands, results, findings, proof limits, residual risk, and next step as applicable.

## Root Budget

The governed body targets 550 words and 850 tokens. It hard-fails above 650
words or 1000 tokens. The exact Registry-generated Targeted References
projection is metadata and is excluded from these counts.

An over-target root is `REVIEW_DENSITY`, or `TIGHTEN_BODY` above 90% of its
triggered hard limit. A hard overage is `BLOCK`. The Readability Panel covers
each current Review or Tighten classification. Formal release requires zero
`tracked-tightening` decisions.

Do not use physical length alone as authored-content evidence. The audit keeps
physical `line_count`, governed `governed_line_count`, and canonical Registry
`projection_overhead_lines` separate, then publishes the independent
`review_state` and all ordered `review_reasons`.

## Layer 3 Loading

Name only plausible candidates in the registry. Load a candidate only when the
current task triggers its decision problem. A Direct Task normally uses zero to
three Layer 3 Skills. Higher-risk work may use more only when each addition maps
to a concrete risk. Foundation and modifier-only Domain items remain behind the
Professional selector and never become Runtime top-level Skills. Task and
Review consume Main's fixed Primary Route instead of rerunning global routing.

## Role Separation

Analysis Skills produce source-backed acceptance, owner, impact, placement, validation, rollback, and the First Executable Slice. Implementation Skills change one bounded scope and validate it. Implementation Review Skills inspect the actual diff and all changed files; pre-implementation Review Skills inspect the bounded artifact, criteria, and supporting evidence. Neither repairs findings. A single root may support more than one role only when its decision contract is genuinely shared and the registry states that support.

## References

Move deep technology matrices, failure catalogs, framework/library/protocol
details, and specialized checklists to targeted references. Keep the root
compact enough to load on every routed task. Prefer an existing Targeted
Reference, Foundation/Domain owner, or Professional owner before creating a new
Professional Skill. Do not repeat the control prompt, full task contract, or
complete Layer 3 bodies.

## Review Questions

Before accepting a Professional Skill, verify that an agent can answer:

1. What should I inspect first?
2. Who owns the behavior and invariant?
3. What is the smallest correct implementation or review boundary?
4. What subtle failure is most likely?
5. What fact requires escalation?
6. What evidence proves the result?

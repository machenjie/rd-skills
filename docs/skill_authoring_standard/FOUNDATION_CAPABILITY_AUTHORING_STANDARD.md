# Foundation Skill Authoring Standard

This standard extends the [base standard](SKILL_AUTHORING_BASE_STANDARD.md).

## Purpose

A Foundation Skill solves one reusable, high-value engineering decision such as transaction boundaries, concurrency control, error handling, test isolation, placement, security coding, or observability. It is a compact decision aid, not a language tutorial or broad handbook.

## Scope

- One decision problem per Skill.
- Concrete trigger and anti-trigger signals.
- Inputs that can be obtained from the current source/task.
- Rules that distinguish safe choices from common failure modes.
- Stop conditions for missing ownership, unknown invariants, unacceptable risk, or insufficient proof.
- A concise output that the primary Professional Skill can consume.

Split a Foundation Skill when independent parts have different triggers, consumers, or escalation boundaries. Do not split merely to reduce line count if the decision remains indivisible.

## Content Class and Budget

Foundation registry schema version 6 requires an explicit authoring class on
every item:

- `compact` is the default for one bounded decision card. It targets 400 words
  and hard-fails above 500. It must not carry `content_class_rationale`.
- `complex` is reserved for an indivisible set of concrete coupled decisions.
  It targets 500 words and hard-fails above 600. It must carry a concrete
  `content_class_rationale` naming the coupled decisions and why governing them
  separately would lose a shared invariant, failure chain, state transition,
  or evidence contract.

Every entry also declares sorted, closed-set `required_expertise_tags` and must
include the tag derived from its Foundation group. These tags are used only to
match qualified Professional Completeness reviewers; builds do not project them
into installed Skill content.

Every class also hard-fails above 900 tokens. An over-target root is
`REVIEW_DENSITY`, or `TIGHTEN_BODY` above 90% of its word hard limit. A hard
overage is `BLOCK`. Classify the authored boundary independently from its
`content_class`; do not promote repetition to `complex` to avoid trimming it. Content
class and rationale remain in the authoring registry and are not compiled into
runtime Skill bodies or build manifests.

## Root Contract

Use this ordered core in every Foundation root:

1. `Registry Trigger` — one `Use when` and one `Do not use when` block that
   includes the registry signals.
2. `Skill Role` — the supported Profiles and the narrow Layer 3 ownership
   boundary.
3. `High-Value Rules` — three to eight rules that materially change a decision.
   Move low-frequency depth to an existing targeted Reference.
4. `Anti-Patterns` — concrete, easy-to-miss failure patterns.
5. `Targeted References` — only registry-indexed links; a Skill with no indexed
   reference states that the root is the complete decision contract.

The optional ordered sections are `Inputs`, `Execution Checklist`, `Stop
Conditions`, `Output Contract`, and `Standards`. Keep an optional section only
when its contents are capability-specific and decision-bearing. Do not restore
generic task-contract inputs, a four-step inspect/apply/return checklist,
generic evidence/next-owner output, return-to-primary language, or prose that
merely tells the agent to read a reference. Do not author bare links or generic
loading prose. The Registry owns each Reference load and skip condition, and
the source section must be its exact generated projection. That projection is
readability-checked metadata and does not consume the Foundation root content
budget. Noncanonical links or prose remain ordinary governed content.

After any bulk tightening, scan all roots for empty headings and the exact
removed scaffold patterns, then review representative Skills from every
capability group to ensure that named decisions, failure modes, and proof
outcomes survived.

## Consumption

Every Foundation registry entry declares exactly one `delivery_scope`:

- `product` solves a normal engineering decision, has at least one task-routable
  Professional owner, and may be compiled into normal profiles;
- `authoring-only` is a durable ChangeForge authoring capability but is exposed
  only as a top-level Skill in `dev`;
- `dev-only` supports internal authoring, evaluation, or control-plane
  maintenance and is exposed only as a top-level Skill in `dev`.

Normal profiles compile only `product` Foundation Skills selected by a
Professional task route. The development profile exposes all Foundation Skills
at the top level. For every `product` entry, `used_by` must exactly equal the
Professional Skills that name it in `layer3_candidates`; their supported Agent
Profiles must intersect. `authoring-only` and `dev-only` entries have no
Professional owner and must not enter a normal task candidate list.

Never ask an agent to load all Foundation Skills. Never hide a task's primary ownership inside a Foundation Skill.

## Examples of Strong Content

- transaction scope aligned with the business invariant and side effects;
- idempotency key ownership and replay semantics;
- lock granularity, ordering, and retry behavior;
- test seam and isolation decisions;
- error translation at a stable boundary;
- log fields, redaction, correlation, and cardinality limits.

Each example is useful only when its trigger is present.

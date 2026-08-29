# Domain Skill Authoring Standard

This standard extends the [base standard](SKILL_AUTHORING_BASE_STANDARD.md).

## Purpose

A Domain Skill supplies high-density invariants and failure judgments for a business or technology domain such as payments, trading, wallets, distributed data, embedded systems, mobile systems, or Web3. It does not replace the task's primary Professional Skill.

Every Domain entry is `modifier-only`. It cannot own a Primary Route or appear
as a Runtime top-level Skill.

Each Domain registry entry declares sorted, closed-set
`required_expertise_tags`, including `domain-<skill-name>`. These authoring-only
tags bind content-reviewer coverage and are not projected into built Skills.

## Required Content

- Domain signals precise enough to avoid accidental routing.
- Anti-signals that keep ordinary changes out of the domain path.
- Required facts such as authority, asset/state ownership, consistency model, trust boundary, external protocol, or rollback limit.
- Domain invariants and state transitions.
- High-cost failure modes and abuse cases.
- Validation and reconciliation requirements.
- Stop conditions for missing authority, irreversible action, production risk, financial/security exposure, or unavailable domain facts.

## Root Budget

The governed body targets 500 words and 800 tokens. It hard-fails above 600
words or 900 tokens. The exact Registry-generated Targeted References
projection is metadata and is excluded from these counts.

An over-target root is `REVIEW_DENSITY`, or `TIGHTEN_BODY` above 90% of its
triggered hard limit. A hard overage is `BLOCK`. Keep Domain checklists at 12 to
15 decision items, with one primary risk decision per item.

## Loading

Domain Skills are loaded only when a concrete domain signal affects the current
decision. They are compiled behind the selected Professional owner and are
never exposed at the Runtime top level. Domain routing must not trigger merely
because a word appears in unrelated prose. Task and Review consume the Primary
Route fixed by Main; they do not bypass the Professional route or globally
reroute from a Domain signal.

## Review

Validate the Domain registry, anti-trigger precision, Professional owner links, routing fixtures, Skill body links, and relevant behavior benchmarks. When a domain rule changes, ensure acceptance and validation cover positive, negative, replay/retry, partial-failure, and rollback or reconciliation behavior as applicable.

Every registered Domain Skill needs a passing positive route and a neighboring
negative route. Its release policy must also require captured behavior evidence.
The paired prompts should share domain terms and differ at the decision boundary.

Write Registry triggers and decision boundaries as atomic signals. Assign every
signal to one oracle route family. Keep the same atoms visible in the
authoritative Router row.

Add one transition-positive fixture per Domain. Add one unchanged-paraphrase
negative control. Coverage uses passing actual routes and exclusions only.

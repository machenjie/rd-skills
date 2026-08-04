# ChangeForge Skill Authoring Base Standard

## Purpose

ChangeForge Skills are concise execution contracts for AI agents. They must improve a concrete engineering decision without requiring private product protocols, complete catalog loading, or source-repository knowledge at task runtime.

## Quick Use

1. Select the Skill layer and ownership boundary in [Required
   Sections](#required-sections) and [Boundaries](#boundaries).
2. Write the discovery contract using [Frontmatter](#frontmatter), then keep the
   root within the [AI Readability Contract](#ai-readability-contract) and
   [Decision Density](#decision-density).
3. Put conditional depth behind the registry-owned [References](#references)
   contract; never hand-edit generated projections.
4. Confirm task/evidence semantics in [Task, Evidence, and Completion
   Contracts](#task-evidence-and-completion-contracts), then run
   [Validation](#validation).

## Frontmatter

Use YAML frontmatter with only:

```yaml
---
name: skill-name
description: Use when ...; do not use when ...
---
```

Names are stable lowercase kebab-case identifiers. Descriptions carry enough positive and negative routing signal for selection.
Control and Professional descriptions target 220 characters and fail above 300;
Foundation and Domain descriptions target 180 characters and fail above 260.
Keep only the trigger, anti-trigger, and consuming profile or owner-Skill
boundary in discovery metadata. Put workflow and evidence detail in the body.

## AI Readability Contract

Apply one readability contract to every AI-facing sentence:

- ordinary sentence target: at most 24 words;
- complex professional sentence target: at most 32 words;
- hard gate: at most 40 words;
- one list item carries one primary decision.

The 24-word and 32-word bands are review signals. More than 40 words fails
validation. Split a list item when it contains independent `must`, `never`,
`stop`, `route`, or execution obligations. Wrapped Markdown lines form one
logical sentence and cannot bypass the gate.

Fenced code, standalone commands, schema fields, table cells, and pure term
enumerations are exempt. Inline code counts as one atom. A Markdown link counts
its visible label. The gate covers the Main Control Prompt, Agent Profile
instructions, descriptions, Skill roots, References, and compiled Layer 3
projections.

## Required Sections

Every Professional and Domain root contains:

- `Role`
- `When To Use`
- `Do Not Use`
- `Required Inputs`
- `Professional Decision Rules`
- `High-Value Gotchas`
- `Execution Checklist`
- `Stop / Escalation Conditions`
- `Output Contract`
- `Targeted References`

Every Foundation root contains this ordered core:

- `Registry Trigger`
- `Skill Role`
- `High-Value Rules`
- `Anti-Patterns`
- `Targeted References`

Foundation roots may add `Inputs`, `Execution Checklist`, `Stop Conditions`,
`Output Contract`, or `Standards` in the validated order only when the section
contains decision-bearing capability content. Generic task inputs,
inspect/apply/return steps, evidence handoff, and return-to-owner prose are
forbidden scaffolding, not authoring completeness.

The section names are a machine-validated contract. Keep each section action-oriented and avoid duplicating the same workflow language across Skills.

## Registry Contract

Every Skill registry entry declares:

```text
name
path
required_expertise_tags (required for every non-Control Skill)
role_support
trigger_signals
anti_trigger_signals
required_inputs
required_inputs_by_role (required for multi-role Professional Skills)
output_contract
output_contract_by_role (required for multi-role Professional Skills)
escalation_signals
reference_index
```

`required_expertise_tags` uses the closed taxonomy in
`scripts/validation_utils.py`. Foundation entries include their group tag;
Domain entries include their Skill-specific domain tag. The field exists only
to bind reviewer qualification coverage and is not projected into built Skill
content.

`reference_index` is a list of mappings, never legacy path strings:

```yaml
reference_index:
  - path: references/checklist.md
    type: targeted
    load_when: cache invalidation or freshness changes need failure coverage
    do_not_load_when: no cache behavior or ownership changes
    required_by: [analysis-agent, task-agent]
    required_output: [decision-record, evidence-gap]
```

Each mapping contains exactly `path`, `type`, `load_when`, `do_not_load_when`,
`required_by`, and `required_output`. Conditions stay short and name the
Reference subject. Roles and outputs must use the control-model vocabulary.
Generic phrases such as `when needed` are invalid.

For a multi-role Professional Skill, keep only role-neutral inputs in
`required_inputs` and map every supported profile exactly once in
`required_inputs_by_role`. The root `Required Inputs` section must use matching
mode labels and must not require an artifact that the role cannot possess.
The shared `output_contract` is the true union across supported modes. Map every
supported profile exactly once in `output_contract_by_role`, and use matching
role-labelled blocks in the root `Output Contract`; swapped role outputs fail
validation.
Professional entries may name Foundation or Domain candidates. Candidate naming makes guidance available; the current task signal decides whether it is loaded.

## Decision Density

Retain content that does at least one of the following:

- improves implementation or review accuracy;
- prevents expensive rework or a material failure;
- finds defects automatic tests are likely to miss;
- shortens the critical path;
- unblocks a downstream task;
- supplies an independent professional perspective.

Delete or relocate general background, tutorials, generic software advice, repeated process prose, and theory that cannot change the current task.

## References

Use a targeted reference for deep, conditional material. The Registry is the
single authority for the six-field Reference Contract v2. Each source
`Targeted References` section with one or more contracts is exactly this
six-column compact table, with one Registry-ordered row per contract:

```markdown
| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [checklist](references/checklist.md) | decision-checklist | task-specific load condition | task-specific anti-condition | task-agent, review-agent | checklist-result, residual-risk |
```

Column order, header and separator bytes, cell spacing, labels, row order, and
comma-space list joins are canonical. A literal pipe is written as `\|`; no
other backslash escape is accepted. An empty index keeps the exact
`- No task-local Reference is indexed for this Skill.` sentinel instead of an
empty table. The former five-line record, bare links, manual loading prose, and
generic conditions such as `when needed` are forbidden.
Every path matches `references/(<slug>/)*<slug>.md`; each slug uses lowercase
letters, digits, and single hyphen-separated words only. Whitespace, brackets,
parentheses, backslashes, pipes, dot segments, and non-Markdown suffixes are
invalid. End a source-EOF projection with exactly one newline, or use exactly
two newlines before a following H2.

Run `python3 scripts/sync-targeted-references.py --write` after changing a
Reference contract. The default command checks drift without writing.
`validate-skill-body-links.py` independently enforces exact source projection.
Reference links remain relative and repository-valid. Never require an agent to
read an entire reference directory.

This exact projection is Registry metadata. It remains AI-readable and source
fingerprinted, but root content budgets and semantic detectors evaluate the
authored decision surface without it. Bare links or manual loading prose do not
receive that exclusion.

Compiled Foundation and Domain references are build outputs. Do not hand-edit generated copies or paste their full content into Professional roots.

## Task, Evidence, and Completion Contracts

Every executable task uses Task Contract v2 from `src/control-model/core-contracts.json`.
It names Task ID, Status, Owner, inputs, read/write scope, non-goals, expected
output, acceptance, verification, Evidence Requirements, workspace and
integration ownership, review ownership, and stop conditions. DAG nodes also
name Dependencies. A Direct Task omits Dependencies when they have no meaning.

Status is exactly `in_progress`, `blocked`, `partial`, or `completed`.
Validation failure or unavailability, stale evidence, missing required review,
unreviewed changed scope, or unresolved blocking findings cannot become
`completed`. New work after `completed` starts a new Task ID.

Evidence is a visible task-local Markdown Ledger in the handoff. Use the
control-model fields and freshness rules; never create private persistence,
a daemon, a runtime task-state engine, or a hidden protocol record.

## Boundaries

- Source stays under `src/`; built output stays under `dist/`.
- Installed Skill folders contain root `SKILL.md`.
- Do not install source registries or user-specific content.
- Do not add internal task identities, private state, prompt transcripts, secrets, environment variables, or full command output to Skills.
- Do not create a new Agent Profile for a thinking dimension.
- Do not make a task agent rerun global routing.
- Do not claim host tool enforcement that the host configuration cannot express.

## Output and Escalation

An output contract names the artifact, evidence, unverified scope, and residual risk expected from the Skill. Escalation conditions name concrete facts that require a user decision, analysis, a different owner, or a more specialized review.

## Validation

```bash
python3 scripts/validate-skills.py
python3 scripts/validate-capabilities.py
python3 scripts/validate-domain-extensions.py
python3 scripts/validate-registry.py
python3 scripts/validate-skill-body-links.py
python3 scripts/validate-skill-content-size.py
python3 scripts/audit-skill-content.py --gate authoring
python3 scripts/eval-routing.py
python3 scripts/eval-skill-professionalism.py
```

Run affected behavior fixtures, builds, and simulated installation checks when
routing, references, packaging, or Profile support changes. A passing
structural fixture does not prove wall-clock performance, production accuracy,
or real-host Profile behavior.

# Skill Content Governance

rd-skills Skills are written for AI execution. The always-loaded root must provide the smallest complete decision contract; detailed or low-frequency material belongs in targeted references.

## Reader Path

- New authors: read [Required Root Structure](#required-root-structure), [Root
  Content](#root-content), and [Targeted References](#targeted-references) before
  changing a Skill.
- Layer maintainers: use [Layer Rules](#layer-rules) to confirm placement and
  delivery boundaries.
- Validation and release operators: go directly to [Validation](#validation),
  then follow the linked authoring or formal-release owner. Do not treat the
  surrounding schema history as an operator checklist.
- For the concise writing contract, start with the [Skill authoring base
  standard](skill_authoring_standard/SKILL_AUTHORING_BASE_STANDARD.md).

## Required Root Structure

Every Professional and Domain Skill uses:

1. Role
2. When To Use
3. Do Not Use
4. Required Inputs
5. Professional Decision Rules
6. High-Value Gotchas
7. Execution Checklist
8. Stop / Escalation Conditions
9. Output Contract
10. Targeted References

Every Foundation Skill instead uses this smaller ordered core:

1. Registry Trigger
2. Skill Role
3. High-Value Rules
4. Anti-Patterns
5. Targeted References

`Inputs`, `Execution Checklist`, `Stop Conditions`, `Output Contract`, and
`Standards` are optional Foundation sections. Add one only when it contains a
capability-specific decision, proof outcome, escalation, or deliverable that is
not already supplied by the control plane or primary Professional Skill.

Frontmatter contains only `name` and `description` unless a repository validator explicitly adds a field.
Description discovery budgets are:

| Skill kind | Recommended | Hard gate |
| --- | ---: | ---: |
| Control | 220 characters | 300 characters |
| Professional | 220 characters | 300 characters |
| Foundation | 180 characters | 260 characters |
| Domain | 180 characters | 260 characters |

A description names when to select the Skill, when not to select it, and the
consuming profile or owner-Skill boundary. The recommended budget is reported
as a content-efficiency advisory. The hard budget fails
`validate-skill-content-size.py` and cannot be excepted.

## AI Readability

AI-facing sentences target 24 words. A complex professional sentence may use
up to 32 words before tightening is expected. More than 40 words is a hard
failure. Every list item carries one primary decision; independent obligations
must be separate items.

The gate reads wrapped Markdown as logical units. It applies to the Main
Control Prompt, Agent Profile instructions, descriptions, Skill roots,
References, and compiled Layer 3 projections. Fenced code, standalone commands,
schema fields, table cells, and pure term enumerations are exempt. Inline code
is one atom, while links count their visible labels.

## Root Content

Keep rules that an agent needs on every selection:

- positive and negative routing boundaries;
- source-backed ownership and invariant decisions;
- minimal-correct design rules;
- high-cost failure modes;
- when the layer owns them, a short execution sequence, concrete stop
  conditions, and an observable output contract.

Remove background essays, generic engineering advice, repeated workflow prose, internal implementation details, and any rule that cannot change the current decision.
Foundation roots must not repeat the generic inspect/apply/return sequence,
task-contract inputs, primary-Skill return language, or generic evidence and
next-owner handoff. Repeated execution and role scaffolding remains actionable
in the content audit; it is not allowlisted merely because many Skills share it.

## Professional Independence

A Professional Skill must pass the transplant test: place its governed content
in an ordinary code repository whose agents know nothing about rd-skills, and
its professional judgments must still be valid. Professional content declares
capability and authority boundaries. Registry, Agent Profile, and control-plane
owners supply runtime routing, dispatch, and adaptation without changing that
domain knowledge.

The transplant test and a zero-finding result cover authored, governed domain
content. The canonical Registry-generated `Targeted References` adapter table
is physically embedded in the source root but logically excluded from that
content: it may select only an optional Reference and its depth. It may not
change the capability owner, invariant, failure behavior, acceptance condition,
domain verdict, or proof obligation. A manual, noncanonical, malformed, or
diverged table is not an adapter exception and remains governed content.

The audit covers every Professional root description and body, every physical
Professional Reference whether indexed or not, and all 18 Professional example
documents. Generic Engineering Brief, Task Contract, Task DAG, First Executable
Slice, Review Boundary, and Evidence Ledger knowledge is not self-coupling by
itself. A finding requires contextual evidence that a judgment depends on an
rd-skills-only role, level, versioned protocol, sibling route, branded schema,
or control-plane state.

Normal `python3 scripts/validate-skills.py` is the hard gate: each confirmed
finding is an error and produces a nonzero exit. Maintainers can inventory the
same deterministic source scope without weakening that gate:

```bash
python3 scripts/validate-skills.py --professional-independence-report
```

Report-only mode emits stable JSON and does not fail merely because findings
exist. Source-collection or schema errors still fail closed. This contextual
static detector can miss indirect or novel control dependencies and does not
inspect non-Markdown assets; a zero-finding report is bounded negative evidence,
not proof that every possible dependency is absent.

## Targeted References

A reference must answer one named decision problem. Its Registry entry owns
Reference Contract v2: path, type, load and skip conditions, required roles,
and required outputs. Every non-empty source section uses one canonical compact
table:

```markdown
| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [checklist](references/checklist.md) | decision-checklist | task-specific load condition | task-specific anti-condition | task-agent, review-agent | checklist-result, residual-risk |
```

Registry order is row order. Headers, separator, six-column order, labels,
spacing, and comma-space joins are exact. Only a literal pipe has an escape:
`\|`. An empty `reference_index` retains the exact no-task-local-Reference
sentinel and never renders an empty table.
Each path matches `references/(<slug>/)*<slug>.md`; a slug contains only
lowercase letters, digits, and single hyphen-separated words. Whitespace,
brackets, parentheses, backslashes, pipes, dot segments, and non-Markdown
suffixes are rejected before serialization. At source EOF the section ends in
exactly one newline; before another H2 it ends in exactly two. A parsed
frontmatter body may reconstruct that terminator only when the original source
proves exact one-newline EOF and exact fragment provenance.
`Required by` names the exact consuming Agent Profiles; it is not an audience
hint. `Required output` names the observable decision or evidence the consumer
must return before that Reference has completed its task-local purpose.
Suitable content includes deep failure matrices, technology-specific
checklists, migration or rollback detail, worked examples, and compiled Layer 3
guidance.

Use `scripts/sync-targeted-references.py --write` to update source projections.
Default mode is check-only. Bare links, manually diverged prose, `when needed`,
`when its subject changes`, the former five-line record, header or separator
drift, extra or missing columns, and noncanonical escapes are invalid.

The canonical section is Registry metadata projected into an AI-facing root.
It remains subject to exact-sync, link, and AI-readability validation. The root
collector preserves the complete source for document fingerprints, but blanks
that exact projection with line offsets intact before content budgets, decision
density, and Root semantic detection. This prevents Registry wording from
inflating authored Skill content or requiring duplicate semantic dispositions.
The projection may select only an optional Reference and its depth; it cannot
change the owner, invariant, failure behavior, acceptance condition, domain
verdict, or proof obligation supplied by authored content. No other section is
exempt: a bare link, manual loading rule, malformed table, or noncanonical
`Targeted References` body remains governed content and fails the applicable
contract.

Do not load a complete Foundation or Domain catalog. Do not use references as a second default-loaded body. Do not duplicate a Layer 3 Skill inside a Professional root.

`scripts/audit-skill-content.py` is the single report-producing collector for
both root Skill content and Reference content. It collects the deterministic
Root and Reference surfaces first, then retains
`semantic_disposition_application` as a separate audit sidecar. An invalid or
stale sidecar remains visible in the audit JSON and formal gate status; it does
not add errors to Root or Reference documents, advisories, disposition
contracts, or surface validation.

The strict validators consume fresh deterministic source, not the tracked audit
report or its application sidecar. `validate-reference-content.py` imports the
auditor's Reference collector, reads current source, and writes no report.
`validate-root-content.py` directly calls the auditor's Root collector for the
Main Control Prompt, Control/Professional/Foundation/Domain root bodies, and
each YAML `description` as a separate agent-facing document part. Its detector
is root-specific: it governs unconditional mechanisms, fixed
duration/threshold/status, fixed vendor/tool choices, mandatory artifacts,
tutorial density, long root examples, and context-free organization policy
without applying Reference preface or duplicate-block heuristics to roots. This
shared collector architecture replaces the proposed duplicate
`audit-reference-content.py`; do not add a second crawler or generated report.

The exact predecessor Root disposition schema versions 4 and 5 may remain
inside `config/skill-content-exceptions.yaml` only until an authorized recorder
migrates them. A line-independent candidate ID is not
sufficient evidence: every entry must also match the current occurrence
membership fingerprint and heading/section/local-context fingerprint. Copying
the same sentence, moving it under another heading, or changing its surrounding
condition therefore makes the disposition stale. Canonical Registry projection
is excluded as described above. Manual loading prose and every other root
section remain scanned.

Root disposition schema version 6 contains lifecycle schema version 4 with
bounded `previous` and `current` snapshot-version-4 records. A snapshot records candidate
identity, lineage, owning-document fingerprint, disposition, first-observed
release metadata, discriminated formal change reviews, and a closed
`bootstrap_refresh_reviews` chain. Review
evidence is provenance metadata; disposition rationale and Skill knowledge
remain in the existing entries. Ordinary audit and strict validation require
6/4/4. Only the bootstrap refresh and formal release recorders may migrate the
exact 5/3/3 or 4/2/2 predecessor shape to 6/4/4 while performing their requested
mutation. The 5/3/3 path validates each raw schema-3 snapshot and every non-empty
bootstrap chain before copying it, changes only the physical snapshot version,
then validates the migrated lifecycle. It handles a bootstrap in either bounded
snapshot position and preserves every historical review object, rationale,
origin, count, and recorded fingerprint. The 4/2/2 path retains the bounded
field-addition migration and creates an empty bootstrap-review list with its
schema-1 origin when applicable. Unknown fields, mixed schema triples, or an
invalid predecessor chain fail before writing. Rolling a release drops
older snapshot history, so this ledger is not a second baseline file or
knowledge base. Its schema-5 `detector_contract` uses
`root-semantic-detector-contract-v1` and hashes one deterministic, source-only
reachable-symbol projection rooted at document enumeration, document
fingerprinting, sentence/document candidate detection, and candidate folding.
The projection resolves lexical globals through the allowlisted auditor and
`validation_utils` modules, fails closed on missing, duplicate, malformed,
syntactically invalid, or unknown reachable symbols, and binds only the selected
`root_tutorial_density_min_words` member of the shared threshold map. Canonical
behavior AST excludes comments and docstrings. The already-evaluated Reference
and role contract models are projected by value, so their module initializers do
not recursively pull Core contract loading, validation, or documentation
rendering into Root currentness. Unreachable report writers, release-manifest
validators, Core hash utilities, other `validation_utils` code, and unused
thresholds are excluded rather than whole-file hashed. Stable repository
identities do not depend on a temporary module load name, Git state, wall-clock
evaluation timestamps, or a generated report. The global document-set fingerprint lets a
removed document be classified conservatively with the detector fingerprint
instead of treating a missing per-document hash as proof of a source rewrite.

The initial bootstrap has `previous: null`. Its existing dispositions use
`first_observed.status: unknown-pre-baseline`; therefore additions, removals, and
age are reported as null or unknown, never as historical zero. A current
bootstrap does not block authoring, but it is not formal-release-ready and
proves no pre-baseline history. When dispositions are current and resolved but
the bootstrap snapshot is stale, record an authoring-only refresh:

```text
python3 scripts/audit-skill-content.py --gate authoring \
  --refresh-root-disposition-bootstrap <reviewer> <rationale>
```

This option is mutually exclusive with release identity, date, and every formal
change-review flag. It requires `previous: null`, a bootstrap `current` without
release identity or formal `change_reviews`, a material live delta, and a
specific reviewer rationale. Stale or unresolved disposition entries and no-op
refreshes fail closed. Each version-1 refresh record binds prior/current state,
document, detector, candidate, and disposition fingerprints plus the minimal
sorted added IDs, removed prior entries, and prior overrides. Validation
reconstructs the complete chain backward from `current`, then verifies its
forward state links. The snapshot preserves the initial
`bootstrap_refresh_origin_state_fingerprint` and increments the closed
`bootstrap_refresh_review_count`; the count must match the list and the
reconstructed terminal state must match the origin. Deleted, reordered,
duplicated, overlapping, non-minimal, forged, or first-observed-rewriting
deltas fail.

Bootstrap-refresh review schema 1 has an immutable core-state hash projection
whose embedded snapshot schema is always 3, regardless of whether the physical
snapshot is schema 3 or 4. Base and chained fingerprints therefore remain
identical across the physical migration. A newly appended schema-1 review uses
the preserved chain tail and does not rewrite earlier objects. A future change
to hashed core fields requires a new refresh-review schema and an explicit
bridge; schema 1 must never be reinterpreted through the current physical
snapshot constant.

The origin, count, and chained hashes verify internal consistency and local
mutation of the tracked closed contract. These hashes are unkeyed; they do not
claim to resist an actor who coherently rewrites every evidence field. Review
still depends on the provenance of the reviewed tracked configuration.

Bootstrap refresh evidence is authoring evidence only. It never satisfies a
formal change review. The first formal release retains the complete bootstrap
chain, origin, and count in `previous`. Release `current` writes an empty chain,
null origin, and zero count; the next
release naturally evicts it with the bounded prior snapshot. To assign the required release identity and
roll the bounded snapshots after the Root source and detector are frozen, run:

```text
python3 scripts/audit-skill-content.py --gate formal-release \
  --record-root-disposition-release <release-id> \
  --released-on YYYY-MM-DD \
  [--change-review <candidate-id> <reviewer> <rationale>]... \
  [--source-replacement-review \
    <prior-id> <new-id>[,<new-id>...] <reviewer> <rationale>]... \
  [--source-removal-review \
    <prior-id> <reviewer> <rationale>]... \
  [--source-detector-replacement-review \
    <prior-id> <new-id>[,<new-id>...] <reviewer> <rationale>]... \
  [--source-detector-removal-review \
    <prior-id> <reviewer> <rationale>]...
```

Release dates are non-decreasing and cannot be in the future. A same-day
rollover is valid only when its release ID is different from every release ID
still present in the bounded current/previous snapshot chain; the chain order,
not a fabricated timestamp, records sequencing. Earlier dates, future dates,
and reused IDs fail closed. Same-day known ages are zero days, while inherited
`unknown-pre-baseline` entries remain unknown.

The recorder preserves prior first-observed metadata and marks only newly added
dispositions as first observed in the new release. Source-only removals and
unambiguous same-lineage replacements remain automatic source rewrites. When
one current candidate has multiple eligible source-only priors, repeat
`--source-replacement-review` or `--source-removal-review` until every prior in
that raw ambiguity group is adjudicated. A replacement selects a non-empty,
sorted, unique subset; a removal selects none. Explicit ownership is applied
before automatic inference, every prior has one review, and every successor has
at most one owner. Unselected additions become independent only after the whole
group is reviewed. Partial, unused, cross-lineage, non-added, disposition-
drifting, source-unchanged, detector-changed, or forged source-only reviews fail
closed. These reviews select single-origin provenance; they do not create a
multi-origin merge. Detector-only
removals remain unclassified until the current release snapshot contains an
exact accountable `change_review`; only then are they detector improvements. A
simultaneous source-and-detector change also remains unclassified unless it has
the matching named review. A replacement review selects a non-empty, sorted,
unique subset of current same-lineage additions. Each selected candidate keeps
the prior disposition and first-observed metadata. Unselected additions are
independent new dispositions first observed in the current release. A removal
review selects no replacements and remains valid even when the same-lineage
eligibility pool contains unrelated additions. Accepted dual-change reviews
enter `source_rewrites` while retaining their dual classification and reviewer.
A removal explained by neither source nor detector remains unclassified.

Every snapshot review uses the discriminated classifications
`disposition-change`, `detector-improvement`, `source-replacement`,
`source-removal`,
`source-and-detector-replacement`, or `source-and-detector-removal`. The recorder
derives the eligibility lineage, selected replacement IDs, prior/current document
fingerprints, and prior/current detector fingerprints; the CLI cannot report
those evidence values. Validation recomputes the exact evidence against the prior
snapshot and current source. Unknown, non-added, cross-lineage, duplicate,
multiply bound, unused, generic, stale, wrongly classified, or
disposition-drifting reviews fail closed. One prior may select multiple new
candidates, but one new candidate may bind only one prior. Repeated source-only
reviews adjudicate competing ownership; they never imply a many-prior merge.
The same prior ID cannot appear across review flags.
Post-bootstrap pending,
stale, invalid, or unclassified lifecycle state blocks formal release. The
recorder may consume a stale current snapshot, but only freshness is relaxed:
schema, duplicate, date, and review validation still fail closed. None of these
release requirements redefine Development Affected selection or the local Full
Regression authoring sub-gate.

Both recorders parse and hash one exact byte sequence for the complete
configuration. The managed writer requires that whole-file SHA-256 and the raw
source schema, checks the digest before constructing its bounded lifecycle and
schema-line update, writes and flushes a mode-preserving temporary file, then
checks the target digest again immediately before `os.replace`. A change to any
lifecycle, disposition, semantic application, Reference entry, comment, or
whitespace aborts without overwriting the concurrent bytes and removes the
temporary file. The digest is internal, not a CLI field or serialized review
claim. This optimistic check has a small residual race between the final read
and `os.replace`; eliminating it would require locking or platform-specific
compare-and-swap outside this repository contract. After a mismatch, reload and
recompute the comparison instead of retrying from stale in-memory state.

Root content schema version 7 counts every list item under Foundation
`High-Value Rules`, including nested items. Nesting cannot hide a constraint
from the 3-8 item, two-sentence, or decision-density contracts. Strict Root
validation uses the Foundation registry's explicit content class. A `compact`
root targets 400 words and hard-fails above 500; a `complex` root targets 500
words and hard-fails above 600. Every Foundation root also hard-fails above 900
tokens. Professional roots target 550 words or 850 tokens and hard-fail above
650 words or 1000 tokens. Domain roots target 500 words or 800 tokens and
hard-fail above 600 words or 900 tokens. Exact Registry-generated Targeted
References are excluded from these governed-body counts. A target overage is
`REVIEW_DENSITY`, or `TIGHTEN_BODY` above 90% of its triggered hard limit. A
hard overage is `BLOCK`. Structural hard gates have no exception entry, and
semantic dispositions cannot waive them.

These values remain the content-budget `classification`; they are not a claim
that the complete Skill needs no review. Audit schema 8 retains an independent
`review_state` with this closed precedence:

```text
BLOCK > TIGHTEN_BODY > REVIEW_READABILITY > REVIEW_CONTEXT > KEEP_WITH_ADVISORY > KEEP
```

The row retains every matched `review_reasons` value in the detector-declared
order. Readability is aggregated by Skill owner across the root, description,
and owned References. Context review distinguishes physical `line_count` from
`governed_line_count` and `projection_overhead_lines`; only a canonical
Registry projection can contribute projection overhead. Expert dispositions
remain release evidence and never reduce the deterministic review state.

Foundation registry schema version 6 requires every entry to declare exactly
one `content_class` and a closed-set `required_expertise_tags` list containing
its Foundation group tag. Professional schema 4 and Domain schema 5 require the
same qualification binding; each Domain entry also includes its own domain tag.
The tags are authoring evidence for expert-panel qualification matching and are
not runtime instructions. A `complex` entry must also explain the concrete coupled
decisions that cannot safely be governed as a compact card; a `compact` entry
must not carry a rationale. The class and rationale are authoring governance,
not runtime instructions, so builds validate them fail-closed but do not emit
them into installed Skill bodies or manifests.

`reference_content` schema version 4 preserves literal local-only preface facts
and adds the complete effective Reference Contract v2. Reference type, load
condition, do-not-load condition, required roles, and required outputs resolve
independently from local metadata, one exact
sibling index row, or one exact parent-root link, in that order. Provenance
retains every source path and line. Filenames, section headings, `Max Level`,
mechanically inverted conditions, generic “subject changes the current
decision” text, and fenced examples cannot establish effective metadata.
The collector rejects symlinked or non-regular source documents before reading
them, requires lexical and realpath owner containment, and hashes the current
registries, owner roots, sibling indexes, and registered Reference paths and
content into one deterministic SHA-256 source fingerprint. Consumers recompute
evidence acceptance, priority, selected values, status, and conflicts; report
claims are not accepted as their own proof.

The required default validator fails only structural defects:

- an indexed Reference is missing;
- a non-template Markdown Reference is orphaned from all registries;
- an indexed Reference has no H1;
- a non-template Reference has multiple H1 headings;
- a non-template Reference has an empty heading;
- effective-preface evidence is duplicated, ambiguous, conflicting, malformed,
  crosses its owner, or lets an index inherit a row it manages.

Template assets are allowed to remain unindexed and may contain multiple H1 or
empty placeholder headings. Those exceptions remain visible as reported facts;
a template with no H1 is still invalid.

The strict authoring gates are fixed at 60 lines for a targeted Reference,
except that the canonical Professional Skill router permits 62 lines for its
closed route table. Mode-contract References permit 80 lines, and Gate,
Checklist, or Decision headings permit 15 items. Missing effective reference
type, load condition, and do-not-load condition are also strict gates; literal
local-only coverage remains reported separately. Strict validation runs
`validate-reference-content.py --strict`, and the command must not pass while
any strict count is nonzero.
The resolved effective Reference type selects the 60/80-line budget; the legacy
local/filename advisory kind is used only while effective type remains unresolved.

The same collector reports four semantic candidate families. Malformed
governance fails default validation; selected unresolved families also gate
strict validation:

- `unconditional_absolute_candidate` finds `must`, `mandatory`,
  `non-negotiable`, `always`, `never`, `every`, `all`, and `only` outside
  fenced, example, and negative-example content. Hyphenated forms such as
  `read-only` are not `only` signals. Wrapped Markdown paragraphs and list
  items are evaluated as logical units with physical line ranges. Conditions,
  scoped Reference-loading or `only for/after/with/...` restrictions,
  questions, `not only` idioms, and negative/proof-limit context remain visible
  as downgraded rows.
  Detector-only downgrades additionally cover only: fully covered inline-code or
  exact lexical compounds; cells under the declared exact contextual headers;
  clause-local `prove`/`cover`/`prescribe` limits where every absolute token is
  governed; explicit Agent/Profile permission language; authority language in
  `Boundary record` cells; evidence-closure `Map every ... to ...` or
  `... in scope` rows from checklist/evidence/mode References; and short
  non-action classification fragments under the four declared headers. A mixed
  uncovered token, technical mandate, adjacent unlisted header, non-evidence
  `Map every` instruction, or action sentence remains unresolved.
- `fixed_number_candidate` finds money, time, percent, cost, SLO, and threshold
  values only when the literal is syntactically associated with the unit or
  policy term. Dates, RFC/standard/protocol versions, HTTP status codes,
  algebraic or process identifiers, inline-code spans, and true
  candidate/baseline/benchmark clauses are excluded. Other clauses in the same
  sentence remain eligible for detection.
- `exact_normalized_duplicate_block` groups decision-bearing Markdown blocks
  from at least two indexed Reference paths after normalizing only whitespace,
  case, bullet markers, and the owning Skill name. Blocks require at least
  three nontrivial lines and 36 tokens. Fences, examples, required prefaces,
  indexes, template assets, link-only blocks, and heading-only fragments are
  excluded.
- `templated_block_candidate` groups structural YAML key-path shapes and
  explicit Tool Permission, Handoff, Closure, Evidence, or Output table/field
  schemas across at least two owners. It compares schema structure, not matrix
  meaning, and remains distinct from exact normalized duplication.

Every candidate records a stable ID derived from finding, scope, and semantic
fingerprint. Line numbers exist only under sorted `occurrences`, so line movement
does not change sentence identity. Duplicate groups use scope `group` and bind a
separate evidence fingerprint to the sorted path/owner occurrence multiset.
Multiplicity is preserved while line numbers are excluded, so an added repeated
occurrence invalidates prior evidence but a line move does not. Group occurrences
also carry normalized decision-row/body fingerprints that exclude pure schema
headers and line locations. A separate sorted path/owner/content multiset binds
dispositions to row semantics, so unchanged membership cannot hide converged or
rewritten rows. The schema-version 7 block reconciles detector-downgraded,
untriaged, rewrite, resolved, unresolved,
priority, group, occurrence, and token counts.
The schema-version 7 object also carries the exact closed
`reference-semantic-detector-contract-v1` object
`{contract_version, algorithm, value}`. Its value hashes the reachable closure
of the pure Reference candidate entrypoint, including sentence parsing,
absolute/fixed-number rules, duplicate/template rules, behavior constants, and
their selected thresholds. Unreachable reporting, lifecycle, and release
utilities do not perturb it. The object, detector contract, summary, candidate,
occurrence, disposition contract, disposition entry, and nested evidence shapes
are closed; unknown fields and legacy aliases fail default validation.

`config/skill-content-exceptions.yaml` remains the single governance file. Its
versioned `reference_semantic_dispositions` entries name candidate identity,
skill owner, P0/P1/P2 priority, one of `rewrite`, `valid-contextual-rule`,
`false-positive`, or `time-bounded-exception`, accountable evidence, mitigation,
and review date. Only time-bounded exceptions may carry a future ISO
`review_after`; all other dispositions require null. `rewrite` remains
unresolved; the other three dispositions resolve the candidate. Stale entries,
identity, group-membership, or normalized-content mismatches, duplicates, malformed evidence, and
expired exceptions fail default validation. Strict validation requires zero
unresolved fixed numbers, templated groups, and P0/P1 unconditional absolutes;
exact duplicate groups and non-family P2 rewrites are non-blocking advisories.

`config/professionalism-release-review.yaml` separately binds formal content
review, not semantic dispositions. Schema 5 contains independent readability
and professional-completeness attestations. Each attestation points to its own
kind-specific decision. Readability has one schema-2 packet and exactly three
ballots. Professional Completeness formal evidence is schema 3: a decision
binds its packet, machine-derived fresh/carry plan, current fresh immutable
discovery/request/final capsule chains and ballots, and every carried target's
direct fresh-origin evidence.
Readability schema-2 evidence binds exactly the current target-authority
manifest, Readability detector contract, and Actionability detector contract,
plus every density, readability, or weak front-loaded-action target. Root,
Reference, audit-summary, and report-presentation drift do not independently
change that three-key currentness binding. Its packet independently replays the
detector over the current closed source-selector inventory and binds each full
canonical sentence to its logical document-part context and exact source span.
Ballots decide every finding exactly once; any nested tightening derives each reviewer
document disposition before the document two-of-three majority. Professional
completeness schema-3 evidence binds
all 188 non-Control Skill packages, including complete root and indexed
Reference content, Registry responsibility and expertise contracts, source
anchors, examined failure and omission candidates, independently derived
adjacency evidence, and proof limits. Adjacency evidence embeds the complete
catalog ranking while requiring every Registry-declared relationship, every
source-declared relationship, overall Top 5, positive per-signal Top 2, and
rank-independent phrase-aware negative-route conflict. Registry declarations
and source declarations remain separate. Source declarations are directional
from target to candidate. They come only from the bound Root and indexed
References. The selector accepts exact inline-code Skill IDs only in imperative
route or handoff sentences and routing, owner, risk-gate, verification, or
handoff table cells. It excludes frontmatter, fenced code, example, history,
background, and generated Layer 3 sections. Unknown and self relationships
fail closed. The current per-target and catalog limits are 57 and 4083. Each
required candidate carries canonical selection reasons. A
reviewer may request another ranked candidate only after inspecting the
discovery capsule. The immutable candidate request records its discovery reason,
exact ranking evidence, and candidate-material fingerprint; an empty request is
also explicit. The final review capsule binds the discovery and request SHA-256
values and adds the requested package's complete source. A ballot binds only
that final capsule and must anchor both packages; it may not omit a required
candidate. Required and added review counts remain separate in the derived
decision evidence.

The exact r11 cap-50 packet and exact r14 selector-v1 packet remain auditable
through review-ID, packet-SHA-256, and old-contract-fingerprint allowlists.
Their adapters are invocation-local comparison views. They do not rewrite
artifact bytes. They do not authorize a generic legacy selector bypass.

Schema-3 source grounding is stricter than the historical schema-2 structural
overlap check. Non-defect criterion, failure-mode, and omission evidence quotes
an anchor-local non-generic bigram; non-defect adjacency rationales quote one
from each package. Defect evidence has only the closed relaxed threshold in the
panel contract. Phrases never cross lines or anchors, and an extreme shared
generic token in the lexical stream also breaks phrase adjacency. An extreme
shared source-free template combined with low grounding fails validation.

Readability uses three independent senior reviewers with unique voter, agent,
and role identities; each ballot covers every target and cannot abstain. A
Professional Completeness fresh reviewer pool uses round-wide unique voter and agent
IDs and non-empty capsule-bound ballot subsets. For every fresh Skill, the aggregator must derive
exactly two domain reviewers whose closed-set expertise tags cover that target
and one reviewer whose only panel-axis tag is
`skill-reference-architecture`; the packet contains no reviewer pre-assignment
table. It decides each ordinary criterion independently by two-of-three,
retains the overall ballot majority, rationales, and dissent as audit evidence
only, and records artifact paths and SHA-256 values. Defects distributed across
different ordinary criteria do not combine into a correction. Any qualified domain-reviewer defect on
professional correctness, erroneous rules, material omissions, failure modes,
boundary conditions, or verification methods changes the final disposition to
`unresolved-professional-disagreement`, regardless of an accepting majority.
Schema 3 has no arbitration or override. Maintainers do not choose or override
the result. Schema 1 and schema 2 Professional decisions remain auditable but
cannot satisfy formal release or authorize carry. Earlier schema-3 review
contract fingerprints are likewise bounded historical evidence and cannot
authorize currentness, promotion, Formal Release, or carry. Exact carry requires an
unchanged review-visible binding and a direct depth-zero fresh origin; an
all-carry round has no reviewer pool, ballots, capsule-chain artifacts, or input
bytes. Professional carry is self-contained: each carried target binds exact
`origin_review_id`, `origin_commit`, `origin_verdict_digest`, and
authenticated compact vote fingerprints;
formal validation never requires a predecessor file or round chain. Formal
Fresh `origin_commit` is the clean, stable `HEAD` at which the validated
decision and current package, review, and dependency bindings are projected
into the attestation. It is not the reviewer-execution commit, decision-file
creation commit, later promotion commit, or fixed-artifact commit. Attestation
generation checks that `HEAD` and the nonignored tree remain unchanged and
clean through the projection write boundary. Carry preserves that direct fresh
origin commit; a later fixed-artifact commit does not rewrite it.
Formal readiness requires current contract/plan/bindings/provenance and recomputed
cost. Formal readiness requires zero `tracked-tightening`, unresolved
`detector-false-positive`, or `rewrite-required` readability decisions, zero
professional corrections, and zero unresolved professional disagreements
across 188 packages. Static qualification claims prove declared tag coverage,
not real-world identity, credentials, or experience.

Current Professional schema-3 packets store no target-level
`package_fingerprint`; each target has one `review_binding` containing
`package_material_binding`, direct `dependency_material_bindings`, and the
single `review_unit_binding`. Decisions retain that review-unit binding and the
packet/ballot artifact chain, but no package or review-binding aliases. Compact
storage keeps one top-level `review_contract_fingerprint`, one shared
`dependency_material_catalog`, and per-Skill package material, review unit,
dependency IDs, votes, result, expertise, and direct-origin provenance. It has
no `source_fingerprints`, per-finding dependency map, or duplicated origin
material. The tool derives these projections, validates closed fields, and
requires all 188 packages fresh whenever the Professional review contract
changes.

Professional compact schema-2 bytes use the physical
`professional-string-catalog-v1` codec. The schema version, kind, axis, review
ID, decision date, and review-contract fingerprint remain literal routing
fields. Every other string value that occurs at least twice is represented by a
negative reference into one sorted, unique canonical string catalog. This
catalog is serialization only: the shared attestation owner expands it before
the existing semantic and current-authority validation, then requires exact
canonical reprojection. A current Professional schema-2 object without that
codec, an incomplete or unused catalog, a literal eligible value, or an
alternative catalog/reference ordering fails closed. The codec does not change
the Professional review-contract fingerprint or authorize carry. Generation
and promotion rederive the same encoded bytes from the authenticated decision;
after promotion, the tracked artifact SHA-256 and clean `HEAD` bytes remain the
external anchor.

Readability compact storage keeps the
`readability-complete-target-authority-manifest-v2` digest as its sole source
authority. Each content or actionability target and each readability finding
stores one tool-generated `readability-review-unit-binding-v3` digest over its
identity and normalized local authority from that manifest. The digest excludes
votes and outcomes; the document conclusion remains derived from finding votes.
The top-level `review_artifacts` object retains the packet SHA-256, exactly three
voter-keyed ballot SHA-256 values in voter order, and the decision SHA-256.
Attestation generation and promotion validate those immutable runtime artifacts,
rederive the compact Readability projection from the decision, and require exact
equality before the destination compare-and-swap. A direct compact parser proves
closed shape, current source authority, exact coverage, and internal results; it
does not independently authorize altered conclusions. After promotion, tracked
`HEAD` bytes and the Formal Release manifest content SHA-256 are the external
artifact anchor. Readability evidence created under the prior currentness,
manifest, or review-unit contract requires a fresh review and cannot authorize
currentness or Formal Release; compact storage remains schema 2.

The tracked Expert Panel inventory is exactly
`evals/expert-panel/readability.json`,
`evals/expert-panel/semantic-disposition.json`, and
`evals/expert-panel/professional-completeness.json`. Each file is one current
compact attestation, is at most 4 MiB, and uses replacement, not append. Full
packets, templates, ballots, capsules, decisions, and other review context exist
only under ignored `.rd-skills/expert-panel/<run-id>/`. A complete scene may be
retained as an optional CI or Release artifact outside the tracked tree. Git
history is the audit trail for replaced attestations: there is no keep-last-N,
dated, or `rN` repository archive. Formal release requires all three compact
attestations to be tracked, equal their `HEAD` blobs, clean, and current.
Pending or stale evidence remains non-blocking for `authoring_gate`, but keeps
`release_gate=release-not-ready`. Authoring blockers cannot be waived.

### Professional Review Cost Authority

`src/control-model/core-contracts.json` at
`final_goal_contract.professional_review_cost_fixtures` owns the professional
review cost policy and thresholds. Currentness is derived from the measured
188-case inventory, exact-three review invariants, arithmetic, and ceilings; it
does not compare catalog, material, projection, case, or review-contract hashes
with a checked-in cost snapshot.
`reports/professionalism-regression-report.json` is the sole machine-readable
professionalism readiness authority and is derived evidence; it does not own or
override the cost contract.
The current 188-package cost fixture satisfies the
one-reviewer-added-relationship-per-target budget. This static cost result does
not replace the final Core formal gate.

When current Root or Reference evidence cannot carry an existing semantic
disposition forward exactly, use the orthogonal `semantic-disposition` panel.
Its packet selects only those current candidates. Exact carry-forward candidate
IDs and stale old IDs remain packet provenance, not voting targets. Root reuse
requires identical stable identity, occurrence, and context evidence. Reference
reuse requires identical stable identity and, for groups, identical membership
and normalized-content evidence. Every other current candidate receives three
independent votes with no abstention. Build and check an immutable round with:

```text
python3 scripts/expert_panel_review.py prepare --panel-kind semantic-disposition --audit reports/skill-content-audit.json --review-id REVIEW_ID --created-on YYYY-MM-DD --semantic-re-review-axis root --semantic-re-review-axis reference --reviewer VOTER_1 AGENT_1 ROLE_1 EXPERTISE_1 --reviewer VOTER_2 AGENT_2 ROLE_2 EXPERTISE_2 --reviewer VOTER_3 AGENT_3 ROLE_3 EXPERTISE_3 --out .rd-skills/expert-panel/REVIEW_ID/packet.json
python3 scripts/expert_panel_review.py materialize-ballot --packet .rd-skills/expert-panel/REVIEW_ID/packet.json --audit .rd-skills/expert-panel/REVIEW_ID/inputs/skill-content-audit.json --template .rd-skills/expert-panel/REVIEW_ID/ballots/VOTER_1.template.json --template-sha256 TEMPLATE_1_SHA256 --manifest /private/tmp/REVIEW_ID/VOTER_1.manifest.jsonl --manifest-size MANIFEST_1_SIZE --manifest-sha256 MANIFEST_1_SHA256 --stdin-framing raw --out .rd-skills/expert-panel/REVIEW_ID/ballots/VOTER_1.json
python3 scripts/expert_panel_review.py materialize-ballot --packet .rd-skills/expert-panel/REVIEW_ID/packet.json --audit .rd-skills/expert-panel/REVIEW_ID/inputs/skill-content-audit.json --template .rd-skills/expert-panel/REVIEW_ID/ballots/VOTER_2.template.json --template-sha256 TEMPLATE_2_SHA256 --manifest /private/tmp/REVIEW_ID/VOTER_2.manifest.jsonl --manifest-size MANIFEST_2_SIZE --manifest-sha256 MANIFEST_2_SHA256 --stdin-framing raw --out .rd-skills/expert-panel/REVIEW_ID/ballots/VOTER_2.json
python3 scripts/expert_panel_review.py materialize-ballot --packet .rd-skills/expert-panel/REVIEW_ID/packet.json --audit .rd-skills/expert-panel/REVIEW_ID/inputs/skill-content-audit.json --template .rd-skills/expert-panel/REVIEW_ID/ballots/VOTER_3.template.json --template-sha256 TEMPLATE_3_SHA256 --manifest /private/tmp/REVIEW_ID/VOTER_3.manifest.jsonl --manifest-size MANIFEST_3_SIZE --manifest-sha256 MANIFEST_3_SHA256 --stdin-framing raw --out .rd-skills/expert-panel/REVIEW_ID/ballots/VOTER_3.json
python3 scripts/expert_panel_review.py validate --packet .rd-skills/expert-panel/REVIEW_ID/packet.json --audit .rd-skills/expert-panel/REVIEW_ID/inputs/skill-content-audit.json --ballot .rd-skills/expert-panel/REVIEW_ID/ballots/VOTER_1.json
python3 scripts/expert_panel_review.py validate --packet .rd-skills/expert-panel/REVIEW_ID/packet.json --audit .rd-skills/expert-panel/REVIEW_ID/inputs/skill-content-audit.json --ballot .rd-skills/expert-panel/REVIEW_ID/ballots/VOTER_2.json
python3 scripts/expert_panel_review.py validate --packet .rd-skills/expert-panel/REVIEW_ID/packet.json --audit .rd-skills/expert-panel/REVIEW_ID/inputs/skill-content-audit.json --ballot .rd-skills/expert-panel/REVIEW_ID/ballots/VOTER_3.json
python3 scripts/expert_panel_review.py aggregate --packet .rd-skills/expert-panel/REVIEW_ID/packet.json --audit .rd-skills/expert-panel/REVIEW_ID/inputs/skill-content-audit.json --ballot .rd-skills/expert-panel/REVIEW_ID/ballots/VOTER_1.json --ballot .rd-skills/expert-panel/REVIEW_ID/ballots/VOTER_2.json --ballot .rd-skills/expert-panel/REVIEW_ID/ballots/VOTER_3.json --decided-on YYYY-MM-DD --record-dir .rd-skills/expert-panel/REVIEW_ID/panel
python3 scripts/expert_panel_review.py attest --panel-kind semantic-disposition --review-id REVIEW_ID --decision .rd-skills/expert-panel/REVIEW_ID/panel/decision.json --audit .rd-skills/expert-panel/REVIEW_ID/inputs/skill-content-audit.json --out .rd-skills/expert-panel/REVIEW_ID/attestation.json
```

`prepare` atomically creates the copied audit and exactly the three unfilled,
create-once templates named by `VOTER_1`, `VOTER_2`, and `VOTER_3`; do not run
`template` afterward. Each independent reviewer writes only its assigned
manifest outside the repository. The task agent records that manifest's exact
size and SHA-256 and uses `materialize-ballot` to create the canonical ballot.
The majority record preserves all three rationales. It never writes semantic
disposition entries; in particular, a `rewrite` majority requires a source
edit. This panel is authoring lifecycle evidence only and cannot satisfy either
formal readability or professional-completeness attestation.

`config/skill-content-exceptions.yaml#semantic_disposition_application` is the
schema-1 application binding. After compact selector finalization it binds
`evals/expert-panel/semantic-disposition.json`, the semantic attestation kind,
and the SHA-256 of the attestation's exact bytes. Until that real artifact and
hash exist, the configured selector remains pending and cannot satisfy formal
release. Compact validation authenticates the three-vote result and source
binding without requiring runtime files from the tracked tree. It then
requires every non-`rewrite` target's current `(axis, candidate_id)` disposition
entry to match the majority exactly. A `rewrite` target stays incomplete while
the old candidate exists; completion requires the old candidate and its entry
to disappear without any new eligible candidate or unrelated evidence drift.
Root strict and Reference strict do not consume this binding: they validate
their fresh deterministic collector results. The canonical audit retains the
binding as its application sidecar. Core Principles runs the audit producer
with `--gate authoring`; its authoring outcomes remain deterministic-content
checks, while its formal-only outcome requires both
`gate_status.formal_release.status=pass` and
`semantic_disposition_application.status=current`. Professionalism likewise
keeps a stale application out of authoring blockers, but preserves its exact
error as a release blocker and limitation; `--require-expert-content-review`
then exits non-zero. The binding records provenance only; Root and Reference
disposition entries remain the single source of truth for applied governance.

The packet retains four closed source fingerprints: Root and Reference candidate
manifests plus the two reachable-behavior detector contracts. Currentness
rechecks both semantic detectors, the complete eligible candidate ID set,
candidate identity and local text fingerprints, Root occurrence/context
evidence, Reference group membership/content evidence, and every review target
and exact carry-forward set. Governance-only fields are excluded from candidate
evidence. Reference `priority` is also excluded because the disposition entry
selects it. A change to detector, candidate identity or text, local context, or
group evidence still invalidates the round.
Raw and detector-downgraded candidate counts remain review-time provenance;
their churn does not invalidate a round when the detector and complete eligible
candidate set and evidence remain unchanged.

Historical Semantic schema-1 artifacts remain readable only for audit and
strict reprojection. They cannot authorize currentness, application, promotion,
carry, or Formal Release. Current Semantic evidence uses artifact schema 2 and
compact storage schema 2; detector or candidate-binding drift fails closed.

## Layer Rules

- Control content owns dispatch, scheduling, progress, review/repair routing, and closure only.
- Professional content owns complete engineering judgment for one task type.
- Foundation content solves one reusable high-value engineering decision.
- Domain content solves one domain-specific invariant or failure problem.
- A targeted reference owns decision depth only when its load trigger selects it.

An acceptable enhancement helps the selected agent answer all six professional
judgment questions:

1. What should I inspect now?
2. Which owner and invariant control this decision?
3. What is the smallest correct design?
4. Which failure mode is easy to miss?
5. When must I stop or escalate?
6. What observable evidence completes the task?

Place each rule in its single owning layer or triggered reference. Do not copy
the same rule across layers, preload catalogs, create Profiles for thinking
dimensions, or add private protocol fields. Add guidance only when it changes a
concrete decision, prevents a costly failure, improves defect discovery,
shortens a critical path, or unblocks downstream work. General background stays
outside the loaded Skill path. Apply the existing [Professional
standard](skill_authoring_standard/PROFESSIONAL_SKILL_AUTHORING_STANDARD.md),
[Foundation standard](skill_authoring_standard/FOUNDATION_CAPABILITY_AUTHORING_STANDARD.md),
and [Domain standard](skill_authoring_standard/DOMAIN_EXTENSION_AUTHORING_STANDARD.md)
for layer-specific form; this document owns cross-layer placement. [Quality
Model](QUALITY_MODEL.md) and [Benchmarks](BENCHMARKS.md) own evidence
interpretation and proof limits.

Before adding a Skill, place new knowledge in this strict order:

1. an existing Targeted Reference;
2. an existing Foundation or Domain Skill;
3. an existing Professional Skill;
4. a new Professional Skill.

New frameworks, libraries, protocols, platform sub-capabilities, scenarios, and
gotchas default to one of the first three owners. They do not justify a new
Host-visible Skill. Add a Professional Skill only when the capability owns a
stable, independent Primary Route and a distinct task boundary that cannot be
owned coherently by an existing Professional Skill.

Foundation is a capability-modifier layer and Domain is `modifier-only`.
Neither becomes a Runtime top-level Skill. Layer 3 selection is an ordered
unique list of zero to three items. More than three items or any duplicate fails
closed; never truncate the selection. Higher risk changes which Layer 3 items
are selected, not the maximum count. Each task receives one Primary
Professional Skill, the selected Layer 3 items, then only the necessary Targeted
References. Task and Review consume the route fixed by Main and do not globally
reroute.
Multi-role Professional Skills declare role-neutral inputs once and
role-specific inputs through `required_inputs_by_role`; analysis cannot require
a future diff, and review cannot be dispatched without an actual diff or named
artifact appropriate to its mode.
They also declare role-specific outputs through `output_contract_by_role` while
keeping `output_contract` as the common union exposed by discovery surfaces.
Role-labelled output blocks must match their own profile and cannot be swapped.

## Validation

Root and Reference strict validation always uses fresh source:

```bash
python3 scripts/validate-skills.py
python3 scripts/validate-capabilities.py
python3 scripts/validate-domain-extensions.py
python3 scripts/validate-skill-body-links.py
python3 scripts/validate-skill-content-size.py
python3 scripts/audit-skill-content.py --gate authoring
python3 scripts/validate-reference-content.py --strict
python3 scripts/validate-root-content.py --strict
```

These focused entrypoints remain available for diagnosed failures. They do not
replace Development Affected, local Full Regression, or the complete Core
Formal Release gate:

| Consumer | Authoring | Formal release |
| --- | --- | --- |
| Standalone content audit | `python3 scripts/audit-skill-content.py --gate authoring` | `python3 scripts/audit-skill-content.py --gate formal-release` |
| Core Principles | `python3 scripts/eval-core-principles.py --gate authoring` | `python3 scripts/eval-core-principles.py --gate formal-release` |
| Standalone professionalism diagnostic | `python3 scripts/validate-professionalism-regression.py --strict` | `python3 scripts/validate-professionalism-regression.py --strict --require-expert-content-review` |

Core's audit producer always uses the authoring audit invocation and evaluates
the retained sidecar only through its formal-only outcome. Run a standalone
producer only to diagnose a verified Core failure; a second unchanged producer
pass is not additional evidence. Running Core starts its declared producer
graph and refreshes the audit report.

Size and actionable-duplication findings are review signals, but required
decision content must not be removed merely to meet a line count. Raw shared
lines remain visible; only Targeted Reference policy lines are excluded from
actionable duplication. Move low-frequency depth, tighten repetition, and
preserve every layer-specific decision and proof contract.

The professionalism regression authority consumes both `reference_content`
and `root_content`, recomputes each source fingerprint from the current tree,
and rejects stale tracked audit evidence.
`reference_content_summary.strict_ready` and
`strict_ready_basis=reference-strict-v4` are Reference-only fields. Reference
structural readiness covers inventory,
effective-preface, size, and decision-item gates; Root structural readiness
covers the strict Foundation root budget and decision-density contract.

Reference and Root semantic triage are reported independently from structural
readiness. Triage is complete only when no candidate is unclassified and every
configured disposition is valid and applied. `rewrite` counts as triaged but not
resolved. Scoped strict blockers and incomplete triage enter the authoring gate.
Top-level `content_readiness` schema 10 publishes Reference, Root, both expert
axes, and aggregate views. Readability and professional completeness remain
independent disclosures and do not redefine the authoring gate. Formal release
requires both axes and the exact Semantic application binding to be current.
Readability covers every current
`REVIEW_DENSITY`, `TIGHTEN_BODY`, and readability advisory target. Professional
completeness covers all 188 non-Control packages. Neither panel can override an
authoring blocker. The complete release check is
`python3 scripts/eval-core-principles.py --gate formal-release`; its aggregate
`professionalism-formal-release-ready` outcome requires the producer process to
pass and the sole JSON authority to report `release_gate=release-ready`.
`scripts/validate-professionalism-regression.py` is the only producer of
`reports/professionalism-regression-report.json`; Core Principles owns the
complete ordered freshness run against current Root, Reference, coverage, and
default release-review inputs. Productization validates that saved JSON's
closed schema, internal semantics, blockers, gates, and expert bindings without
rerunning the producer. Formal-release orchestration writes schema-4
professionalism/Core JSON and Markdown projections under
`.rd-skills/formal-release/<captured-head>/reports/`. That ignored scene is
bound to the captured `HEAD` and validated locally; Markdown is not a readiness
authority, and Core authoring refreshes only tracked ordinary JSON.

Canonical fixed-attestation paths, not Readability or Professional policy
config, select Expert Panel evidence; the formal target remains all 188
non-Control packages. Formal release requires a current Semantic application
bound to the exact fixed-attestation bytes. Reuse all three compact attestations
while their strict current validators pass; replace an axis only after source,
detector, binding, or review-contract drift. Prior attestations remain auditable
through Git history only. These fixed attestations do not prove that the final
local formal gate passed.

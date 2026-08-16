# Quality Model

rd-skills quality is the combination of control correctness, professional judgment, bounded context, observable evidence, and maintainable packaging.

## Control Correctness

- Direct Tasks begin after one classification.
- Analyzed Work receives one complete source-backed initial Analysis.
- Accepted decisions remain authoritative until new evidence invalidates a
  protected decision; then Delta Analysis covers only its transitive impact.
- The First Executable Slice is found before unnecessary plan breadth.
- Task completion, Task switching, ordinary discovery, and an unreached Review
  Boundary do not repeat Analysis.
- Writes are parallel only with safe host isolation and non-overlap.

## Professional Judgment

- Every Task is a complete semantic change with one primary Professional Skill;
  mechanically different files, functions, layers, tests, or edit steps do not
  create separate Tasks.
- Work with materially different Primary Professional Skills remains separate
  even when Tasks share a combined Review Boundary.
- Implementation Layer 3 Skills are triggered by Task risks or technologies.
  Review assignments independently select zero to three Layer 3 Skills from
  review risk; review selection is not a Task-side union.
- Combined review preserves all required Review Skills, Specialist obligations,
  and professional-risk dimensions.
- Owner, invariant, placement, failure behavior, and validation are explicit.
- New material risk stops or escalates instead of silently widening scope.

## Evidence Quality

- Validation runs after the latest material edit.
- Fresh, scope-correct validation with a trustworthy oracle is reused unless a
  concrete freshness, coverage, oracle, flake, environment, reviewer-doubt, or
  independent-reproduction trigger requires another run.
- Implementation review examines the actual diff and every changed file;
  artifact review examines the bounded artifact, decision criteria, and
  supporting source evidence.
- Effective Level sets review depth; minimum sufficient Review/Risk Boundaries
  set frequency. L1-L3 related scope defaults to one combined independent final
  review, L4 adds triggered specialist depth rather than automatic rounds, and
  L5 retains its pre-implementation and final requirements.
- A current Review Boundary carries its Boundary and Review Round IDs, strategy,
  Effective Level, required Review Skills, Specialist obligations, Covered Task
  IDs, changed scope, professional-risk dimensions, current validation binding,
  assignment schedule, and primary-close ordering. Exactly one primary and zero
  or more specialist review-agent assignments share the round; each assignment
  has one registered Review Skill and bounded review-risk Layer 3 selection.
  Specialists do not close Tasks or add rounds. The primary consumes their
  current results and emits one artifact referenced exactly by every covered
  Task projection.
- Only material current-task findings require bounded Repair. Fundamental
  failure may stop `blocked` with Reviewed and Unreviewed Scope; `pass` still
  requires the complete required changed-scope review.
- Any scoped material edit invalidates validation and review evidence for
  intersecting scope and transitive Task dependencies only, retaining
  unaffected current evidence. Repair receives fresh targeted validation and
  scoped independent re-review; a re-review covering the final obligation
  subsumes another Final Review.
- Unverified scope and residual risk are stated plainly.

## Evidence Privacy

rd-skills has no required product-runtime or private telemetry channel.
Ordinary agents use visible task contracts, source, diffs, commands, validation,
review, repair, and handoff evidence. They do not write private event streams,
internal task identities, prompt transcripts, or hidden evidence records.

Evidence artifacts exclude raw prompts, secrets, environment variables, full
command logs, personal archives, and user-specific content. Local evaluation
report retention follows repository and user policy. A retained report must
identify its evidence type and source freshness; persistence does not make
stale output current. [Benchmarks](BENCHMARKS.md) owns interpretation and proof
limits.

## Content Quality

Professional and Layer 3 Skills are concise AI instructions, not background articles. Their decision rules, gotchas, execution checklist, stop conditions, output contract, and targeted references must change a current engineering decision.

## Claim Quality

Structural validators prove structure. Deterministic and captured fixtures prove
only their declared contracts. Default code-generation commands prove only case
definition integrity, checked-in harness execution, and starter negative-control
behavior; they do not evaluate a generated candidate. These artifacts do not
prove real-host startup, wall-clock performance, provider behavior, production
accuracy, or installed user experience. Generated catalogs are local discovery
assets. The handwritten scorecard records release expectations, not generated
status.
Repository evidence does not support project rankings,
popularity, external-adoption, privacy-guarantee, or competitor-superiority
claims beyond the specific evidence it contains.

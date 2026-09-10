# Implementation Structure Evidence Patterns

- Trace generated placement as `editable source -> generator/template/config -> artifact -> committed/derived policy -> regen/freshness check`.

Use this reference to close reuse, owner-private placement, deliberate-separation, or generated-source claims after the decision owner and candidate locations are known.

## Evidence Record

- Record searched owners, callers, tests, generated consumers, terms, and paths.
- Compare semantics, authority, failure behavior, lifecycle, and evolution for each reuse or deliberate-separation candidate.
- Record selected and rejected locations, visibility, imports, tests, source authority, generated policy, drift control, and delete condition.
- Bind `editable source -> generator/template/config -> artifact -> committed/derived policy -> regen/freshness check` to current paths and owners.

## Validation Plan

- Exercise focused owner behavior and the failure mechanism that a wrong placement would break.
- Check imports, visibility, public/export absence, and forbidden cross-owner edges.
- Regenerate from authoritative inputs and compare semantic or mechanical output according to repository policy.
- Include a negative control for unknown generated authority and an owner-external/shared placement.

## Proof Limits And Residual Risk

- Local search and tests cover only inspected owners, callers, generated surfaces, and fixtures.
- Build graph and freshness checks cover declared inputs and targets; reflection, plugins, dynamic loads, undeclared tools, and external consumers remain outside the claim.
- Record uninspected consumers, ambient generator inputs, intentional-copy drift, missing delete conditions, and unsupported platforms as residual risks.

## Anti-Patterns

- Reject convention-, size-, utility-, or test-only exports as ownership or placement proof.

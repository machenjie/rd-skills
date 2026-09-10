# Engineering Brief

Create a Brief only when complex cross-agent work needs stable engineering decisions. Analysis can return a direct source-backed answer without this artifact. Ordinary implementation does not require it.

## Goal

Requested behavior and observable acceptance.

## Important Constraints and Invariants

Current owner, material behavioral or data invariants, dependency direction, affected consumers, and authority limits that matter to the decision.

## Key Decisions

Source-backed choices and rationale. Reuse existing structure; introduce an abstraction only for current requirements or a demonstrated variation or boundary. State the next implementable change once important decisions are clear.

## Validation

Checks that establish normal, invalid, boundary, forbidden, and regression behavior where relevant. Include post-final-edit freshness, recovery or rollback evidence for affected irreversible effects, and proof limits.

## Unresolved Issues

Concrete questions that could change implementation, their evidence, and affected scope. Preserve settled decisions and investigate again only when new evidence invalidates them. Decompose only for real dependencies or independently useful work; no mandatory DAG or Review Boundary.

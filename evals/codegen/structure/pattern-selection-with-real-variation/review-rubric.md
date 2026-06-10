# Review Rubric

## Passing Standard

The solution passes when current provider variation is represented behind a
stable contract, provider-specific behavior stays local to providers, and
runtime lifecycle costs are explicit.

## Scoring

- 30 percent pattern selection for real current variation.
- 25 percent provider contract tests and no caller branching.
- 20 percent retry, error mapping, timeout, and lifecycle placement.
- 15 percent object, method, module, and file placement rationale.
- 10 percent payment idempotency and residual-risk evidence.

## Automatic Failure Conditions

- If/else scattered across service code for concrete providers.
- Base class only for shared code.
- Provider creates client per request.
- No contract tests for provider behavior.
- Retry or timeout behavior is invisible to the provider boundary.

## Reviewer Notes

Reward strategy or adapter/provider when the contract is current and tested.
Penalize inheritance that exists only to share helper code.

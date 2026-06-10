# Review Rubric

## Passing Standard

The solution passes when clients and pools are lifecycle-managed, network or
storage IO is visible, and resources are cleaned up on all paths.

## Scoring

- 30 percent reusable client or pool lifecycle design.
- 25 percent response body, stream, cursor, and shutdown cleanup.
- 20 percent timeout, retry, keep-alive, and pool sizing.
- 15 percent repository/adapter/proxy pattern decision quality.
- 10 percent observability and tests.

## Automatic Failure Conditions

- Per-operation client construction remains.
- Response body leak remains.
- No pool sizing or lifecycle owner is declared.
- Hidden network IO behind repository or adapter remains.
- Timeout and retry behavior are absent.

## Reviewer Notes

Repository and adapter patterns are acceptable only when IO visibility,
lifecycle, and cleanup are explicit.

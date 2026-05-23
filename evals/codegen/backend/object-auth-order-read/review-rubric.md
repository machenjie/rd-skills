# Review Rubric

## Passing Standard

The implementation must enforce object level authorization on every order read
path and prove tenant isolation with tests. It should be easy to identify who
can read an order and why a denied read was blocked.

## Scoring

- 35 percent authorization correctness across owner, tenant admin, support, and anonymous cases.
- 20 percent data protection for scoped queries, safe status codes, and redacted logs.
- 20 percent test coverage for role matrix, cross tenant denial, and regression paths.
- 15 percent maintainability for a clear policy boundary and simple repository contract.
- 10 percent auditability for useful denial events without sensitive payloads.

## Automatic Failure Conditions

- A cross tenant actor can read an order.
- Support agents can read any order without an active linked case.
- Authorization happens only in frontend or only after full data serialization.
- Denial responses or logs expose order details.

## Reviewer Notes

Strong solutions make the policy independent from transport code while keeping
the endpoint behavior straightforward. Reward scoped repository queries and
tests that demonstrate data was not loaded unnecessarily for denied reads.
Review this API contract change:

The provider renames response field `account_status` to `lifecycle_status` in
`GET /accounts`. The provider unit tests pass, but no consumer pact, generated
client check, OpenAPI diff, mobile compatibility check, or migration window is
included. Existing consumers still read `account_status`.

Decide whether the change is acceptable and state the contract evidence required.

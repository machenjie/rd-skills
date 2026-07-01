Add a `SUSPENDED` status to the account enum and allow transitions from
`ACTIVE` and `PENDING`. The proposed patch updates the enum and one serializer
test but does not define allowed/forbidden transitions, rule authority,
protected invariants, failure signal, or validation map.


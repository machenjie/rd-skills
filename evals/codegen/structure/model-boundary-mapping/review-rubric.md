# Review Rubric

## Passing Standard

The solution passes when model boundaries are clear, mapping ownership is explicit, compatibility semantics are tested, and business rules remain outside accidental mapper code.

## Scoring

- 25 percent boundary separation: DTO, command, query, domain, value object, persistence, event, and view model roles are distinct where needed.
- 25 percent mapping semantics: null, default, optional, serialization, and validation ownership are preserved.
- 20 percent leakage prevention: ORM and generated models do not cross inappropriate boundaries.
- 20 percent compatibility testing: schema versioning and mapping tests cover old and new payloads.
- 10 percent simplicity: extra model classes are only introduced where boundary risk requires them.

## Automatic Failure Conditions

- API DTO is used as a domain object.
- ORM or persistence model is returned directly from API.
- Mapper owns business rules without being declared as a policy.
- Null, default, or optional semantics drift without tests.

## Reviewer Notes

Reward explicit assemblers and boundary-local generated models. Penalize blanket duplication that creates many identical models with no semantic boundary.

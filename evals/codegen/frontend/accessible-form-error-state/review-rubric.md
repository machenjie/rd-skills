# Review Rubric

## Passing Standard

The implementation must make validation errors understandable and accessible
without sacrificing backend validation or existing submit behavior. A reviewer
should be able to verify each state through tests or documented UI evidence.

## Scoring

- 30 percent accessibility for labels, descriptions, invalid state, focus, and announcements.
- 25 percent behavior for client validation, server mapping, value preservation, and loading state.
- 20 percent test quality for user level queries and failure states.
- 15 percent design consistency with existing form primitives and content patterns.
- 10 percent security and privacy for safe rendering and backend authority.

## Automatic Failure Conditions

- Errors are visible only by color or disconnected from their input.
- Server validation errors erase user input or are ignored.
- Raw server error HTML is rendered.
- Tests only inspect component internals and not user observable behavior.

## Reviewer Notes

Strong answers keep the component small by separating validation mapping from
rendering. Prefer tests that mirror keyboard and screen reader relevant user
flows over brittle snapshots.
# Test Suite

## Required Checks

- Empty required fields show field errors connected by accessible description.
- Invalid email format blocks submit and marks the email field invalid.
- Mismatched confirmation reports the correct field error.
- Server uniqueness error maps to the email field and preserves values.
- Unknown server error appears in a form summary and receives announcement or focus handling.

## Fixtures

- Successful email change response.
- Field level backend error for duplicate email.
- Form level backend error for recent password confirmation required.
- User event fixture for keyboard only interaction.

## Expected Commands

- `npm test -- EmailChangeForm`
- `npm run test:a11y -- EmailChangeForm`

## Regression Cases

- Existing happy path submit still calls the API with the same payload shape.
- Submit button disabled state prevents duplicate submissions while loading.
- Error elements remain stable across rerenders and do not create duplicate ids.
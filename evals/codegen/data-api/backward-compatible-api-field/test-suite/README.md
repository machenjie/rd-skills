# Test Suite

## Required Checks

- GET profile includes the new field for customers with a stored preference.
- GET profile returns a safe nullable value for existing customers without one.
- PATCH accepts email, phone, sms, and null according to the contract.
- PATCH rejects invalid values with existing validation error shape.
- Old client fixture omits the field and still passes contract tests.

## Fixtures

- Existing customer profile without preferred contact method.
- New customer profile with each allowed value.
- Old generated client fixture that ignores unknown response fields.
- Invalid PATCH payload with unsupported value.

## Expected Commands

- `npm test -- customerProfile`
- `npm run test:contract -- customer-profile`

## Regression Cases

- Name, email, phone, and marketing consent behavior remains unchanged.
- Response field ordering is stable where snapshots or docs depend on it.
- Documentation examples validate against the OpenAPI schema.
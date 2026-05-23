# Security Checks

## Threat Surface

Customer profile data includes identifiers, contact channels, and consent
signals. The primary risks are unsafe validation, overexposed contact data, and
contract changes that bypass existing authorization checks.

## Required Checks

- Preserve existing authentication and authorization checks for profile access.
- Validate enum values server side and reject unexpected strings.
- Do not expose contact preference for customers outside the caller scope.
- Avoid logging full profile payloads during validation errors.
- Confirm docs do not recommend client side only enforcement.

## Rejection Cases

- Any solution weakens profile authorization to add the field.
- Any solution accepts arbitrary strings for contact method.
- Any solution logs full profile payloads including email or phone by default.
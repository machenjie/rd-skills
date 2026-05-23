# Benchmark Prompt

## Task

Implement accessible validation and error states for the account email change
form. The starter component currently shows visual red text after submit but
does not connect errors to fields or announce failures to assistive technology.

## Context

Users enter a new email address and confirm it. The backend already validates
format, uniqueness, and recent password confirmation. The frontend must handle
client validation, server validation, loading, success, and retry states without
losing user input.

## Requirements

- Add client validation for required fields, email format, and matching confirmation.
- Associate each error with its input using accessible attributes.
- Move focus or announce submit level errors predictably after failed submit.
- Preserve entered values when server validation fails.
- Add tests for keyboard navigation, screen reader labels, and server error mapping.

## Constraints

- Do not replace backend validation with client only checks.
- Do not use color alone to communicate an error.
- Do not introduce a new design system component unless the existing primitives cannot express the state.

## Deliverables

- Updated form component, validation helper, and tests.
- State matrix covering empty, invalid, submitting, server rejected, success, and disabled states.
- Short note describing how backend errors map to fields or form summary.

## Completion Evidence

- Component tests proving fields expose accessible names and descriptions.
- Manual or automated accessibility evidence for error announcement behavior.
- Regression evidence that existing successful email change still works.
# Test Suite

## Required Checks

- `values.schema.json` rejects missing required values, wrong types, and unsafe defaults.
- Helm lint and template rendering are represented for each supported values file.
- Rendered manifests are validated before promotion.
- Atomic waited upgrade semantics and rollback boundaries are reviewable.

## Fixtures

- Fixture data for valid and invalid Helm values.
- Fixture data for rendered manifest validation.
- Fixture data for release notes, chart version, and `appVersion`.
- At least one denied or failure fixture that proves the implementation does not take a forbidden shortcut.

## Expected Commands

- `bash ../test-suite/run.sh`

## Regression Cases

- Reject shortcut: Keeping API tokens in values-prod.yaml.
- Reject shortcut: Skipping helm template validation.
- Reject shortcut: Using helm upgrade without atomic, wait, and timeout semantics.
- Existing successful behavior remains available after the new guard or compatibility path is added.

# Starter Repo

## Stack

TypeScript React frontend with feature folders, design-system primitives, and
component tests using accessible queries.

## Initial State

Security settings are implemented under `features/security-settings`. Existing
design primitives include `Banner`, `Button`, and `InlineAction`. Feature-local
state is used for settings-specific visibility. No shared recovery-code reminder
contract exists.

## Files

- `src/features/security-settings/SecuritySettingsPage.tsx` owns the settings page.
- `src/features/security-settings/hooks/useSecuritySettings.ts` owns feature data loading.
- `src/design-system/Banner.tsx` provides a generic banner primitive.
- `src/features/security-settings/__tests__/SecuritySettingsPage.test.tsx` covers current rendering.

## Constraints

Do not add security-specific behavior to `components/common` or global hooks.
Do not introduce a shared folder to avoid choosing the feature owner. Tests must
assert user-visible behavior.

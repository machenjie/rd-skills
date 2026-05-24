# Starter Repo

## Stack

TypeScript backend API with user controllers, profile service, serializers, and
unit tests for public endpoint behavior.

## Initial State

One endpoint dereferences `profile.name` when `profile` may be undefined. Similar
assumptions may appear in user export and notification preview paths. The
reported bug is narrow, but the defect pattern can recur elsewhere.

## Files

- `src/users/profileController.ts` handles the reported endpoint.
- `src/users/profileService.ts` loads optional profile data.
- `src/users/userSerializer.ts` formats user responses.
- `src/notifications/profilePreview.ts` builds profile preview copy.
- `src/users/__tests__/profileController.test.ts` covers endpoint behavior.

## Constraints

Do not bypass authorization checks or turn missing profile data into a silent
success for paths where absence is invalid. Keep tests at public behavior
boundaries rather than private helper assertions.
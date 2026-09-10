# Expected Route

## Path

One Task: inspect, edit, self-check, targeted validation, then done. The change
uses the existing form and API behavior. Local discovery stays with the Task;
no separate Analysis or independent Review is needed under the stated facts.

## Task Assignment

- Profile: `task-agent`
- Primary Professional Skill: `frontend-change-builder`
- Layer 3 Skills: `state-management-design`, `frontend-testing`
- Allowed scope: the billing form, its existing API/error adapter, and adjacent tests
- Verify: `npm test -- --runInBand src/billing/settings/__tests__/BillingSettingsForm.test.tsx`
  in the non-production test environment for dirty, submitting, failed, and
  successful states

If inspection reveals a changed public contract or unresolved interaction rule,
resolve that specific gap before the affected edit. Such evidence can change the
assignment; completing a local edit does not itself trigger another stage.

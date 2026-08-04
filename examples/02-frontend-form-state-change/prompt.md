# Prompt

The billing UI team owns the existing billing settings form, API/error adapter, and adjacent component tests. Update that existing placement so changing the billing contact shows unsaved state, disables save while submitting, and keeps server validation errors visible after a failed save. Run `npm test -- --runInBand src/billing/settings/__tests__/BillingSettingsForm.test.tsx` in the non-production test environment. The change is one-form reversible, does not alter consumers or public contracts, and stops if those facts or its material impact differ.

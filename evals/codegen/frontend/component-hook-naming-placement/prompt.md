# Benchmark Prompt

## Task

Add a security settings recovery-code reminder with a component and optional
hook. Decide names, placement, and state ownership before implementation.

## Context

The starter repo has `features/security-settings`, a design-system button and
banner primitive, and existing feature-local hooks. AI-generated code proposes
`components/common/FeatureCard.tsx`, `hooks/useFeature.ts`, props named `data`,
and a new `shared` folder for reminder state.

## Requirements

- Keep security-specific UI and state feature-local unless a stable shared contract exists.
- Reuse existing design primitives.
- Use names that express the security settings concept and rendered role.
- Keep hook and state scope narrow.
- Add tests for render, dismiss, and persistence behavior.

## Constraints

- Do not put security-specific copy, rules, or state in common components.
- Do not create generic hooks such as `useFeature`, `useData`, or `useThing`.
- Do not introduce global state for one feature.
- Do not rely on snapshot-only tests.

## Deliverables

- Feature-local component and hook or local state composition.
- Tests for user-visible reminder behavior.
- Implementation Structure Plan covering naming, taxonomy, placement, rejected shared alternatives, and test location.

## Completion Evidence

- Tests prove the reminder renders and can be dismissed.
- Review evidence shows feature-local versus shared placement was decided.
- Naming evidence shows component, hook, prop, file, and directory names follow local TypeScript conventions.

---
name: typescript-professional-usage
description: Use when writing or reviewing professional TypeScript for frontend, Node.js services, SDKs, or tooling with focus on strict typing, runtime validation, async errors, state modeling, API contracts, bundling, and safe escape hatches.
license: MIT
changeforge_kind: foundation-capability
changeforge_capability_id: "91"
changeforge_version: 0.1.0
---

# Mission

Enforce professional TypeScript usage for frontend (React / Vue / Svelte / SolidJS), Node.js services, SDKs, and tooling: strict typing, exhaustive narrowing, runtime validation at every boundary, async error discipline, public-type compatibility, bundle budgets, and accessibility. Reject `any`-typed escape hatches and the assumption that compile-time types protect runtime data.

# Pinned Tooling Baseline (TypeScript)

Pinned versions are review baselines, not permanent recommendations. If a pinned baseline is EOL, superseded, unsupported, or conflicts with the target project's approved platform policy, update this capability before relying on it for new product work.

- **TypeScript**: ≥ 5.4 (5.5+ preferred). `tsconfig.json` `"strict": true` + `"noUncheckedIndexedAccess": true` + `"noImplicitOverride": true` + `"exactOptionalPropertyTypes": true` + `"verbatimModuleSyntax": true`.
- **Node.js**: Node.js must be an active or maintenance LTS version. EOL Node versions are rejected. The target project must pin the exact supported major and update this capability when the organization’s Node.js LTS policy changes.
- **Package manager**: `pnpm` ≥ 9 (preferred for monorepos), `npm` ≥ 10, or `yarn` Berry. Lockfile mandatory; CI uses `--frozen-lockfile` / `npm ci`.
- **Linter**: `eslint` ≥ 9 (flat config) + `@typescript-eslint` v8 with `strict-type-checked` + `stylistic-type-checked` configs.
- **Formatter**: `prettier` ≥ 3.
- **Runtime validation**: `zod` ≥ 3.23 (preferred), `valibot` (smaller bundle), or `@sinclair/typebox`. Boundary schemas are the source of truth; inferred types drive code.
- **Test runner**: `vitest` ≥ 2 (preferred for Vite ecosystems) or `jest` ≥ 29 with `ts-jest`. Browser testing via `@testing-library/react|vue|svelte` + `playwright` for E2E.
- **Accessibility**: `axe-core` / `@axe-core/playwright` in CI for any user-facing UI.
- **Bundler**: `vite` ≥ 5 / `esbuild` / `rspack`; webpack 5 acceptable for legacy. Frontend bundle budgets enforced via `size-limit` or bundle analyzer in CI.
- **Security**: `npm audit --omit=dev` or `pnpm audit` or `osv-scanner` in CI.

# When To Use

Use when TypeScript code, public type definitions, frontend state, Node.js service logic, SDK contracts, build tooling, or API boundary validation is added or reviewed. Use whenever an external input (HTTP request, fetch response, localStorage, WebSocket message, postMessage, IPC) enters TypeScript code.

# Do Not Use When

Do not use to teach TypeScript syntax. Do not use to bless `any` as a shortcut. Do not use for raw JavaScript projects — require TypeScript migration first.

# Non-Negotiable Rules

- **`strict: true`** plus `noUncheckedIndexedAccess` mandatory. Any disable of strict flags requires inline justification + owner + expiration.
- **No `any` without inline justification.** Prefer `unknown` + narrowing or explicit schema. `@ts-ignore` / `@ts-expect-error` requires reason + owner + expiration; bare disables rejected.
- **External boundaries validated at runtime** with zod / valibot / typebox. Includes: HTTP request bodies, fetch / SDK responses, localStorage / sessionStorage / IndexedDB, WebSocket messages, postMessage, env vars (`process.env` typed as `Record<string, string | undefined>` and validated).
- **Backend models never reach the frontend untransformed.** A DTO layer (with its own zod schema) separates wire format from internal/DB model. ORM entities and Prisma types are not DTOs.
- **All Promises are handled.** No floating Promise (`@typescript-eslint/no-floating-promises`). Top-level awaits handle rejection; `unhandledrejection` listener registered in apps.
- **Discriminated unions for state.** Loading/success/error states modeled as a discriminant tag union, not three booleans.
- **Public SDK types are stable.** Breaking changes require major version bump; changes verified with `@arethetypeswrong/cli` and `api-extractor` / `tsd` snapshot tests.
- **Bundle budgets enforced for frontend.** LCP / INP / CLS targets defined; `size-limit` in CI fails the build on budget breach.
- **Accessibility**: WCAG 2.2 AA target; axe rules in CI; keyboard-only navigation tested; focus-visible / aria-* attributes correct.
- **No `require()` in TS files**; ESM only for new code (`"type": "module"` + `"moduleResolution": "bundler"` or `"nodenext"`).

# Industry Benchmarks

- **TypeScript Handbook** + **Matt Pocock / Total TypeScript** patterns for advanced types.
- **Effective TypeScript** (Vanderkam) for boundary modeling.
- **TC39 proposals** at stage ≥ 3 for forward-compat (e.g., `using` for explicit resource management, decorators stage 3).
- **WCAG 2.2** for accessibility; **Lighthouse CI** with Core Web Vitals (LCP < 2.5s, INP < 200ms, CLS < 0.1).
- **OWASP Top 10 (web)** — XSS, CSRF, SSRF, deserialization, injection mappings to TypeScript idioms (DOMPurify for HTML rendering; never `dangerouslySetInnerHTML` without sanitization; `URL` parsing not regex).
- **Semantic Versioning** + **api-extractor** for SDK compatibility.
- **`@typescript-eslint` strict-type-checked** as the floor for service/SDK code.

# Selection Rules

Select when TypeScript, frontend state, Node.js services, SDKs, generated types, bundling, or public API types appear. Pair with `frontend-change-builder`, `data-api-contract-changer` (for public APIs), `language-idiom-enforcement`, `language-testing-strategy`, `package-dependency-management`.

# Risk Escalation Rules

- Escalate to `data-api-contract-changer` for public API / SDK contract changes.
- Escalate to `frontend-change-builder` for UI state, bundle, Core Web Vitals impact.
- Escalate to `quality-test-gate` for behavior + accessibility test evidence.
- Escalate to `package-dependency-management` for npm/pnpm dep additions, audit, supply-chain (postinstall scripts).
- Escalate to `security-privacy-gate` for XSS / CSRF / `dangerouslySetInnerHTML` / `eval` / Function constructor / prototype pollution / unsafe deserialization.
- Escalate to `language-performance-safety` for Node.js event-loop blocking, memory leak via closure capture, large allocation.

# Critical Details

- **`unknown` over `any`**: `unknown` requires narrowing before use; `any` opts out of all checks and silently propagates.
- **`noUncheckedIndexedAccess`** makes `arr[0]` typed as `T | undefined` — forces null/undefined check before use. Catches a large class of runtime bugs.
- **`exhaustive switch` via `never`**: `function assertNever(x: never): never { throw new Error(...) }`; place in `default:` of switch over discriminated union. Adding a new variant becomes a compile error.
- **`as` casts are escape hatches.** Each `as` requires justification; prefer `satisfies` to narrow without lying about types.
- **`zod.parse` vs `zod.safeParse`**: `parse` throws; `safeParse` returns discriminated result. Boundary code prefers `safeParse` + explicit error response.
- **DOM XSS**: `innerHTML` / `dangerouslySetInnerHTML` / `v-html` accept attacker-controlled HTML by default. Use `DOMPurify` if HTML must be rendered; prefer text + structured components.
- **`new Function(str)` / `eval(str)` / template engines with unsafe expressions** are RCE primitives in Node. Reject in code review.
- **Prototype pollution**: `Object.assign({}, JSON.parse(body))` is unsafe if body contains `__proto__` / `constructor.prototype`. Use schema validation; `Object.create(null)` for maps.
- **Floating promise**: `myAsync()` without `await` / `.catch()` swallows rejection. `@typescript-eslint/no-floating-promises` mandatory.
- **`fetch` does not reject on HTTP error status** (4xx / 5xx). Always check `res.ok`.
- **Closure memory leaks** in React: event handler captures stale state via closure; `useEffect` cleanup omitted; subscriptions not unsubscribed. Detection: `eslint-plugin-react-hooks` exhaustive-deps + memory profile.
- **`process.env` is `string | undefined`**: validate at startup; never `process.env.FOO!` (non-null assertion hides missing env).
- **Tree-shaking** requires ESM, `sideEffects: false` in package.json where true, and named exports. CommonJS / default-export-of-object defeats tree-shaking.
- **React Server Components / Suspense / streaming**: boundary between server and client code must be explicit (`"use client"` / `"use server"`).

# Failure Modes

- **Trusted `any` at boundary** — Symptom: production crash on malformed JSON. Cause: type annotation assumed at fetch / req body. Detection: zod at every boundary. Impact: outage on hostile input.
- **Backend model leaks to frontend** — Symptom: frontend breaks on backend DB schema change; PII exposed in DOM. Cause: ORM entity serialized directly to JSON response. Detection: DTO layer with own schema. Impact: contract churn, privacy incident.
- **Floating promise** — Symptom: silent failure; unhandled rejection logged but feature broken. Cause: missing `await`. Detection: `no-floating-promises` lint. Impact: invisible bug.
- **`dangerouslySetInnerHTML` XSS** — Symptom: stored XSS via comment field. Cause: HTML rendered without sanitization. Detection: lint + code review. Impact: account takeover.
- **`as any` escape** — Symptom: type errors disappear locally; production breaks. Cause: cast silenced real type mismatch. Detection: ban `as any` via eslint. Impact: hidden type drift.
- **Bundle bloat** — Symptom: Lighthouse LCP regression after merge. Cause: imported large library default; CJS package defeats tree-shaking. Detection: `size-limit` in CI. Impact: Core Web Vitals breach.
- **`process.env.X!`** — Symptom: runtime undefined-deref. Cause: non-null assertion on env without validation. Detection: env schema at startup. Impact: crash at first request.
- **Stale closure in React** — Symptom: handler uses old state value. Cause: missing dependency in `useEffect` / `useCallback`. Detection: `react-hooks/exhaustive-deps`. Impact: subtle UX bugs.
- **Public SDK type break** — Symptom: downstream TS consumers can't compile after minor bump. Cause: type widened/narrowed without major bump. Detection: `api-extractor` + `tsd` snapshot in CI. Impact: ecosystem breakage.
- **`fetch` ignored status** — Symptom: error response parsed as success body. Cause: missing `res.ok` check. Detection: code review + helper wrapper. Impact: silent failure modes.

# Output Contract

Return a **TypeScript Usage Review** containing:
- **TS / Node versions** and `tsconfig` strictness flags status
- **Tooling pins**: eslint + plugins, prettier, zod / valibot, test runner versions
- **`any` / `as` / `@ts-ignore` audit** — each justified with owner + expiration
- **Boundary validation coverage** — every external input has a runtime schema
- **DTO layer** — frontend / SDK types decoupled from backend models
- **Promise handling** — `no-floating-promises` clean; `unhandledrejection` listener
- **State modeling** — discriminated unions; exhaustive switches with `assertNever`
- **Bundle budget** (frontend) — `size-limit` config and CI status; Core Web Vitals targets
- **Accessibility** — axe CI status; WCAG 2.2 AA verdict; keyboard nav verified
- **Public SDK compatibility** — api-extractor + tsd snapshot status; semver verdict
- **Security** — XSS / prototype-pollution / `eval` / unsafe deserialization audited
- **Tests** — vitest/jest coverage; testing-library behavior + axe; Playwright E2E for critical flows
- **Accepted exceptions** with owner / scope / expiration

# Quality Gate

1. TS ≥ 5.4 with `strict` + `noUncheckedIndexedAccess`; Node ≥ 20 LTS.
2. `eslint` (strict-type-checked) + `prettier --check` green in CI; no bare `any` or `@ts-ignore` without justification.
3. Every external input has a runtime schema (`zod.safeParse` or equivalent).
4. DTO layer separates frontend / SDK types from backend models.
5. `@typescript-eslint/no-floating-promises` green; `unhandledrejection` listener present in apps.
6. Bundle budget defined and met in CI (`size-limit`); Lighthouse LCP / INP / CLS within target.
7. Accessibility: axe CI green; WCAG 2.2 AA verified for user-facing changes.
8. Public SDK: api-extractor / tsd snapshot reviewed; semver-correct bump.
9. Security: no `dangerouslySetInnerHTML` without sanitization; no `eval` / `new Function`; npm/pnpm audit green or triaged.
10. Tests cover behavior (not only snapshot); critical flows have Playwright E2E.

# Used By

frontend-change-builder, backend-change-builder, data-api-contract-changer, sdk-library-contract-design, quality-test-gate, ai-code-review-refactor, language-runtime-selection

# Handoff

- **`data-api-contract-changer`** for public API / SDK contract changes.
- **`frontend-change-builder`** for UI state, bundle, Web Vitals.
- **`package-dependency-management`** for dep / supply-chain.
- **`security-privacy-gate`** for XSS / injection / unsafe deserialization.
- **`quality-test-gate`** for behavior + accessibility evidence.
- **`language-performance-safety`** for Node.js event-loop / memory.

# Completion Criteria

Review is complete when: strict TS + lint + format are green; every boundary is validated at runtime; DTO layer is enforced; no floating promises; bundle / WCAG budgets met; public SDK compatibility verified; security audit clean; tests cover behavior + accessibility + E2E for critical flows; and any escape hatch has owner, scope, and expiration.

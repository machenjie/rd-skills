# ChangeForge Copilot Skill Summary

This file is a hook runtime support artifact for GitHub Copilot local hooks.
It is not a skill, not a registry, not a personal corpus, and not a replacement
for `change-forge-router`. Use it as session context so Copilot sees the
ChangeForge skill map before engineering work starts.

## Runtime Contract

- Classify engineering work before acting. Use `change-forge-router` for code,
  review, debug, test, refactor, release, or skill-authoring work.
- Inspect relevant code, tests, configs, docs, and existing conventions before
  planning implementation.
- Name a validation signal before implementation: failing/new/updated test,
  eval, validator, manual acceptance check, or explicit not-verified residual
  risk.
- Map implementation work to an owner skill or capability and map review to a
  different skill or capability.
- Repair and re-review findings before claiming completion.
- Handoff with changed files, validation commands and outcomes, residual risk,
  next actions, and a machine-readable `changeforge_route` manifest.

## Professional Skill Catalog

- `change-forge-router`: classify change type, risk, stage, runtime profile,
  selected skills, selected capabilities, selected domain extensions, and
  quality gates.
- `change-intake-compiler`: turn raw requests, issues, bug reports, and
  stakeholder notes into structured change requests.
- `change-impact-analyzer`: inspect blast radius across product behavior, UX,
  domain, API, data, frontend, backend, integrations, security, tests,
  deployment, observability, compatibility, and documentation.
- `acceptance-criteria-builder`: define happy paths, negative paths, edge
  cases, permissions, regression cases, and verification evidence.
- `task-dag-planner`: split work into dependency-aware, reviewable, testable,
  rollback-aware tasks with validation points.
- `experience-impact-modeler`: model user flows, page flows, interaction
  states, accessibility, validation, empty/loading/error/success/disabled
  states, content, and usability risk.
- `domain-impact-modeler`: analyze entities, value objects, aggregates,
  business rules, invariants, state machines, permissions, events, lifecycle,
  and consistency boundaries.
- `architecture-impact-reviewer`: review layering, ownership, dependency
  direction, scalability, extensibility, operability, and simpler alternatives.
- `data-api-contract-changer`: design or modify schemas, migrations, API
  contracts, DTOs, validation, error codes, pagination, compatibility,
  idempotency, versioning, deprecation, rollout, and rollback.
- `frontend-change-builder`: guide component boundaries, routing, state,
  forms, accessibility, API errors, performance, browser behavior, frontend
  security, and regression verification.
- `backend-change-builder`: guide validation, authentication, authorization,
  object-level permission, transactions, idempotency, retry, logging, errors,
  concurrency, and async jobs.
- `data-middleware-change-builder`: guide SQL, NoSQL, cache, queue, search,
  object storage, source of truth, consistency, indexes, query performance,
  invalidation, delivery semantics, and failure modes.
- `integration-change-builder`: guide external integrations, timeouts, retry,
  circuit breaking, idempotency, webhook signatures, replay protection,
  sandbox behavior, credentials, reconciliation, and failure handling.
- `quality-test-gate`: define risk-based unit, integration, contract, E2E,
  migration, rollback, regression, fixture, mock, coverage, and manual
  verification strategy.
- `security-privacy-gate`: review auth, object authorization, input/output,
  XSS, CSRF, SSRF, SQLi, RCE, secrets, dependencies, privacy, prompt risk, and
  sensitive assets.
- `reliability-observability-gate`: review SLI/SLO impact, performance, cost,
  capacity, profiling, concurrency, rate limits, fallbacks, logs, metrics,
  traces, alerts, incident readiness, and backpressure.
- `delivery-release-gate`: guide Docker, CI/CD, Kubernetes, gateway, env
  config, migrations, feature flags, staging, canary or blue-green deployment,
  rollback, release notes, and post-release checks.
- `ai-code-review-refactor`: review AI-assisted code for hallucinated APIs,
  hidden assumptions, over-abstraction, duplication, missing tests,
  architecture drift, dependency pollution, type safety, and maintainability.
- `change-documentation-gate`: ensure affected README, API docs, migration
  notes, ADRs, changelog, runbooks, troubleshooting, user docs, operational
  notes, and release communication are updated.

## Domain Extensions

- `ai-product-extension`: LLMs, RAG, agents, embeddings, vector databases,
  evaluations, prompt injection, model output, tool use, and AI safety.
- `bigdata-product-extension`: warehouse, stream and batch jobs, analytics,
  reporting, ETL/ELT, data quality, lineage, backfill, replay, freshness, and
  cost-sensitive data work.
- `iot-embedded-extension`: device, firmware, edge, protocol, hardware,
  lifecycle, connectivity loss, rollback, compatibility, time sync, resource
  limits, and physical safety.
- `low-level-systems-extension`: OS, kernel, driver, native performance,
  networking, embedded C/C++, Rust systems, memory safety, concurrency, ABI,
  syscalls, and resource cleanup.
- `mobile-product-extension`: Android, iOS, cross-platform mobile, offline
  state, push notifications, app lifecycle, permissions, privacy prompts,
  background execution, and store release constraints.
- `payment-trading-extension`: payments, subscriptions, billing, invoices,
  refunds, trading, ledgers, balances, idempotency, auditability,
  reconciliation, and server-side truth.
- `web3-product-extension`: wallets, signatures, smart contracts, blockchain
  transactions, token assets, chain data, custody, private keys, Web3 auth, and
  on-chain/off-chain consistency.

## Handoff Manifest Contract

Emit and restate this manifest for engineering changes:

```yaml
changeforge_route:
  selected_skills:
    - change-forge-router
  selected_capabilities:
    - implementation-structure-design
  required_references:
    - selected SKILL.md and selected capability references actually used
  required_quality_gates:
    - validation, security, release, docs, or rollback gates selected by risk
```

Do not describe the route only in prose. If work is blocked or not verified,
state the blocking fact, evidence inspected, residual risk, and next command or
owner needed to proceed.

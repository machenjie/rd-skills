# Activation Precision Evaluation

This generated report uses deterministic route activation fixtures. It measures resolver precision/recall for staged loading decisions; it is not live runtime pass-rate evidence.

## Summary

- Status: `pass`
- Mode: `built`
- Runtime root: `dist/codex/project/.codex/hooks`
- Cases: 24
- Passed: 24
- Failed: 0

| Metric | Value |
| --- | --- |
| `stage_accuracy` | `1.0` |
| `skill_precision` | `1.0` |
| `skill_recall` | `1.0` |
| `capability_precision` | `1.0` |
| `capability_recall` | `1.0` |
| `reference_precision` | `1.0` |
| `reference_recall` | `1.0` |
| `language_fp_rate` | `0.0` |
| `language_fn_rate` | `0.0` |
| `risk_surface_fp_rate` | `0.0` |
| `risk_surface_fn_rate` | `0.0` |
| `overroute_rate` | `0.0` |

## Cases

| Case | Status | Stage | Product Surfaces | Languages | Risks |
| --- | --- | --- | --- | --- | --- |
| `backend-conditional-planning` | `pass` | `implementation-planning` | backend-product | python | none |
| `frontend-tsx-no-backend` | `pass` | `implementation-planning` | frontend-product | typescript | none |
| `webhook-review-no-web3` | `pass` | `code-review` | external-integration, webhook | python | none |
| `backend-security-risk` | `pass` | `implementation-planning` | backend-product | python | security |
| `docs-release-handoff` | `pass` | `documentation-handoff` | documentation-only | none | delivery, documentation |
| `web3-wallet-no-webhook` | `pass` | `implementation-planning` | web3 | none | none |
| `frontend-ui-state-does-not-trigger-agent-workflow` | `pass` | `implementation-planning` | frontend-product | typescript | none |
| `docs-api-mention-does-not-trigger-api-implementation` | `pass` | `documentation-handoff` | documentation-only | none | data-api, documentation |
| `business-registry-does-not-trigger-skill-authoring` | `pass` | `implementation-planning` | backend-product, cache, sdk-library | none | none |
| `sql-migration-distinct-from-query` | `pass` | `implementation-planning` | database-migration | sql | data-api, delivery |
| `sql-query-does-not-trigger-migration` | `pass` | `implementation-planning` | none | sql | data-api |
| `c-header-routes-cpp-only` | `pass` | `refactoring` | none | cpp | none |
| `react-ts-frontend-not-node-backend` | `pass` | `implementation-planning` | frontend-product | typescript | none |
| `node-ts-backend-not-react-frontend` | `pass` | `implementation-planning` | backend-product | typescript | none |
| `redis-cache-does-not-trigger-queue` | `pass` | `implementation-planning` | cache | python | none |
| `kafka-queue-does-not-trigger-cache` | `pass` | `implementation-planning` | message-queue | python | none |
| `web3-signature-does-not-trigger-webhook` | `pass` | `implementation-planning` | web3 | none | none |
| `webhook-signature-does-not-trigger-web3` | `pass` | `code-review` | webhook | none | none |
| `docs-release-words-not-deployment-config` | `pass` | `documentation-handoff` | documentation-only | none | delivery, documentation |
| `deployment-config-triggers-release` | `pass` | `release-delivery` | infrastructure-deployment, kubernetes-helm | none | delivery |
| `refactor-stage-does-not-load-planning-conditional` | `pass` | `refactoring` | backend-product | python | none |
| `review-stage-uses-review-conditionals-only` | `pass` | `code-review` | backend-product | python | none |
| `test-stage-loads-validation-broker-not-implementation-structure` | `pass` | `testing` | backend-product, validation-broker | python | none |
| `repair-stage-loads-workflow-not-planning-conditionals` | `pass` | `code-review` | backend-product, execution-trajectory | python | none |

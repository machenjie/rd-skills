# Hookless Professional Routing Coverage

> Fresh deterministic actual-route coverage only; no live precision, recall, latency, or adoption claim is made.

- Routing evidence: `eval-routing.evaluate_routes actual`
- Routing cases: 233
- Professional Skills: 26
- Layer 3 Skills: 163
- Errors: 0

| Professional Skill | Profiles | Task routable | Primary cases | Review cases | Negative cases |
|---|---|---|---:|---:|---:|
| `acceptance-criteria-builder` | analysis-agent | true | 1 | 0 | 0 |
| `ai-code-review-refactor` | review-agent | true | 14 | 82 | 0 |
| `architecture-impact-reviewer` | analysis-agent, review-agent | true | 5 | 98 | 1 |
| `backend-change-builder` | task-agent | true | 26 | 0 | 0 |
| `change-documentation-gate` | task-agent, review-agent | true | 4 | 4 | 0 |
| `change-intake-compiler` | analysis-agent | true | 1 | 0 | 0 |
| `data-api-contract-changer` | analysis-agent, task-agent | true | 4 | 0 | 0 |
| `data-middleware-change-builder` | analysis-agent, task-agent | true | 7 | 0 | 0 |
| `delivery-release-gate` | analysis-agent, task-agent, review-agent | true | 5 | 7 | 0 |
| `domain-impact-modeler` | analysis-agent | true | 3 | 0 | 0 |
| `engineering-artifact-review` | review-agent | true | 1 | 2 | 0 |
| `engineering-change-analysis` | analysis-agent | true | 103 | 0 | 0 |
| `experience-impact-modeler` | analysis-agent | true | 3 | 0 | 0 |
| `frontend-change-builder` | task-agent | true | 10 | 0 | 0 |
| `high-risk-design-review` | review-agent | true | 2 | 3 | 0 |
| `incident-response-coordinator` | analysis-agent | true | 1 | 0 | 1 |
| `installed-client-change-builder` | task-agent | true | 9 | 0 | 0 |
| `integration-change-builder` | analysis-agent, task-agent | true | 3 | 0 | 0 |
| `logging-design-gate` | task-agent, review-agent | true | 5 | 7 | 1 |
| `platform-infrastructure-change-builder` | task-agent | true | 3 | 0 | 0 |
| `quality-test-gate` | analysis-agent, task-agent, review-agent | true | 2 | 4 | 0 |
| `reliability-observability-gate` | analysis-agent, task-agent, review-agent | true | 5 | 9 | 5 |
| `repository-tooling-change-builder` | task-agent | true | 8 | 0 | 1 |
| `routing-quality-review` | review-agent | false | 0 | 0 | 0 |
| `security-privacy-gate` | analysis-agent, task-agent, review-agent | true | 7 | 17 | 8 |
| `task-dag-planner` | analysis-agent | true | 1 | 0 | 0 |

## Domain Family Coverage

| Domain | Family | Canonical actual cases | Paraphrase actual cases |
|---|---|---|---|
| `ai-product-extension` | `agent-model-authority` | ai-agent-tool-authority | ai-model-decision-paraphrase |
| `ai-product-extension` | `retrieval-data` | ai-rag-tool-authority | ai-rag-http-contrast-clause, ai-retrieval-permission-paraphrase |
| `android-platform-extension` | `accessibility-platform-authority` | android-accessibility-platform-authority | android-accessibility-compose-focus-paraphrase |
| `android-platform-extension` | `platform-lifecycle-authority` | mobile-native-lifecycle-permission | mobile-android-permission-paraphrase |
| `bigdata-product-extension` | `distributed-batch-schema` | bigdata-distributed-backfill-schema | bigdata-lake-reprocessing-paraphrase |
| `bigdata-product-extension` | `stream-cdc-replay` | bigdata-cdc-stream-replay | bigdata-stream-checkpoint-paraphrase |
| `cloud-platform-extension` | `cloud-account-authority` | structure-owner-internal-backend-placement | structure-real-pattern-force |
| `cross-platform-client-extension` | `shared-target-ownership` | unknown-owner | source-backed-question |
| `ios-ipados-platform-extension` | `platform-lifecycle-authority` | mobile-offline-deeplink | mobile-store-upgrade-paraphrase |
| `iot-embedded-extension` | `device-physical-runtime` | iot-device-physical-runtime | iot-edge-provisioning-paraphrase |
| `iot-embedded-extension` | `firmware-update-recovery` | iot-firmware-actuator-rollout | iot-firmware-brownout-paraphrase |
| `linux-desktop-platform-extension` | `desktop-session-authority` | multi-task-plan | structure-unresolved-placement-is-not-refactoring |
| `low-level-systems-extension` | `abi-ffi-memory` | low-level-ffi-ownership | low-level-native-memory-paraphrase |
| `low-level-systems-extension` | `kernel-realtime-concurrency` | low-level-kernel-driver | low-level-realtime-paraphrase |
| `macos-platform-extension` | `platform-lifecycle-authority` | structure-generated-authority-unknown | structure-fixed-placement-refactor-analysis |
| `payment-trading-extension` | `money-ledger-settlement` | payment-security | payment-ledger-settlement-paraphrase, payment-wallet-custody-accounting-conflict |
| `payment-trading-extension` | `trading-order-execution` | payment-trading-execution | payment-venue-order-paraphrase |
| `web3-product-extension` | `chain-custody-finality` | web3-chain-custody-finality | web3-wallet-signing-paraphrase |
| `web3-product-extension` | `contract-cross-chain` | web3-chain-contract-finality | web3-bridge-proof-paraphrase |
| `windows-platform-extension` | `application-identity-authority` | structure-minimal-backend | structure-object-classification-method-placement |
| `windows-platform-extension` | `service-lifecycle-authority` | structure-ef-mapping-domain-facts-unchanged | structure-deliberate-separate-owner-implementations |

## Domain Transition and Unchanged Controls

| Domain | Transition actual cases | Unchanged excluded cases |
|---|---|---|
| `ai-product-extension` | ai-transition-search-to-prompt-context | ai-anti-unchanged-rag-documentation |
| `android-platform-extension` | mobile-transition-pwa-to-native-lifecycle | mobile-anti-responsive-pwa |
| `bigdata-product-extension` | bigdata-transition-table-to-distributed-batch | bigdata-anti-unchanged-pipeline-documentation |
| `cloud-platform-extension` | structure-owner-internal-backend-placement | platform-infrastructure-direct |
| `cross-platform-client-extension` | unknown-owner | frontend-direct |
| `ios-ipados-platform-extension` | mobile-offline-deeplink | mobile-anti-unchanged-permission-help |
| `iot-embedded-extension` | iot-transition-cloud-api-to-device-protocol | iot-anti-unchanged-protocol-documentation |
| `linux-desktop-platform-extension` | multi-task-plan | documentation |
| `low-level-systems-extension` | low-level-transition-rust-to-os-resource | low-level-anti-unchanged-ffi-documentation |
| `macos-platform-extension` | structure-generated-authority-unknown | logging |
| `payment-trading-extension` | payment-transition-price-display-to-wallet-ledger | payment-anti-order-display-unchanged-state, payment-anti-unchanged-wallet-copy |
| `web3-product-extension` | web3-transition-api-signature-to-chain-custody | web3-anti-unchanged-wallet-documentation |
| `windows-platform-extension` | structure-object-classification-method-placement | validation |

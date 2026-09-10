# Hookless Routing Evaluation

- Cases: 233
- Passed: 233
- Evidence scope: `deterministic-fixtures`
- Explicit negative-route cases: 69
- Domain family cases: 44
- Domain anti-route cases: 26
- Domain transition cases: 13
- Domain unchanged-paraphrase controls: 14
- Maximum Layer 3 Skills in one route: 3
- Decision axes: 7
- Controlled Decision mutants: 9
- Compatibility baseline: 233+62
- Targeted boundary relations: 8/8

| Case | Domain family | Path | Profile | Primary | Layer 3 | Review | Excluded | Pass |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ambiguous-request | - | analyzed | analysis-agent | change-intake-compiler | requirement-clarification | ai-code-review-refactor | - | True |
| acceptance-gap | - | analyzed | analysis-agent | acceptance-criteria-builder | acceptance-standard-definition | ai-code-review-refactor | - | True |
| unknown-owner | cross-platform-client-extension:shared-target-ownership:canonical | analyzed | analysis-agent | engineering-change-analysis | cross-platform-client-extension, android-platform-extension, repository-context-map | architecture-impact-reviewer | - | True |
| source-backed-question | cross-platform-client-extension:shared-target-ownership:paraphrase | analyzed | analysis-agent | engineering-change-analysis | cross-platform-client-extension, ios-ipados-platform-extension, repository-context-map | architecture-impact-reviewer | - | True |
| failure-diagnosis | - | analyzed | analysis-agent | engineering-change-analysis | failure-diagnosis | reliability-observability-gate | - | True |
| multi-task-plan | linux-desktop-platform-extension:desktop-session-authority:canonical | analyzed | analysis-agent | engineering-change-analysis | linux-desktop-platform-extension | ai-code-review-refactor | - | True |
| accepted-brief-task-dag | - | analyzed | analysis-agent | task-dag-planner | task-dag-decomposition | engineering-artifact-review | - | True |
| high-risk-multi-task | - | analyzed | analysis-agent | engineering-change-analysis | release-rollback | high-risk-design-review | - | True |
| domain-invariant | - | analyzed | analysis-agent | domain-impact-modeler | business-rule-extraction, state-machine-modeling | architecture-impact-reviewer | - | True |
| architecture-boundary | - | analyzed | analysis-agent | architecture-impact-reviewer | implementation-structure-design | architecture-impact-reviewer | - | True |
| structure-owner-internal-backend-placement | cloud-platform-extension:cloud-account-authority:canonical | analyzed | analysis-agent | engineering-change-analysis | cloud-platform-extension, repository-context-map | architecture-impact-reviewer | module-boundary-design, api-contract-design | True |
| structure-known-generator-authority-placement | - | direct | task-agent | repository-tooling-change-builder | build-tool-professional-usage, targeted-validation-selection | ai-code-review-refactor | - | True |
| structure-owner-private-business-predicate-not-placement | - | direct | task-agent | backend-change-builder | - | ai-code-review-refactor | implementation-structure-design | True |
| structure-relative-business-method-homonym-not-placement | - | direct | task-agent | backend-change-builder | - | ai-code-review-refactor | implementation-structure-design | True |
| structure-named-generic-anaphora-ambiguous | - | analyzed | analysis-agent | engineering-change-analysis | repository-context-map | architecture-impact-reviewer | - | True |
| structure-passive-private-helper-move-not-request | - | analyzed | analysis-agent | engineering-change-analysis | repository-context-map | architecture-impact-reviewer | - | True |
| structure-fixed-helper-placement-declaration-not-request | - | analyzed | analysis-agent | engineering-change-analysis | repository-context-map | architecture-impact-reviewer | - | True |
| structure-owner-private-runtime-selection-not-placement | - | direct | task-agent | backend-change-builder | - | ai-code-review-refactor | implementation-structure-design | True |
| structure-put-selected-file-placement | - | direct | task-agent | backend-change-builder | implementation-structure-design | ai-code-review-refactor | - | True |
| structure-move-selected-file-placement | - | direct | task-agent | backend-change-builder | implementation-structure-design | ai-code-review-refactor | - | True |
| structure-placement-within-selected-destination | - | direct | task-agent | backend-change-builder | implementation-structure-design | ai-code-review-refactor | - | True |
| structure-tooling-within-selected-destination | - | direct | task-agent | repository-tooling-change-builder | build-tool-professional-usage, implementation-structure-design, targeted-validation-selection | ai-code-review-refactor | - | True |
| structure-placement-incompatible-destinations | - | analyzed | analysis-agent | engineering-change-analysis | repository-context-map | architecture-impact-reviewer | - | True |
| structure-placement-multiple-anaphora | - | analyzed | analysis-agent | engineering-change-analysis | repository-context-map | architecture-impact-reviewer | - | True |
| structure-actual-diff-private-move | - | direct | review-agent | ai-code-review-refactor | implementation-structure-design, refactoring | ai-code-review-refactor | - | True |
| structure-domain-object-classification | - | analyzed | analysis-agent | domain-impact-modeler | domain-object-identification | architecture-impact-reviewer | - | True |
| structure-real-pattern-force | cloud-platform-extension:cloud-account-authority:paraphrase | direct | task-agent | backend-change-builder | cloud-platform-extension, design-pattern-selection, concurrency-control | ai-code-review-refactor | - | True |
| structure-pattern-analysis | - | analyzed | analysis-agent | architecture-impact-reviewer | design-pattern-selection | architecture-impact-reviewer | - | True |
| structure-known-generator-pattern | - | direct | task-agent | repository-tooling-change-builder | build-tool-professional-usage, design-pattern-selection, targeted-validation-selection | ai-code-review-refactor | - | True |
| structure-actual-diff-pattern | - | direct | review-agent | ai-code-review-refactor | design-pattern-selection | ai-code-review-refactor | - | True |
| structure-actual-diff-domain-object | - | direct | review-agent | ai-code-review-refactor | domain-object-identification | ai-code-review-refactor | - | True |
| structure-minimal-delete-list | - | direct | review-agent | ai-code-review-refactor | minimal-correct-implementation | ai-code-review-refactor | - | True |
| structure-minimal-analysis | - | analyzed | analysis-agent | engineering-change-analysis | minimal-correct-implementation | architecture-impact-reviewer | - | True |
| structure-minimal-backend | windows-platform-extension:application-identity-authority:canonical | analyzed | analysis-agent | engineering-change-analysis | windows-platform-extension, minimal-correct-implementation | architecture-impact-reviewer | - | True |
| structure-minimal-generator | - | direct | task-agent | repository-tooling-change-builder | build-tool-professional-usage, minimal-correct-implementation, targeted-validation-selection | ai-code-review-refactor | - | True |
| structure-object-classification-method-placement | windows-platform-extension:application-identity-authority:paraphrase | analyzed | analysis-agent | domain-impact-modeler | windows-platform-extension, domain-object-identification | architecture-impact-reviewer | - | True |
| structure-ef-mapping-domain-facts-unchanged | windows-platform-extension:service-lifecycle-authority:canonical | direct | task-agent | backend-change-builder | windows-platform-extension | ai-code-review-refactor | domain-object-identification | True |
| structure-deliberate-separate-owner-implementations | windows-platform-extension:service-lifecycle-authority:paraphrase | direct | task-agent | backend-change-builder | windows-platform-extension, implementation-structure-design | ai-code-review-refactor | module-boundary-design | True |
| structure-generated-authority-unknown | macos-platform-extension:platform-lifecycle-authority:canonical | analyzed | analysis-agent | engineering-change-analysis | macos-platform-extension, repository-context-map | architecture-impact-reviewer | implementation-structure-design | True |
| structure-cross-module-public-edge | - | analyzed | analysis-agent | architecture-impact-reviewer | module-boundary-design | architecture-impact-reviewer | implementation-structure-design | True |
| structure-fixed-placement-refactor | - | direct | review-agent | ai-code-review-refactor | refactoring | ai-code-review-refactor | implementation-structure-design | True |
| structure-fixed-placement-refactor-analysis | macos-platform-extension:platform-lifecycle-authority:paraphrase | analyzed | analysis-agent | engineering-change-analysis | macos-platform-extension, refactoring | architecture-impact-reviewer | implementation-structure-design | True |
| structure-unresolved-placement-is-not-refactoring | linux-desktop-platform-extension:desktop-session-authority:paraphrase | analyzed | analysis-agent | engineering-change-analysis | linux-desktop-platform-extension, repository-context-map | architecture-impact-reviewer | refactoring | True |
| structure-guard-naming-only | - | direct | review-agent | ai-code-review-refactor | code-clarity-maintainability | ai-code-review-refactor | implementation-structure-design, module-boundary-design, refactoring | True |
| structure-dto-table-ui-not-domain | - | analyzed | analysis-agent | data-api-contract-changer | model-boundary-mapping | architecture-impact-reviewer | domain-object-identification | True |
| structure-pattern-word-comment-only | - | direct | task-agent | change-documentation-gate | documentation-generation | change-documentation-gate | design-pattern-selection | True |
| structure-documentation-only-module-wording | - | direct | task-agent | change-documentation-gate | documentation-generation | change-documentation-gate | module-boundary-design | True |
| structure-documentation-with-runtime-architecture-change | - | analyzed | analysis-agent | architecture-impact-reviewer | module-boundary-design | architecture-impact-reviewer | documentation-generation | True |
| structure-module-api-explicitly-unchanged | - | analyzed | analysis-agent | engineering-change-analysis | repository-context-map | architecture-impact-reviewer | module-boundary-design, api-contract-design | True |
| structure-filesystem-safety-not-placement | - | direct | task-agent | backend-change-builder | filesystem-process-safety | ai-code-review-refactor | implementation-structure-design | True |
| structure-sdk-contract-not-reuse | - | analyzed | analysis-agent | data-api-contract-changer | sdk-library-contract-design | architecture-impact-reviewer | implementation-structure-design | True |
| structure-package-supply-chain-not-reuse | - | analyzed | analysis-agent | engineering-change-analysis | package-dependency-management | architecture-impact-reviewer | implementation-structure-design | True |
| platform-infrastructure-direct | anti:cloud-platform-extension | direct | task-agent | platform-infrastructure-change-builder | infrastructure-as-code-safety | ai-code-review-refactor | reliability-observability-gate, cloud-platform-extension | True |
| repository-tooling-direct | - | direct | task-agent | repository-tooling-change-builder | build-tool-professional-usage, targeted-validation-selection | ai-code-review-refactor | incident-response-coordinator | True |
| incident-response-command | - | analyzed | analysis-agent | incident-response-coordinator | failure-diagnosis, observability | reliability-observability-gate | repository-tooling-change-builder | True |
| backend-idempotency | - | analyzed | analysis-agent | engineering-change-analysis | idempotency-retry-design | ai-code-review-refactor | - | True |
| frontend-direct | anti:cross-platform-client-extension | direct | task-agent | frontend-change-builder | state-management-design | ai-code-review-refactor | architecture-impact-reviewer, cross-platform-client-extension | True |
| experience-analysis | - | analyzed | analysis-agent | experience-impact-modeler | interaction-state-modeling | ai-code-review-refactor | - | True |
| experience-design-analysis | - | analyzed | analysis-agent | experience-impact-modeler | design-system-rules | ai-code-review-refactor | - | True |
| experience-combined-analysis | - | analyzed | analysis-agent | experience-impact-modeler | interaction-state-modeling, design-system-rules | ai-code-review-refactor | - | True |
| experience-generic-negative | - | analyzed | analysis-agent | engineering-change-analysis | repository-context-map | architecture-impact-reviewer | interaction-state-modeling, design-system-rules | True |
| public-api | - | analyzed | analysis-agent | engineering-change-analysis | api-contract-design, version-compatibility | architecture-impact-reviewer | - | True |
| accepted-api-analysis | - | analyzed | analysis-agent | data-api-contract-changer | version-compatibility | architecture-impact-reviewer | - | True |
| data-migration | - | analyzed | analysis-agent | engineering-change-analysis | data-migration-design, transaction-consistency, release-rollback | delivery-release-gate | - | True |
| accepted-data-analysis | - | analyzed | analysis-agent | data-middleware-change-builder | transaction-consistency | quality-test-gate | - | True |
| integration | - | analyzed | analysis-agent | engineering-change-analysis | consumer-impact-analysis, failure-contract-design | ai-code-review-refactor | - | True |
| accepted-integration-analysis | - | analyzed | analysis-agent | integration-change-builder | contract-testing | ai-code-review-refactor | - | True |
| validation | anti:windows-platform-extension | direct | task-agent | quality-test-gate | regression-testing | ai-code-review-refactor | windows-platform-extension | True |
| security | - | analyzed | analysis-agent | security-privacy-gate | permission-boundary-modeling, threat-modeling | security-privacy-gate | - | True |
| security-ssrf-boundary | - | analyzed | analysis-agent | engineering-change-analysis | threat-modeling, web-security | security-privacy-gate | - | True |
| reliability | - | direct | review-agent | reliability-observability-gate | degradation-circuit-breaking, observability, backup-recovery | reliability-observability-gate | - | True |
| cache-stampede-reliability | - | analyzed | analysis-agent | engineering-change-analysis | concurrency-control, degradation-circuit-breaking, observability | reliability-observability-gate | - | True |
| logging | anti:macos-platform-extension | direct | task-agent | logging-design-gate | logging-error-handling | logging-design-gate | macos-platform-extension | True |
| release | - | direct | review-agent | delivery-release-gate | release-rollback, version-compatibility | delivery-release-gate | - | True |
| documentation | anti:linux-desktop-platform-extension | direct | task-agent | change-documentation-gate | documentation-generation | change-documentation-gate | logging-design-gate, linux-desktop-platform-extension | True |
| review-only | - | direct | review-agent | ai-code-review-refactor | code-review | ai-code-review-refactor | - | True |
| engineering-artifact-review | - | direct | review-agent | engineering-artifact-review | - | engineering-artifact-review | - | True |
| ai-rag-tool-authority | ai-product-extension:retrieval-data:canonical | analyzed | analysis-agent | engineering-change-analysis | ai-product-extension, repository-context-map | architecture-impact-reviewer | - | True |
| ai-retrieval-permission-paraphrase | ai-product-extension:retrieval-data:paraphrase | analyzed | analysis-agent | engineering-change-analysis | ai-product-extension, repository-context-map | architecture-impact-reviewer | - | True |
| ai-agent-tool-authority | ai-product-extension:agent-model-authority:canonical | analyzed | analysis-agent | engineering-change-analysis | ai-product-extension, repository-context-map | architecture-impact-reviewer | - | True |
| ai-model-decision-paraphrase | ai-product-extension:agent-model-authority:paraphrase | analyzed | analysis-agent | engineering-change-analysis | ai-product-extension, repository-context-map | architecture-impact-reviewer | - | True |
| ai-transition-search-to-prompt-context | transition:ai-product-extension:retrieval-data | analyzed | analysis-agent | engineering-change-analysis | ai-product-extension, repository-context-map | architecture-impact-reviewer | - | True |
| ai-rag-http-contrast-clause | ai-product-extension:retrieval-data:paraphrase | analyzed | analysis-agent | engineering-change-analysis | ai-product-extension, repository-context-map | architecture-impact-reviewer | - | True |
| ai-anti-static-search | anti:ai-product-extension | analyzed | analysis-agent | engineering-change-analysis | repository-context-map | architecture-impact-reviewer | ai-product-extension | True |
| ai-anti-unchanged-rag-documentation | anti:ai-product-extension | analyzed | analysis-agent | engineering-change-analysis | repository-context-map | architecture-impact-reviewer | ai-product-extension | True |
| ai-anti-database-model-evaluation | anti:ai-product-extension | analyzed | analysis-agent | engineering-change-analysis | repository-context-map | architecture-impact-reviewer | ai-product-extension | True |
| bigdata-cdc-stream-replay | bigdata-product-extension:stream-cdc-replay:canonical | analyzed | analysis-agent | engineering-change-analysis | bigdata-product-extension, repository-context-map | architecture-impact-reviewer | - | True |
| bigdata-stream-checkpoint-paraphrase | bigdata-product-extension:stream-cdc-replay:paraphrase | analyzed | analysis-agent | engineering-change-analysis | bigdata-product-extension, repository-context-map | architecture-impact-reviewer | - | True |
| bigdata-distributed-backfill-schema | bigdata-product-extension:distributed-batch-schema:canonical | analyzed | analysis-agent | engineering-change-analysis | bigdata-product-extension, repository-context-map | architecture-impact-reviewer | - | True |
| bigdata-lake-reprocessing-paraphrase | bigdata-product-extension:distributed-batch-schema:paraphrase | analyzed | analysis-agent | engineering-change-analysis | bigdata-product-extension, repository-context-map | architecture-impact-reviewer | - | True |
| bigdata-transition-table-to-distributed-batch | transition:bigdata-product-extension:distributed-batch-schema | direct | task-agent | data-middleware-change-builder | bigdata-product-extension | ai-code-review-refactor | - | True |
| bigdata-anti-single-database-table | anti:bigdata-product-extension | analyzed | analysis-agent | data-middleware-change-builder | transaction-consistency | quality-test-gate | bigdata-product-extension | True |
| bigdata-anti-single-table-without-pipeline | anti:bigdata-product-extension | analyzed | analysis-agent | data-middleware-change-builder | transaction-consistency | quality-test-gate | bigdata-product-extension | True |
| bigdata-anti-unchanged-pipeline-documentation | anti:bigdata-product-extension | analyzed | analysis-agent | engineering-change-analysis | repository-context-map | architecture-impact-reviewer | bigdata-product-extension | True |
| iot-firmware-actuator-rollout | iot-embedded-extension:firmware-update-recovery:canonical | analyzed | analysis-agent | engineering-change-analysis | iot-embedded-extension, repository-context-map | architecture-impact-reviewer | - | True |
| iot-firmware-brownout-paraphrase | iot-embedded-extension:firmware-update-recovery:paraphrase | analyzed | analysis-agent | engineering-change-analysis | iot-embedded-extension, repository-context-map | architecture-impact-reviewer | - | True |
| iot-device-physical-runtime | iot-embedded-extension:device-physical-runtime:canonical | analyzed | analysis-agent | engineering-change-analysis | iot-embedded-extension, repository-context-map | architecture-impact-reviewer | - | True |
| iot-edge-provisioning-paraphrase | iot-embedded-extension:device-physical-runtime:paraphrase | analyzed | analysis-agent | engineering-change-analysis | iot-embedded-extension, repository-context-map | architecture-impact-reviewer | - | True |
| iot-transition-cloud-api-to-device-protocol | transition:iot-embedded-extension:device-physical-runtime | analyzed | analysis-agent | engineering-change-analysis | iot-embedded-extension, repository-context-map | architecture-impact-reviewer | - | True |
| iot-anti-cloud-device-api | anti:iot-embedded-extension | analyzed | analysis-agent | engineering-change-analysis | api-contract-design, version-compatibility | architecture-impact-reviewer | iot-embedded-extension | True |
| iot-anti-cloud-only-no-firmware-physical | anti:iot-embedded-extension | analyzed | analysis-agent | engineering-change-analysis | api-contract-design, version-compatibility | architecture-impact-reviewer | iot-embedded-extension | True |
| iot-anti-unchanged-protocol-documentation | anti:iot-embedded-extension | analyzed | analysis-agent | engineering-change-analysis | repository-context-map | architecture-impact-reviewer | iot-embedded-extension | True |
| iot-anti-cloud-network-protocol-timing | anti:iot-embedded-extension | analyzed | analysis-agent | engineering-change-analysis | repository-context-map | architecture-impact-reviewer | iot-embedded-extension | True |
| low-level-ffi-ownership | low-level-systems-extension:abi-ffi-memory:canonical | analyzed | analysis-agent | engineering-change-analysis | low-level-systems-extension, repository-context-map | architecture-impact-reviewer | - | True |
| low-level-native-memory-paraphrase | low-level-systems-extension:abi-ffi-memory:paraphrase | analyzed | analysis-agent | engineering-change-analysis | low-level-systems-extension, repository-context-map | architecture-impact-reviewer | - | True |
| low-level-kernel-driver | low-level-systems-extension:kernel-realtime-concurrency:canonical | analyzed | analysis-agent | engineering-change-analysis | low-level-systems-extension, repository-context-map | architecture-impact-reviewer | - | True |
| low-level-realtime-paraphrase | low-level-systems-extension:kernel-realtime-concurrency:paraphrase | analyzed | analysis-agent | engineering-change-analysis | low-level-systems-extension, repository-context-map | architecture-impact-reviewer | - | True |
| low-level-transition-rust-to-os-resource | transition:low-level-systems-extension:abi-ffi-memory | direct | task-agent | backend-change-builder | low-level-systems-extension | ai-code-review-refactor | - | True |
| low-level-anti-rust-business-service | anti:low-level-systems-extension | direct | task-agent | backend-change-builder | - | ai-code-review-refactor | low-level-systems-extension | True |
| low-level-anti-unchanged-ffi-documentation | anti:low-level-systems-extension | direct | task-agent | backend-change-builder | - | ai-code-review-refactor | low-level-systems-extension | True |
| mobile-native-lifecycle-permission | android-platform-extension:platform-lifecycle-authority:canonical | direct | task-agent | installed-client-change-builder | android-platform-extension | ai-code-review-refactor | - | True |
| mobile-android-permission-paraphrase | android-platform-extension:platform-lifecycle-authority:paraphrase | direct | task-agent | installed-client-change-builder | android-platform-extension | ai-code-review-refactor | - | True |
| android-accessibility-platform-authority | android-platform-extension:accessibility-platform-authority:canonical | direct | task-agent | installed-client-change-builder | android-platform-extension, accessibility-inclusive-design | ai-code-review-refactor | - | True |
| android-accessibility-compose-focus-paraphrase | android-platform-extension:accessibility-platform-authority:paraphrase | direct | task-agent | installed-client-change-builder | android-platform-extension, accessibility-inclusive-design | ai-code-review-refactor | - | True |
| mobile-offline-deeplink | ios-ipados-platform-extension:platform-lifecycle-authority:canonical | direct | task-agent | installed-client-change-builder | ios-ipados-platform-extension | ai-code-review-refactor | - | True |
| mobile-store-upgrade-paraphrase | ios-ipados-platform-extension:platform-lifecycle-authority:paraphrase | direct | task-agent | installed-client-change-builder | ios-ipados-platform-extension | ai-code-review-refactor | - | True |
| mobile-transition-pwa-to-native-lifecycle | transition:android-platform-extension:platform-lifecycle-authority | direct | task-agent | installed-client-change-builder | android-platform-extension | ai-code-review-refactor | - | True |
| mobile-anti-responsive-pwa | anti:android-platform-extension | direct | task-agent | frontend-change-builder | state-management-design | ai-code-review-refactor | android-platform-extension | True |
| mobile-anti-unchanged-permission-help | anti:ios-ipados-platform-extension | direct | task-agent | frontend-change-builder | state-management-design | ai-code-review-refactor | ios-ipados-platform-extension | True |
| payment-security | payment-trading-extension:money-ledger-settlement:canonical | analyzed | analysis-agent | engineering-change-analysis | payment-trading-extension, repository-context-map | architecture-impact-reviewer | - | True |
| payment-ledger-settlement-paraphrase | payment-trading-extension:money-ledger-settlement:paraphrase | analyzed | analysis-agent | engineering-change-analysis | payment-trading-extension, repository-context-map | architecture-impact-reviewer | - | True |
| payment-trading-execution | payment-trading-extension:trading-order-execution:canonical | analyzed | analysis-agent | engineering-change-analysis | payment-trading-extension, repository-context-map | architecture-impact-reviewer | - | True |
| payment-venue-order-paraphrase | payment-trading-extension:trading-order-execution:paraphrase | analyzed | analysis-agent | engineering-change-analysis | payment-trading-extension, repository-context-map | architecture-impact-reviewer | - | True |
| payment-transition-price-display-to-wallet-ledger | transition:payment-trading-extension:money-ledger-settlement | analyzed | analysis-agent | engineering-change-analysis | payment-trading-extension, repository-context-map | architecture-impact-reviewer | - | True |
| payment-wallet-custody-accounting-conflict | payment-trading-extension:money-ledger-settlement:paraphrase | analyzed | analysis-agent | engineering-change-analysis | payment-trading-extension, repository-context-map | architecture-impact-reviewer | - | True |
| payment-anti-authorization-copy | anti:payment-trading-extension | direct | task-agent | frontend-change-builder | state-management-design | ai-code-review-refactor | security-privacy-gate, payment-trading-extension | True |
| payment-anti-order-copy | anti:payment-trading-extension | direct | task-agent | frontend-change-builder | state-management-design | ai-code-review-refactor | security-privacy-gate, payment-trading-extension | True |
| payment-anti-order-display-unchanged-state | anti:payment-trading-extension | direct | task-agent | frontend-change-builder | state-management-design | ai-code-review-refactor | security-privacy-gate, payment-trading-extension | True |
| payment-anti-unchanged-wallet-copy | anti:payment-trading-extension | direct | task-agent | frontend-change-builder | state-management-design | ai-code-review-refactor | security-privacy-gate, payment-trading-extension | True |
| web3-chain-custody-finality | web3-product-extension:chain-custody-finality:canonical | analyzed | analysis-agent | engineering-change-analysis | web3-product-extension, repository-context-map | architecture-impact-reviewer | - | True |
| web3-wallet-signing-paraphrase | web3-product-extension:chain-custody-finality:paraphrase | analyzed | analysis-agent | engineering-change-analysis | web3-product-extension, repository-context-map | architecture-impact-reviewer | - | True |
| web3-chain-contract-finality | web3-product-extension:contract-cross-chain:canonical | analyzed | analysis-agent | engineering-change-analysis | web3-product-extension, repository-context-map | architecture-impact-reviewer | - | True |
| web3-bridge-proof-paraphrase | web3-product-extension:contract-cross-chain:paraphrase | analyzed | analysis-agent | engineering-change-analysis | web3-product-extension, repository-context-map | architecture-impact-reviewer | - | True |
| web3-transition-api-signature-to-chain-custody | transition:web3-product-extension:chain-custody-finality | analyzed | analysis-agent | engineering-change-analysis | web3-product-extension, repository-context-map | architecture-impact-reviewer | - | True |
| web3-anti-hash-signature | anti:web3-product-extension | direct | task-agent | backend-change-builder | - | ai-code-review-refactor | web3-product-extension | True |
| web3-anti-unchanged-wallet-documentation | anti:web3-product-extension | direct | task-agent | backend-change-builder | - | ai-code-review-refactor | web3-product-extension | True |
| web3-anti-payment-wallet-recovery | anti:web3-product-extension | direct | task-agent | frontend-change-builder | state-management-design | ai-code-review-refactor | web3-product-extension | True |
| security-anti-credential-session-internal-refactor | - | direct | task-agent | backend-change-builder | - | ai-code-review-refactor | security-privacy-gate | True |
| security-credential-session-lifecycle-change | - | analyzed | analysis-agent | security-privacy-gate | authentication-security | security-privacy-gate | - | True |
| security-anti-reliability-only | - | direct | review-agent | reliability-observability-gate | degradation-circuit-breaking, observability, backup-recovery | reliability-observability-gate | security-privacy-gate | True |
| security-anti-input-shape | - | analyzed | analysis-agent | data-api-contract-changer | api-contract-design | architecture-impact-reviewer | security-privacy-gate | True |
| security-anti-scanner-report | - | direct | task-agent | change-documentation-gate | documentation-generation | change-documentation-gate | security-privacy-gate | True |
| reliability-anti-unit-local-performance | - | direct | task-agent | quality-test-gate | regression-testing | ai-code-review-refactor | reliability-observability-gate | True |
| reliability-anti-logging-field | - | direct | task-agent | logging-design-gate | logging-error-handling | logging-design-gate | reliability-observability-gate | True |
| reliability-anti-release-ordering | - | direct | review-agent | delivery-release-gate | release-rollback, version-compatibility | delivery-release-gate | reliability-observability-gate | True |
| reliability-anti-data-correctness | - | analyzed | analysis-agent | data-middleware-change-builder | transaction-consistency | quality-test-gate | reliability-observability-gate | True |
| t2b-critical-backend-owner | - | analyzed | analysis-agent | engineering-change-analysis | repository-context-map | architecture-impact-reviewer | - | True |
| t2b-critical-backend-placement | - | analyzed | analysis-agent | engineering-change-analysis | repository-context-map | architecture-impact-reviewer | - | True |
| t2b-critical-backend-acceptance | - | analyzed | analysis-agent | engineering-change-analysis | repository-context-map | architecture-impact-reviewer | - | True |
| t2b-critical-backend-verification | - | analyzed | analysis-agent | engineering-change-analysis | repository-context-map | architecture-impact-reviewer | - | True |
| t2b-critical-backend-rollback | - | analyzed | analysis-agent | engineering-change-analysis | repository-context-map | architecture-impact-reviewer | - | True |
| t2b-critical-backend-revert | - | analyzed | analysis-agent | engineering-change-analysis | repository-context-map | architecture-impact-reviewer | - | True |
| t2b-backend-resolved-direct | - | direct | task-agent | backend-change-builder | - | ai-code-review-refactor | - | True |
| t2b-backend-negated-unknown-direct | - | direct | task-agent | backend-change-builder | - | ai-code-review-refactor | - | True |
| t2b-repair-owner-not-unknown-direct | - | direct | task-agent | backend-change-builder | - | ai-code-review-refactor | - | True |
| t2b-repair-rollback-no-longer-unknown-direct | - | direct | task-agent | backend-change-builder | - | ai-code-review-refactor | - | True |
| t2b-repair-no-owner-unknown-direct | - | direct | task-agent | backend-change-builder | - | ai-code-review-refactor | - | True |
| t2b-repair-unrelated-unknown-direct | - | direct | task-agent | backend-change-builder | - | ai-code-review-refactor | - | True |
| t2b-preparation-backend-repair | - | analyzed | analysis-agent | engineering-change-analysis | repository-context-map | ai-code-review-refactor | - | True |
| t2b-preparation-tenant-authorization | - | analyzed | analysis-agent | engineering-change-analysis | permission-boundary-modeling, threat-modeling | security-privacy-gate | - | True |
| t2b-dedicated-tenant-authorization-analysis | - | analyzed | analysis-agent | security-privacy-gate | permission-boundary-modeling, threat-modeling | security-privacy-gate | - | True |
| t2b-preparation-payment | - | analyzed | analysis-agent | engineering-change-analysis | payment-trading-extension, repository-context-map | architecture-impact-reviewer | - | True |
| t2b-dedicated-payment-analysis | - | analyzed | analysis-agent | engineering-change-analysis | payment-trading-extension, repository-context-map | architecture-impact-reviewer | - | True |
| t2b-preparation-ai | - | analyzed | analysis-agent | engineering-change-analysis | ai-product-extension, repository-context-map | architecture-impact-reviewer | - | True |
| t2b-dedicated-ai-analysis | - | analyzed | analysis-agent | engineering-change-analysis | ai-product-extension, repository-context-map | architecture-impact-reviewer | - | True |
| t2b-preparation-platform | - | analyzed | analysis-agent | engineering-change-analysis | - | ai-code-review-refactor | - | True |
| t2b-dedicated-platform-owner | - | analyzed | analysis-agent | engineering-change-analysis | repository-context-map | architecture-impact-reviewer | - | True |
| t2b-critical-preparation-tie | - | analyzed | analysis-agent | engineering-change-analysis | repository-context-map | architecture-impact-reviewer | - | True |
| t2b-critical-preparation-tie-reversed | - | analyzed | analysis-agent | engineering-change-analysis | repository-context-map | architecture-impact-reviewer | - | True |
| t2b-bare-backend-plan-not-preparation | - | direct | task-agent | backend-change-builder | - | ai-code-review-refactor | - | True |
| t2c-review-security-tenant-auth-diff | - | direct | review-agent | security-privacy-gate | permission-boundary-modeling, threat-modeling | security-privacy-gate | - | True |
| t2c-review-security-auth-unchanged | - | direct | review-agent | ai-code-review-refactor | refactoring | ai-code-review-refactor | - | True |
| t2c-review-security-background-context | - | direct | review-agent | ai-code-review-refactor | refactoring | ai-code-review-refactor | - | True |
| t2c-review-release-production-rollout | - | direct | review-agent | delivery-release-gate | release-rollback, version-compatibility | delivery-release-gate | - | True |
| t2c-review-release-out-of-scope | - | direct | review-agent | ai-code-review-refactor | refactoring | ai-code-review-refactor | - | True |
| t2c-review-logging-secret-redaction | - | direct | review-agent | logging-design-gate | logging-error-handling, secret-configuration-security | logging-design-gate | - | True |
| t2c-review-logging-unchanged | - | direct | review-agent | ai-code-review-refactor | refactoring | ai-code-review-refactor | - | True |
| t2c-review-reliability-slo-recovery | - | direct | review-agent | reliability-observability-gate | degradation-circuit-breaking, observability, backup-recovery | reliability-observability-gate | - | True |
| t2c-review-reliability-slo-unchanged | - | direct | review-agent | ai-code-review-refactor | refactoring | ai-code-review-refactor | - | True |
| t2c-review-generic-refactor-diff | - | direct | review-agent | ai-code-review-refactor | refactoring | ai-code-review-refactor | - | True |
| t2c-review-regression-security-risk | - | direct | review-agent | security-privacy-gate | permission-boundary-modeling, threat-modeling, regression-testing | security-privacy-gate | - | True |
| t2c-review-regression-ordinary | - | direct | review-agent | ai-code-review-refactor | regression-testing | ai-code-review-refactor | - | True |
| t2c-preparation-security-risk | - | analyzed | analysis-agent | engineering-change-analysis | permission-boundary-modeling, threat-modeling | security-privacy-gate | - | True |
| t2c-preparation-release-risk | - | analyzed | analysis-agent | engineering-change-analysis | release-rollback, version-compatibility | delivery-release-gate | - | True |
| t2c-preparation-logging-risk | - | analyzed | analysis-agent | engineering-change-analysis | - | logging-design-gate | - | True |
| t2c-preparation-reliability-risk | - | analyzed | analysis-agent | engineering-change-analysis | degradation-circuit-breaking, observability | reliability-observability-gate | - | True |
| t2c-repair-security-material-logging-none | - | direct | review-agent | security-privacy-gate | permission-boundary-modeling, threat-modeling | security-privacy-gate | - | True |
| t2c-repair-logging-material-security-unchanged | - | direct | review-agent | logging-design-gate | logging-error-handling, secret-configuration-security | logging-design-gate | - | True |
| t2c-repair-security-material-release-out-of-scope | - | direct | review-agent | security-privacy-gate | permission-boundary-modeling, threat-modeling | security-privacy-gate | - | True |
| t2c-repair-release-material-security-background | - | direct | review-agent | delivery-release-gate | release-rollback, version-compatibility | delivery-release-gate | - | True |
| t2c-repair-release-material-reliability-unchanged | - | direct | review-agent | delivery-release-gate | release-rollback, version-compatibility | delivery-release-gate | - | True |
| t2c-repair-reliability-material-release-out-of-scope | - | direct | review-agent | reliability-observability-gate | degradation-circuit-breaking, observability, backup-recovery | reliability-observability-gate | - | True |
| t2c-repair-logging-material-reliability-none | - | direct | review-agent | logging-design-gate | logging-error-handling, secret-configuration-security, observability | logging-design-gate | - | True |
| t2c-repair-reliability-material-logging-background | - | direct | review-agent | reliability-observability-gate | degradation-circuit-breaking, observability, backup-recovery | reliability-observability-gate | - | True |
| t2c-repair-conflict-security-release | - | analyzed | analysis-agent | engineering-change-analysis | repository-context-map | architecture-impact-reviewer | - | True |
| t2c-repair-conflict-release-security | - | analyzed | analysis-agent | engineering-change-analysis | repository-context-map | architecture-impact-reviewer | - | True |
| t2c-repair-conflict-logging-reliability | - | analyzed | analysis-agent | engineering-change-analysis | repository-context-map | architecture-impact-reviewer | - | True |
| t2c-repair-conflict-reliability-logging | - | analyzed | analysis-agent | engineering-change-analysis | repository-context-map | architecture-impact-reviewer | - | True |
| external-integration-consumer-only | - | analyzed | analysis-agent | engineering-change-analysis | consumer-impact-analysis | ai-code-review-refactor | - | True |
| external-integration-failure-only | - | analyzed | analysis-agent | engineering-change-analysis | failure-contract-design | ai-code-review-refactor | - | True |
| external-integration-consumer-reliability-conflict | - | analyzed | analysis-agent | engineering-change-analysis | repository-context-map | architecture-impact-reviewer | - | True |
| external-integration-failure-reliability-conflict | - | analyzed | analysis-agent | engineering-change-analysis | repository-context-map | architecture-impact-reviewer | - | True |
| external-integration-combined-reliability-conflict | - | analyzed | analysis-agent | engineering-change-analysis | repository-context-map | architecture-impact-reviewer | - | True |
| wave1a-stack-architecture-analysis | - | analyzed | analysis-agent | architecture-impact-reviewer | technology-stack-selection | architecture-impact-reviewer | - | True |
| wave1a-stack-accepted-brief-review | - | direct | review-agent | high-risk-design-review | technology-stack-selection | high-risk-design-review | - | True |
| wave1a-module-boundary-major-brief-review | - | direct | review-agent | high-risk-design-review | module-boundary-design | high-risk-design-review | - | True |
| wave1a-config-frontend | - | direct | task-agent | frontend-change-builder | web-platform-professional-usage, configuration-runtime-policy | ai-code-review-refactor | - | True |
| wave1a-config-installed-client | - | direct | task-agent | installed-client-change-builder | configuration-runtime-policy | ai-code-review-refactor | - | True |
| wave1a-config-backend | - | direct | task-agent | backend-change-builder | configuration-runtime-policy | ai-code-review-refactor | - | True |
| wave1a-config-data-middleware | - | direct | task-agent | data-middleware-change-builder | configuration-runtime-policy | ai-code-review-refactor | - | True |
| wave1a-config-platform-infrastructure | - | direct | task-agent | platform-infrastructure-change-builder | infrastructure-as-code-safety, configuration-runtime-policy | ai-code-review-refactor | - | True |
| wave1a-config-integration | - | direct | task-agent | integration-change-builder | configuration-runtime-policy | ai-code-review-refactor | - | True |
| wave1a-config-repository-tooling | - | direct | task-agent | repository-tooling-change-builder | build-tool-professional-usage, targeted-validation-selection, configuration-runtime-policy | ai-code-review-refactor | - | True |
| wave1a-config-owner-unknown | - | analyzed | analysis-agent | engineering-change-analysis | repository-context-map, configuration-runtime-policy | architecture-impact-reviewer | - | True |
| wave1a-dependency-frontend | - | direct | task-agent | frontend-change-builder | web-platform-professional-usage, dependency-vulnerability-scanning | security-privacy-gate | - | True |
| wave1a-dependency-installed-client | - | direct | task-agent | installed-client-change-builder | dependency-vulnerability-scanning | security-privacy-gate | - | True |
| wave1a-dependency-backend | - | direct | task-agent | backend-change-builder | dependency-vulnerability-scanning | security-privacy-gate | - | True |
| wave1a-dependency-data-middleware | - | direct | task-agent | data-middleware-change-builder | dependency-vulnerability-scanning | security-privacy-gate | - | True |
| wave1a-dependency-platform-infrastructure | - | direct | task-agent | platform-infrastructure-change-builder | infrastructure-as-code-safety, dependency-vulnerability-scanning | security-privacy-gate | - | True |
| wave1a-dependency-integration | - | direct | task-agent | integration-change-builder | dependency-vulnerability-scanning | security-privacy-gate | - | True |
| wave1a-dependency-repository-tooling | - | direct | task-agent | repository-tooling-change-builder | build-tool-professional-usage, targeted-validation-selection, dependency-vulnerability-scanning | security-privacy-gate | - | True |
| wave1a-stack-language-negative | - | analyzed | analysis-agent | engineering-change-analysis | repository-context-map | architecture-impact-reviewer | technology-stack-selection | True |
| wave1a-stack-fixed-negative | - | analyzed | analysis-agent | engineering-change-analysis | repository-context-map | architecture-impact-reviewer | technology-stack-selection | True |
| wave1a-stack-invalid-brief-negative | - | analyzed | analysis-agent | engineering-change-analysis | repository-context-map | architecture-impact-reviewer | technology-stack-selection | True |
| wave1a-stack-unaccepted-brief-negative | - | analyzed | analysis-agent | engineering-change-analysis | repository-context-map | architecture-impact-reviewer | technology-stack-selection | True |
| wave1a-stack-stale-brief-negative | - | analyzed | analysis-agent | engineering-change-analysis | repository-context-map | architecture-impact-reviewer | technology-stack-selection | True |
| wave1a-config-generic-negative | - | analyzed | analysis-agent | engineering-change-analysis | repository-context-map | architecture-impact-reviewer | configuration-runtime-policy | True |
| wave1a-config-build-only-negative | - | analyzed | analysis-agent | engineering-change-analysis | repository-context-map | architecture-impact-reviewer | configuration-runtime-policy | True |
| wave1a-config-secret-only-negative | - | direct | task-agent | backend-change-builder | - | logging-design-gate | configuration-runtime-policy | True |
| wave1a-dependency-package-mechanics-negative | - | analyzed | analysis-agent | engineering-change-analysis | package-dependency-management | architecture-impact-reviewer | technology-stack-selection, dependency-vulnerability-scanning | True |
| wave1a-dependency-lockfile-negative | - | direct | task-agent | repository-tooling-change-builder | - | ai-code-review-refactor | dependency-vulnerability-scanning | True |
| wave1a-dependency-advisory-keyword-negative | - | analyzed | analysis-agent | engineering-change-analysis | repository-context-map | architecture-impact-reviewer | dependency-vulnerability-scanning | True |
| wave1a-sandbox-dev-only-negative | - | analyzed | analysis-agent | engineering-change-analysis | repository-context-map | architecture-impact-reviewer | agent-tool-permission-sandbox | True |

## Limitations

- Deterministic routing fixtures do not measure wall-clock performance.
- Fixture agreement does not prove real-host accuracy or the installed user experience.
- Prompt matching is a deterministic regression oracle, not a learned or production router.

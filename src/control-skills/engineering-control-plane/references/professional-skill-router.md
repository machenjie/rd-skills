# Professional Skill Router
Route the expertise needed for the current request. Implementation requests start with a task-agent that can read, search, edit, and execute. Locating an owner, file, caller, or test needs bounded discovery, not a separate Analysis assignment. Use deeper Analysis when the user asks or current evidence reveals a question that can materially change implementation.
Select one Primary Professional from the Professional registry. Load only its generated `references/runtime/selector.json` and select zero to three Layer 3 Skills from positive evidence and anti-triggers. Validate each selected item against the Professional, Profile, and reciprocal Domain authorization; never truncate an invalid selection or load the full Foundation/Domain catalog. Runtime paths resolve inside the Host-selected Professional root using Core's build identity. Build/package integrity remains an authoring concern.
Main owns the route. Task and Review consume their assigned expertise and necessary Targeted References. A projection typo is corrected from the current selection without repeating Analysis. New evidence may require different expertise; it does not automatically require a new design. An optional Brief may carry established decisions for complex cross-agent work.
The table's Review column names useful expertise when independent review is selected. It creates no review obligation. Use independent judgment for an explicit request or an important reachable semantic failure that local checks cannot adequately assess. Review selects its own zero to three Layer 3 Skills, rather than copying implementation choices. A task boundary, file count, edit count, or implementation completion is not a review trigger.
Safety expertise needs a reachable trust, sensitive-data, executable-input, privilege, destructive, production, or irreversible boundary. Words such as log, shell, path, mutable, or external do not establish that boundary. Repository tooling normally uses its existing owner and filesystem/process correctness knowledge.
| Task signal | Start profile | Primary Professional Skill | Review expertise when selected |
| --- | --- | --- | --- |
| explicit standalone requirement clarification | analysis-agent | change-intake-compiler | ai-code-review-refactor |
| explicit standalone acceptance definition | analysis-agent | acceptance-criteria-builder | ai-code-review-refactor |
| bounded local backend bug fix | task-agent | backend-change-builder | ai-code-review-refactor |
| bounded backend feature with local owner discovery | task-agent | backend-change-builder | architecture-impact-reviewer |
| bounded local backend repair | task-agent | backend-change-builder | ai-code-review-refactor |
| bounded repository-owned generator plugin harness internal CLI monorepo automation or maintenance utility source change | task-agent | repository-tooling-change-builder | ai-code-review-refactor |
| repository implementation or repair with owner files not yet located | task-agent | repository-tooling-change-builder | architecture-impact-reviewer |
| source-backed engineering question (`source-backed-answer`) | analysis-agent | engineering-change-analysis | architecture-impact-reviewer |
| failure diagnosis (`diagnosis-only`) | analysis-agent | engineering-change-analysis | reliability-observability-gate |
| integration implementation with established dependencies | task-agent | integration-change-builder | ai-code-review-refactor |
| implementation with established architecture and dependency decisions | task-agent | repository-tooling-change-builder | high-risk-design-review |
| explicit dependency-planning request with established decisions | analysis-agent | task-dag-planner | engineering-artifact-review |
| explicit user-flow or interaction analysis | analysis-agent | experience-impact-modeler | ai-code-review-refactor |
| explicit domain-rule or invariant analysis | analysis-agent | domain-impact-modeler | architecture-impact-reviewer |
| explicit module ownership architecture artifact or architecture tradeoff analysis | analysis-agent | architecture-impact-reviewer | architecture-impact-reviewer |
| public API or data-contract implementation | task-agent | data-api-contract-changer | architecture-impact-reviewer |
| explicit API compatibility artifact analysis when the user requests the artifact decision | analysis-agent | data-api-contract-changer | architecture-impact-reviewer |
| stateful database cache queue or migration implementation | task-agent | data-middleware-change-builder | delivery-release-gate |
| explicit data consistency or recovery artifact analysis when the user requests the artifact decision | analysis-agent | data-middleware-change-builder | quality-test-gate |
| external or cross-module integration implementation | task-agent | integration-change-builder | ai-code-review-refactor |
| explicit integration handoff artifact analysis when the user requests the artifact decision | analysis-agent | integration-change-builder | ai-code-review-refactor |
| explicit test-data or test-strategy analysis | analysis-agent | quality-test-gate | quality-test-gate |
| test implementation | task-agent | quality-test-gate | ai-code-review-refactor |
| explicit analysis of a proved reachable trust, privilege, permission, privacy, credential, secret, or authentication-authorization boundary, including hardening or review | analysis-agent | security-privacy-gate | security-privacy-gate |
| SSRF or URL-fetch security implementation | task-agent | security-privacy-gate | security-privacy-gate |
| security implementation | task-agent | security-privacy-gate | security-privacy-gate |
| cache stampede or cache-contention implementation | task-agent | reliability-observability-gate | reliability-observability-gate |
| reliability implementation | task-agent | reliability-observability-gate | reliability-observability-gate |
| delivery artifact implementation | task-agent | delivery-release-gate | delivery-release-gate |
| explicit reliability or observability analysis | analysis-agent | reliability-observability-gate | reliability-observability-gate |
| active multi-responder incident command mitigation coordination communications or handoff | analysis-agent | incident-response-coordinator | reliability-observability-gate |
| reliability or observability review | review-agent | reliability-observability-gate | reliability-observability-gate |
| logging implementation | task-agent | logging-design-gate | logging-design-gate |
| logging review | review-agent | logging-design-gate | logging-design-gate |
| release implementation | task-agent | delivery-release-gate | delivery-release-gate |
| explicit release rollout or rollback plan analysis | analysis-agent | delivery-release-gate | delivery-release-gate |
| release artifact or diff review | review-agent | delivery-release-gate | delivery-release-gate |
| documentation implementation | task-agent | change-documentation-gate | change-documentation-gate |
| documentation review | review-agent | change-documentation-gate | change-documentation-gate |
| general diff review | review-agent | ai-code-review-refactor | ai-code-review-refactor |
| model, prompt, retrieval, embedding, evaluation, or AI data behavior with permission, model context, delegated authority, or consequential boundaries; excluding work with no AI surface and ordinary search without a model decision | task-agent | security-privacy-gate | security-privacy-gate |
| batch, stream, data lake, distributed compute, schema evolution, or high-volume pipeline with checkpoint, downstream, partition, consumer, or schema compatibility boundaries; excluding ordinary transactional persistence and large-table work without a distributed pipeline | task-agent | data-middleware-change-builder | quality-test-gate |
| device, firmware, edge, protocol, sensor, actuator, physical safety, or constrained runtime with recovery, activation, physical safety, timing, or hardware boundaries; excluding ordinary cloud work and APIs without device or firmware behavior | task-agent | delivery-release-gate | delivery-release-gate |
| kernel, driver, C, C++, Rust, memory, ABI, real-time, or systems concurrency with ownership, resource, deadline, or platform boundaries; excluding work with no systems boundary and C++ or Rust without a native ABI, OS, or resource boundary | task-agent | backend-change-builder | ai-code-review-refactor |
| Android application lifecycle or platform accessibility behavior with application lifecycle or accessibility behavior; excluding Web PWA backend infrastructure non-Android Kotlin-only or framework-only work without a confirmed Android target and store rollout signing authorization or release approval | task-agent | installed-client-change-builder | ai-code-review-refactor |
| iOS/iPadOS with application lifecycle; excluding Web PWA backend infrastructure non-Apple-mobile Swift-only or framework-only work without a confirmed iOS/iPadOS target and store rollout signing authorization or release approval | task-agent | installed-client-change-builder | ai-code-review-refactor |
| Windows packaged desktop application with application identity; excluding Web PWA generic backend infrastructure non-Windows C#-only PowerShell-only or framework-only work without a confirmed Windows target and release signing or rollout authorization | task-agent | installed-client-change-builder | ai-code-review-refactor |
| Windows service with service lifecycle; excluding Web PWA generic backend infrastructure non-Windows C#-only PowerShell-only or framework-only work without a confirmed Windows target and release signing or rollout authorization | task-agent | backend-change-builder | ai-code-review-refactor |
| macOS installed application with application lifecycle; excluding Web PWA backend infrastructure non-macOS Swift-only or framework-only work without a confirmed macOS target and release signing notarization or rollout authorization | task-agent | installed-client-change-builder | ai-code-review-refactor |
| Linux graphical desktop with desktop session; excluding Linux server service runtime Web PWA backend infrastructure language-only or framework-only work without a confirmed Linux desktop target and distribution rollout authorization or independent review | task-agent | installed-client-change-builder | ai-code-review-refactor |
| shared installed client with concrete platform targets; excluding framework name without repository build release or published-artifact target evidence and unknown target language-only Web PWA backend infrastructure or release authorization | task-agent | installed-client-change-builder | ai-code-review-refactor |
| cloud control plane with account authority; excluding unknown cloud scope provider-name-only local Kubernetes or generic backend work without cloud control-plane dependency and release authorization or production mutation | task-agent | platform-infrastructure-change-builder | ai-code-review-refactor |
| payment, ledger, balance, settlement, trading, order, wallet, or money movement with accounting, reconciliation, fill, or settlement boundaries; excluding work with no monetary invariant and orders without funds, ledger, settlement, or execution state | task-agent | backend-change-builder | architecture-impact-reviewer |
| blockchain, smart contract, wallet, key, chain transaction, or custody behavior with finality, recovery, authority, upgrade, or replay boundaries; excluding ordinary non-Web3 work and terminology without chain or custody behavior | task-agent | integration-change-builder | ai-code-review-refactor |

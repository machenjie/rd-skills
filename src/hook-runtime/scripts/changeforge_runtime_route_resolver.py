#!/usr/bin/env python3
"""Resolve hook classifications into canonical ChangeForge runtime routes.

The resolver is intentionally local and deterministic: it uses bounded hook
facts (stage, paths, compact surface names, and command program) and never reads
reference bodies, network resources, prompts from state, or project source.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Iterable

from changeforge_context_control_policy import (
    ROUTER_SELF_REFERENCES as CONTEXT_CONTROL_ROUTER_REFERENCES,
    apply_reference_budget,
    build_context_control_record,
    context_budget_limits,
    context_budget_mode,
)


ROUTER_SELF_REFERENCES = (
    "references/routing-rules.md",
    "references/skill-registry.md",
    "references/capability-index.md",
    "references/domain-extension-index.md",
)
RUNTIME_ROUTE_INDEX_NAME = "changeforge_runtime_route_index.json"

CODE_FILE_EXTENSIONS = frozenset(
    {
        ".c",
        ".cc",
        ".cpp",
        ".cxx",
        ".h",
        ".hh",
        ".hpp",
        ".ipp",
        ".tpp",
        ".go",
        ".java",
        ".kt",
        ".kts",
        ".js",
        ".jsx",
        ".ts",
        ".tsx",
        ".mts",
        ".cts",
        ".py",
        ".rs",
        ".sh",
        ".bash",
        ".zsh",
        ".sql",
    }
)

LANGUAGE_FILE_EXTENSIONS = {
    "go": (".go",),
    "typescript": (".ts", ".tsx", ".js", ".jsx", ".mts", ".cts"),
    "python": (".py",),
    "java-jvm": (".java", ".kt", ".kts"),
    "rust": (".rs",),
    "cpp": (".c", ".cc", ".cpp", ".cxx", ".h", ".hh", ".hpp", ".ipp", ".tpp"),
    "shell": (".sh", ".bash", ".zsh"),
    "sql": (".sql",),
}

LANGUAGE_CAPABILITIES = {
    "go": "go-professional-usage",
    "java-jvm": "java-jvm-professional-usage",
    "typescript": "typescript-professional-usage",
    "python": "python-professional-usage",
    "rust": "rust-professional-usage",
    "cpp": "cpp-professional-usage",
    "shell": "shell-cli-professional-usage",
    "sql": "sql-professional-usage",
}

LANGUAGE_SURFACE_SIGNALS = {
    "go": ("go", "golang", "goroutine", "context", "channel"),
    "java-jvm": ("java", "jvm", "spring", "executor", "thread"),
    "typescript": ("typescript", "ts", "node", "react", "promise"),
    "python": ("python", "py", "asyncio", "pytest", "type hints"),
    "rust": ("rust", "borrow", "lifetime", "unsafe", "cargo"),
    "cpp": ("c++", "cpp", "C ABI", "native C", "native C++", "raii", "abi", "ffi", "sanitizer"),
    "shell": ("shell", "bash", "sh", "zsh", "cli"),
    "sql": ("sql", "SQL query", "SQL index", ".sql"),
}

PRODUCT_SURFACE_ORDER = (
    "frontend-product",
    "backend-product",
    "api-contract",
    "data-model",
    "database-migration",
    "cache",
    "message-queue",
    "network-gateway",
    "search-analytics",
    "external-integration",
    "webhook",
    "infrastructure-deployment",
    "kubernetes-helm",
    "ci-cd",
    "ai-rag-agent",
    "web3",
    "payment-trading",
    "low-level-systems",
    "linux-systems",
    "sdk-library",
    "cli-daemon",
    "documentation-only",
    "git-workflow",
    "skill-authoring",
    "agent-runtime-governance",
    "repository-intelligence",
    "project-memory",
    "validation-broker",
    "execution-trajectory",
)

SOURCE_ROOT_PREFIX = "src/"
SKILL_AUTHORING_PREFIXES = (
    SOURCE_ROOT_PREFIX + "professional-skills/",
    SOURCE_ROOT_PREFIX + "foundation/capabilities/",
    SOURCE_ROOT_PREFIX + "domain-extensions/",
)
RUNTIME_AUTHORING_PREFIXES = (
    SOURCE_ROOT_PREFIX + "registry/",
    SOURCE_ROOT_PREFIX + "hook-runtime/",
)
SKILL_AUTHORING_TEXT_PATTERNS = (
    r"(?:^|[\s\"'`])src/(?:professional-skills|foundation/capabilities|domain-extensions|registry|hook-runtime)/",
    r"(?:^|[\s\"'`])(?:[\w./-]+/)?SKILL\.md\b",
    r"(?:^|[\s\"'`])routing-rules\.ya?ml\b",
    r"(?:^|[\s\"'`])stage-model\.ya?ml\b",
)
DOCS_ONLY_TEXT_PATH_RE = re.compile(
    r"(?:^|[\s\"'`])(?:docs|documentation)/[^\s\"'`]+"
    r"\.(?:md|mdx|rst|adoc|txt)\b",
    re.I,
)
CODE_TEXT_PATH_RE = re.compile(
    r"(?:^|[\s\"'`])(?:src|app|lib|internal|pkg|cmd|deploy|db|migrations?|tests?)/"
    r"[^\s\"'`]+\.(?:c|cc|cpp|cxx|h|hh|hpp|ipp|tpp|go|java|kt|kts|js|jsx|ts|tsx|mts|cts|py|rs|sh|bash|zsh|sql|ya?ml|json|toml)\b",
    re.I,
)
SECURITY_RISK_PATTERNS = (
    r"\bauth\b",
    r"\bauthorization\b",
    r"\bpermission\b",
    r"\brbac\b",
    r"\bsecret\b",
    r"\btoken\b",
    r"\bcredential\b",
    r"\bprivate key\b",
)

DOMAIN_EXTENSION_BY_SURFACE = {
    "ai-rag-agent": "ai-product-extension",
    "web3": "web3-product-extension",
    "payment-trading": "payment-trading-extension",
    "low-level-systems": "low-level-systems-extension",
}

ALL_DOMAIN_EXTENSIONS = (
    "web3-product-extension",
    "ai-product-extension",
    "mobile-product-extension",
    "bigdata-product-extension",
    "iot-embedded-extension",
    "payment-trading-extension",
    "low-level-systems-extension",
)

PRODUCT_OWNER = {
    "frontend-product": "frontend-change-builder",
    "backend-product": "backend-change-builder",
    "api-contract": "data-api-contract-changer",
    "data-model": "data-api-contract-changer",
    "database-migration": "data-api-contract-changer",
    "cache": "data-middleware-change-builder",
    "message-queue": "data-middleware-change-builder",
    "network-gateway": "reliability-observability-gate",
    "search-analytics": "data-middleware-change-builder",
    "external-integration": "integration-change-builder",
    "webhook": "integration-change-builder",
    "infrastructure-deployment": "delivery-release-gate",
    "kubernetes-helm": "delivery-release-gate",
    "ci-cd": "delivery-release-gate",
    "documentation-only": "change-documentation-gate",
    "git-workflow": "development-process-orchestrator",
    "skill-authoring": "change-forge-router",
    "agent-runtime-governance": "change-forge-router",
    "repository-intelligence": "change-impact-analyzer",
    "project-memory": "change-forge-router",
    "validation-broker": "quality-test-gate",
    "execution-trajectory": "ai-code-review-refactor",
    "sdk-library": "data-api-contract-changer",
    "cli-daemon": "backend-change-builder",
    "linux-systems": "reliability-observability-gate",
}

PRODUCT_SURFACE_SIGNALS = {
    "frontend-product": ("frontend", "component", "route", "form", "browser", "accessibility", "state"),
    "backend-product": ("backend", "service", "controller", "transaction", "background job", "auth"),
    "api-contract": (
        "api",
        "endpoint",
        "dto",
        "schema",
        "response",
        "request",
        "json schema",
        "protobuf",
        "yaml config",
        "xml",
        "toml",
        "parser compatibility",
        "serializer",
        "deserializer",
        "wire format",
        "schema registry",
        "field number",
        "duplicate key",
        "scalar coercion",
        "unknown field",
        "generated model",
        "golden fixture",
    ),
    "data-model": ("data model", "table", "column", "entity", "persistence", "database"),
    "database-migration": ("migration", "backfill", "rollback", "schema change", "irreversible data"),
    "cache": ("cache", "redis", "ttl", "invalidation", "stampede"),
    "message-queue": ("queue", "kafka", "consumer", "producer", "dlq", "offset", "dead letter"),
    "network-gateway": (
        "nginx",
        "envoy",
        "haproxy",
        "cloudflare",
        "cdn",
        "reverse proxy",
        "load balancer",
        "gateway",
        "ingress",
        "tls",
        "websocket",
        "grpc",
        "502",
        "503",
        "504",
        "timeout chain",
    ),
    "search-analytics": ("search", "analytics", "search index", "dashboard", "data freshness", "warehouse freshness"),
    "external-integration": ("third-party", "integration", "provider", "timeout", "retry"),
    "webhook": ("webhook", "hmac", "webhook signature", "webhook replay", "webhook idempotency", "provider event"),
    "infrastructure-deployment": (
        "deployment",
        "rollout",
        "container",
        "environment",
        "infrastructure",
        "发布",
        "部署",
    ),
    "kubernetes-helm": (
        "kubernetes",
        "k8s",
        "helm",
        "chart",
        "values.yaml",
        "ingress",
        "serviceaccount",
        "rbac",
    ),
    "ci-cd": (
        "ci",
        "cd",
        "workflow",
        "pipeline",
        "lockfile",
        "makefile",
        "bazel",
        "gradle",
        "maven",
        "build graph",
        "generated build artifact",
        "remote cache",
    ),
    "ai-rag-agent": ("ai", "llm", "rag", "agent", "embedding", "vector", "prompt", "model"),
    "web3": ("web3", "wallet", "eip-712", "smart contract", "blockchain", "on-chain"),
    "payment-trading": ("payment", "subscription", "billing", "trading", "ledger"),
    "low-level-systems": ("kernel", "driver", "ffi", "abi", "syscall", "memory safety"),
    "linux-systems": (
        "linux",
        "systemd",
        "journald",
        "cgroup",
        "namespace",
        "procfs",
        "signal handling",
        "ulimit",
        "service restart",
        "daemon",
        "pid 1",
    ),
    "sdk-library": ("sdk", "library", "client", "package", "public api"),
    "cli-daemon": ("cli", "daemon", "command", "stdout", "stderr", "exit code"),
    "documentation-only": ("documentation", "docs", "readme", "changelog", "runbook"),
    "git-workflow": (
        "merge conflict",
        "rebase conflict",
        "cherry-pick",
        "conflict",
        "dirty worktree",
        "stash",
        "branch naming",
        "commit message",
        "commit splitting",
        "staged diff",
        "unstaged diff",
        "backup branch",
        "generated file conflict",
        "lease-protected push",
        "signed tag",
        "release tag",
        "bisect",
        "reflog",
        "submodule",
    ),
    "skill-authoring": (
        "skill",
        "capability",
        "skill registry",
        "routing rule",
        "stage model",
        "hook runtime",
        "context control plane",
        "context budget",
        "reference bloat",
        "selected references",
        "skipped references",
    ),
    "agent-runtime-governance": (
        "executor adapter",
        "runtime adapter",
        "adapter capabilities",
        "normalized event",
        "closure contract",
        "unsupported runtime event",
    ),
    "repository-intelligence": (
        "repo graph",
        "symbol graph",
        "import graph",
        "call graph",
        "reference graph",
        "test graph",
        "context pack",
        "source of truth unknown",
    ),
    "project-memory": (
        "project memory",
        "repeat failure",
        "fragile file",
        "stale context",
        "previous fix failed",
        "latest commit review follow-up",
    ),
    "validation-broker": (
        "validation broker",
        "validation command selection",
        "stale validation",
        "validation without outcome",
        "affected tests",
        "changed path validation",
    ),
    "execution-trajectory": (
        "trajectory",
        "edit before read",
        "repair without re-review",
        "stop without residual risk",
        "skipped engineering stage",
    ),
}

DOMAIN_OWNER = {
    "ai-product-extension": "security-privacy-gate",
    "web3-product-extension": "security-privacy-gate",
    "payment-trading-extension": "security-privacy-gate",
    "low-level-systems-extension": "reliability-observability-gate",
    "mobile-product-extension": "quality-test-gate",
    "bigdata-product-extension": "data-middleware-change-builder",
    "iot-embedded-extension": "reliability-observability-gate",
}

SURFACE_CAPABILITIES = {
    "frontend-product": (
        "page-component-decomposition",
        "state-management-design",
        "form-validation-design",
        "frontend-api-integration",
    ),
    "backend-product": (
        "service-business-logic",
        "authentication-authorization",
        "idempotency-retry-design",
        "logging-error-handling",
    ),
    "api-contract": (
        "api-contract-design",
        "dto-schema-design",
        "error-code-design",
        "version-compatibility",
    ),
    "data-model": (
        "data-model-design",
        "relational-database",
        "indexing-query-optimization",
    ),
    "database-migration": (
        "data-migration-design",
        "transaction-consistency",
        "release-rollback",
    ),
    "cache": ("cache-design", "concurrency-control"),
    "message-queue": ("message-queue-design", "idempotency-retry-design"),
    "network-gateway": (
        "network-protocol-gateway-usage",
        "degradation-circuit-breaking",
        "observability",
    ),
    "search-analytics": ("search-analytics-design", "indexing-query-optimization"),
    "external-integration": (
        "degradation-circuit-breaking",
        "idempotency-retry-design",
    ),
    "webhook": ("authentication-security", "idempotency-retry-design"),
    "infrastructure-deployment": ("containerization", "release-rollback", "ci-cd"),
    "kubernetes-helm": ("kubernetes-gateway", "ci-cd", "secret-configuration-security"),
    "ci-cd": ("ci-cd", "package-dependency-management", "build-tool-professional-usage"),
    "ai-rag-agent": ("threat-modeling", "observability", "test-strategy"),
    "web3": ("authentication-security", "threat-modeling"),
    "payment-trading": ("idempotency-retry-design", "transaction-consistency"),
    "low-level-systems": ("concurrency-control", "language-performance-safety"),
    "linux-systems": ("linux-systems-professional-usage", "observability"),
    "sdk-library": ("sdk-library-contract-design", "version-compatibility", "package-dependency-management"),
    "cli-daemon": ("cli-daemon-interface-design", "logging-error-handling"),
    "documentation-only": ("documentation-generation",),
    "git-workflow": (
        "git-professional-usage",
        "repository-context-map",
        "validation-broker",
        "plan-execution-consistency",
        "agent-tool-permission-sandbox",
    ),
    "skill-authoring": (
        "repository-context-map",
        "skill-authoring-expert",
        "engineering-stage-professionalism",
        "skill-efficacy-benchmark",
        "plan-execution-consistency",
        "context-control-plane",
    ),
    "agent-runtime-governance": (
        "executor-adapter-protocol",
        "agent-tool-permission-sandbox",
        "agent-workflow-state-machine",
        "context-control-plane",
    ),
    "repository-intelligence": (
        "repository-graph-analysis",
        "repository-context-map",
        "context-packaging",
        "context-control-plane",
    ),
    "project-memory": (
        "project-memory-governance",
        "agent-execution-discipline",
        "plan-execution-consistency",
        "context-control-plane",
    ),
    "validation-broker": (
        "validation-broker",
        "repository-graph-analysis",
        "plan-execution-consistency",
        "context-control-plane",
    ),
    "execution-trajectory": (
        "execution-trajectory-analysis",
        "agent-workflow-state-machine",
        "validation-broker",
        "context-control-plane",
    ),
}

STAGE_CAPABILITIES = {
    "requirement-intake": (
        "requirement-clarification",
        "requirement-structuring",
        "non-goal-boundary-definition",
        "acceptance-standard-definition",
        "scenario-decomposition",
    ),
    "architecture-design": (
        "architecture-style-selection",
        "module-boundary-design",
        "layered-architecture-design",
        "architecture-tradeoff-analysis",
        "extensibility-design",
        "solution-optimality-evaluation",
    ),
    "implementation-planning": (
        "repository-context-map",
        "implementation-structure-design",
        "module-boundary-design",
        "code-clarity-maintainability",
        "language-idiom-enforcement",
    ),
    "coding": (
        "language-idiom-enforcement",
        "input-validation",
        "logging-error-handling",
    ),
    "debugging-diagnosis": ("failure-diagnosis", "agent-execution-discipline", "observability"),
    "bug-fix": ("agent-execution-discipline", "regression-testing", "code-review"),
    "code-review": (
        "code-review",
        "plan-execution-consistency",
        "implementation-structure-design",
        "code-clarity-maintainability",
        "language-idiom-enforcement",
    ),
    "refactoring": (
        "refactoring",
        "implementation-structure-design",
        "code-clarity-maintainability",
        "code-review",
        "regression-testing",
    ),
    "testing": (
        "test-strategy",
        "plan-execution-consistency",
        "language-testing-strategy",
        "test-data-management",
    ),
    "release-delivery": (
        "ci-cd",
        "release-rollback",
        "containerization",
        "kubernetes-gateway",
        "observability",
        "backup-recovery",
    ),
    "documentation-handoff": (
        "agent-workflow-state-machine",
        "plan-execution-consistency",
        "documentation-generation",
        "agent-execution-discipline",
    ),
    "skill-authoring": (
        "repository-context-map",
        "skill-authoring-expert",
        "skill-efficacy-benchmark",
        "documentation-generation",
        "agent-execution-discipline",
        "plan-execution-consistency",
    ),
}

STAGE_CONDITIONAL_CAPABILITIES = {
    "architecture-design": (
        "architecture-enforcement-tooling",
        "consumer-impact-analysis",
        "dependency-wiring-lifecycle",
        "minimal-correct-implementation",
    ),
    "debugging-diagnosis": (
        "data-format-contract-usage",
    ),
    "implementation-planning": (
        "code-element-professionalism",
        "testability-seam-design",
        "dependency-wiring-lifecycle",
        "algorithm-data-structure-selection",
        "failure-contract-design",
        "configuration-runtime-policy",
        "model-boundary-mapping",
        "data-format-contract-usage",
        "data-side-effect-flow-tracing",
        "cleanup-deletion-governance",
        "minimal-correct-implementation",
        "agent-workflow-state-machine",
        "repository-graph-analysis",
        "plan-execution-consistency",
    ),
    "coding": (
        "code-element-professionalism",
        "dependency-wiring-lifecycle",
        "algorithm-data-structure-selection",
        "failure-contract-design",
        "configuration-runtime-policy",
        "data-format-contract-usage",
        "data-side-effect-flow-tracing",
        "minimal-correct-implementation",
        "agent-tool-permission-sandbox",
        "agent-workflow-state-machine",
        "plan-execution-consistency",
    ),
    "bug-fix": (
        "code-element-professionalism",
        "data-format-contract-usage",
        "minimal-correct-implementation",
        "execution-trajectory-analysis",
        "project-memory-governance",
        "plan-execution-consistency",
        "agent-workflow-state-machine",
    ),
    "code-review": (
        "code-element-professionalism",
        "data-format-contract-usage",
        "minimal-correct-implementation",
        "agent-workflow-state-machine",
    ),
    "refactoring": (
        "code-element-professionalism",
        "testability-seam-design",
        "model-boundary-mapping",
        "data-side-effect-flow-tracing",
        "cleanup-deletion-governance",
        "minimal-correct-implementation",
    ),
    "testing": (
        "unit-testing",
        "integration-testing",
        "contract-testing",
        "e2e-testing",
        "regression-testing",
        "testability-seam-design",
        "code-element-professionalism",
        "algorithm-data-structure-selection",
        "failure-contract-design",
        "model-boundary-mapping",
        "data-side-effect-flow-tracing",
        "minimal-correct-implementation",
        "agent-workflow-state-machine",
        "validation-broker",
        "repository-graph-analysis",
    ),
    "release-delivery": (
        "configuration-runtime-policy",
        "agent-tool-permission-sandbox",
        "plan-execution-consistency",
        "architecture-enforcement-tooling",
        "consumer-impact-analysis",
        "cleanup-deletion-governance",
        "minimal-correct-implementation",
    ),
    "documentation-handoff": (
        "executor-adapter-protocol",
        "validation-broker",
        "execution-trajectory-analysis",
        "project-memory-governance",
    ),
    "skill-authoring": (
        "minimal-correct-implementation",
        "agent-workflow-state-machine",
        "executor-adapter-protocol",
        "repository-graph-analysis",
        "project-memory-governance",
        "validation-broker",
        "execution-trajectory-analysis",
        "context-control-plane",
    ),
}

CAPABILITY_TRIGGERS: dict[str, tuple[str, ...]] = {
    "agent-workflow-state-machine": (
        "agent workflow state machine",
        "current stage",
        "next stage",
        "legal transition",
        "repair re-review",
        "validation freshness",
        "stage manifest",
    ),
    "minimal-correct-implementation": (
        "minimal correct",
        "smallest correct",
        "simplest",
        "avoid overengineering",
        "delete shrink",
    ),
    "validation-broker": (
        "validation broker",
        "validation command selection",
        "stale validation",
        "validation without outcome",
        "changed path validation",
    ),
    "context-control-plane": (
        "context control plane",
        "context budget",
        "token overhead",
        "reference bloat",
        "selected references",
        "skipped references",
        "jit retrieval",
        "just in time retrieval",
        "graph as selector",
        "tool output boundary",
        "compaction snapshot",
        "branch route repair",
        "route repair summary",
        "output truncation",
        "over routing",
        "under routing",
    ),
    "code-element-professionalism": (
        "variable uninitialized",
        "uninitialized variable",
        "variable shadowing",
        "shadowed variable",
        "variable reused for unrelated purpose",
        "variable reuse",
        "sentinel null",
        "default sentinel",
        "mutable default",
        "null default",
        "none default",
        "nil default",
        "undefined default",
        "nullish",
        "truthiness",
        "falsey",
        "falsy",
        "hidden assignment",
        "assignment expression",
        "chained assignment",
        "mixed operator precedence",
        "operator precedence",
        "magic constant",
        "nested ternary",
        "complex conditional",
        "side effect expression",
        "side-effect expression",
        "empty loop",
        "empty branch",
        "empty catch",
        "no-op catch",
        "switch fallthrough",
        "fallthrough",
        "loop counter mutation",
        "missing resource cleanup",
        "broad try",
        "try scope too wide",
        "missing cleanup",
        "resource cleanup",
        "event before commit",
        "cache before commit",
        "external io before commit",
        "ignored return",
        "boolean trap",
        "side effect getter",
        "side-effect getter",
    ),
    "data-format-contract-usage": (
        "protobuf",
        "yaml config",
        "xml",
        "toml",
        "json schema",
        "parser compatibility",
        "serializer",
        "deserializer",
        "serialization",
        "wire format",
        "schema registry",
        "field number",
        "duplicate key",
        "scalar coercion",
        "unknown field",
        "generated model",
        "golden fixture",
        "storage format",
    ),
}

CAPABILITY_IDS = {
    "requirement-clarification": "01",
    "requirement-structuring": "02",
    "user-role-identification": "03",
    "scenario-decomposition": "04",
    "acceptance-standard-definition": "05",
    "non-goal-boundary-definition": "06",
    "information-architecture": "07",
    "user-flow-modeling": "08",
    "prototype-description": "09",
    "interaction-state-modeling": "10",
    "design-system-rules": "11",
    "domain-object-identification": "12",
    "business-rule-extraction": "13",
    "state-machine-modeling": "14",
    "use-case-modeling": "15",
    "permission-boundary-modeling": "16",
    "domain-event-modeling": "17",
    "architecture-style-selection": "18",
    "module-boundary-design": "19",
    "layered-architecture-design": "20",
    "microservice-splitting": "21",
    "event-driven-architecture": "22",
    "architecture-tradeoff-analysis": "23",
    "extensibility-design": "24",
    "data-model-design": "25",
    "api-contract-design": "26",
    "dto-schema-design": "27",
    "error-code-design": "28",
    "version-compatibility": "29",
    "data-migration-design": "30",
    "page-component-decomposition": "31",
    "routing-navigation-design": "32",
    "state-management-design": "33",
    "form-validation-design": "34",
    "frontend-api-integration": "35",
    "frontend-testing": "36",
    "controller-api-implementation": "37",
    "service-business-logic": "38",
    "domain-logic-implementation": "39",
    "repository-persistence": "40",
    "authentication-authorization": "41",
    "idempotency-retry-design": "42",
    "async-job-design": "43",
    "logging-error-handling": "44",
    "relational-database": "45",
    "nosql-database": "46",
    "indexing-query-optimization": "47",
    "transaction-consistency": "48",
    "cache-design": "49",
    "message-queue-design": "50",
    "search-analytics-design": "51",
    "threat-modeling": "52",
    "input-validation": "53",
    "web-security": "54",
    "authentication-security": "55",
    "secret-configuration-security": "56",
    "dependency-vulnerability-scanning": "57",
    "test-strategy": "58",
    "unit-testing": "59",
    "integration-testing": "60",
    "contract-testing": "61",
    "e2e-testing": "62",
    "test-data-management": "63",
    "regression-testing": "64",
    "performance-budgeting": "65",
    "profiling": "66",
    "concurrency-control": "67",
    "degradation-circuit-breaking": "68",
    "observability": "69",
    "backup-recovery": "70",
    "project-initialization": "71",
    "containerization": "72",
    "ci-cd": "73",
    "kubernetes-gateway": "74",
    "release-rollback": "75",
    "context-packaging": "76",
    "task-dag-decomposition": "77",
    "code-review": "78",
    "refactoring": "79",
    "documentation-generation": "80",
    "failure-diagnosis": "81",
    "solution-optimality-evaluation": "82",
    "technology-stack-selection": "83",
    "language-runtime-selection": "84",
    "language-idiom-enforcement": "85",
    "language-testing-strategy": "86",
    "language-performance-safety": "87",
    "package-dependency-management": "88",
    "go-professional-usage": "89",
    "java-jvm-professional-usage": "90",
    "typescript-professional-usage": "91",
    "python-professional-usage": "92",
    "rust-professional-usage": "93",
    "cpp-professional-usage": "94",
    "shell-cli-professional-usage": "95",
    "sql-professional-usage": "96",
    "sdk-library-contract-design": "97",
    "cli-daemon-interface-design": "98",
    "file-storage-processing": "99",
    "i18n-timezone-money-safety": "100",
    "implementation-structure-design": "101",
    "agent-execution-discipline": "102",
    "skill-authoring-expert": "103",
    "engineering-stage-professionalism": "104",
    "code-clarity-maintainability": "105",
    "design-pattern-selection": "106",
    "testability-seam-design": "107",
    "dependency-wiring-lifecycle": "108",
    "algorithm-data-structure-selection": "109",
    "failure-contract-design": "110",
    "configuration-runtime-policy": "111",
    "model-boundary-mapping": "112",
    "data-side-effect-flow-tracing": "113",
    "architecture-enforcement-tooling": "114",
    "consumer-impact-analysis": "115",
    "cleanup-deletion-governance": "116",
    "minimal-correct-implementation": "117",
    "repository-context-map": "118",
    "agent-workflow-state-machine": "119",
    "agent-tool-permission-sandbox": "120",
    "skill-efficacy-benchmark": "121",
    "plan-execution-consistency": "122",
    "executor-adapter-protocol": "123",
    "repository-graph-analysis": "124",
    "project-memory-governance": "125",
    "validation-broker": "126",
    "execution-trajectory-analysis": "127",
    "context-control-plane": "128",
    "code-element-professionalism": "129",
    "git-professional-usage": "130",
    "build-tool-professional-usage": "131",
    "linux-systems-professional-usage": "132",
    "network-protocol-gateway-usage": "133",
    "data-format-contract-usage": "134",
}


def _load_runtime_route_index() -> dict[str, Any]:
    index_path = Path(__file__).with_name(RUNTIME_ROUTE_INDEX_NAME)
    if not index_path.is_file():
        return {}
    try:
        data = json.loads(index_path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    if not isinstance(data, dict) or data.get("kind") != "changeforge.runtime_route_index":
        return {}
    return data


def _tuple_mapping(value: object, fallback: dict[str, tuple[str, ...]]) -> dict[str, tuple[str, ...]]:
    if not isinstance(value, dict):
        return fallback
    mapped: dict[str, tuple[str, ...]] = {}
    for key, items in value.items():
        if not isinstance(key, str) or not isinstance(items, list):
            return fallback
        if not all(isinstance(item, str) and item.strip() for item in items):
            return fallback
        mapped[key] = tuple(item.strip() for item in items)
    return mapped


def _merge_nonempty_tuple_mapping(
    value: object,
    fallback: dict[str, tuple[str, ...]],
) -> dict[str, tuple[str, ...]]:
    if not isinstance(value, dict):
        return fallback
    merged = dict(fallback)
    for key, items in value.items():
        if not isinstance(key, str) or not isinstance(items, list):
            return fallback
        if not all(isinstance(item, str) and item.strip() for item in items):
            return fallback
        cleaned = tuple(item.strip() for item in items)
        if cleaned:
            merged[key] = cleaned
    return merged


def _string_mapping(value: object, fallback: dict[str, str]) -> dict[str, str]:
    if not isinstance(value, dict):
        return fallback
    mapped: dict[str, str] = {}
    for key, item in value.items():
        if not isinstance(key, str) or not isinstance(item, str) or not item.strip():
            return fallback
        mapped[key] = item.strip()
    return mapped


def _string_tuple(value: object, fallback: tuple[str, ...]) -> tuple[str, ...]:
    if not isinstance(value, list):
        return fallback
    if not all(isinstance(item, str) and item.strip() for item in value):
        return fallback
    return tuple(item.strip() for item in value)


def _apply_runtime_route_index() -> None:
    index = _load_runtime_route_index()
    if not index:
        return
    global LANGUAGE_FILE_EXTENSIONS
    global LANGUAGE_CAPABILITIES
    global LANGUAGE_SURFACE_SIGNALS
    global PRODUCT_SURFACE_ORDER
    global PRODUCT_SURFACE_SIGNALS
    global DOMAIN_EXTENSION_BY_SURFACE
    global ALL_DOMAIN_EXTENSIONS
    global PRODUCT_OWNER
    global DOMAIN_OWNER
    global SURFACE_CAPABILITIES
    global STAGE_CAPABILITIES
    global STAGE_CONDITIONAL_CAPABILITIES
    global CAPABILITY_TRIGGERS
    global CAPABILITY_IDS

    LANGUAGE_FILE_EXTENSIONS = _tuple_mapping(
        index.get("language_file_extensions"),
        LANGUAGE_FILE_EXTENSIONS,
    )
    LANGUAGE_CAPABILITIES = _string_mapping(index.get("language_capabilities"), LANGUAGE_CAPABILITIES)
    LANGUAGE_SURFACE_SIGNALS = _tuple_mapping(
        index.get("language_surface_signals"),
        LANGUAGE_SURFACE_SIGNALS,
    )
    PRODUCT_SURFACE_ORDER = _string_tuple(index.get("product_surface_order"), PRODUCT_SURFACE_ORDER)
    PRODUCT_SURFACE_SIGNALS = _tuple_mapping(
        index.get("product_surface_signals"),
        PRODUCT_SURFACE_SIGNALS,
    )
    DOMAIN_EXTENSION_BY_SURFACE = _string_mapping(
        index.get("domain_extension_by_surface"),
        DOMAIN_EXTENSION_BY_SURFACE,
    )
    ALL_DOMAIN_EXTENSIONS = _string_tuple(index.get("all_domain_extensions"), ALL_DOMAIN_EXTENSIONS)
    PRODUCT_OWNER = _string_mapping(index.get("product_owner"), PRODUCT_OWNER)
    DOMAIN_OWNER = _string_mapping(index.get("domain_owner"), DOMAIN_OWNER)
    SURFACE_CAPABILITIES = _tuple_mapping(index.get("surface_capabilities"), SURFACE_CAPABILITIES)
    STAGE_CAPABILITIES = _tuple_mapping(index.get("stage_capabilities"), STAGE_CAPABILITIES)
    STAGE_CONDITIONAL_CAPABILITIES = _tuple_mapping(
        index.get("stage_conditional_capabilities"),
        STAGE_CONDITIONAL_CAPABILITIES,
    )
    CAPABILITY_TRIGGERS = _merge_nonempty_tuple_mapping(
        index.get("capability_triggers"),
        CAPABILITY_TRIGGERS,
    )
    CAPABILITY_IDS = _string_mapping(index.get("capability_ids"), CAPABILITY_IDS)


_apply_runtime_route_index()

NO_INJECTION_STAGES = {"question", "unknown", "no_engineering_action", "compaction"}


def detect_product_surfaces(paths: list[str], command: str = "", text: str = "") -> list[str]:
    evidence = _evidence(paths, command, text)
    surfaces: list[str] = []

    if _is_skill_authoring_evidence(paths, evidence):
        return ["skill-authoring"]

    if _docs_only(paths) or _text_docs_only(evidence):
        return ["documentation-only"]

    for surface in PRODUCT_SURFACE_ORDER:
        if _signals_match(evidence, PRODUCT_SURFACE_SIGNALS.get(surface, ())):
            surfaces.append(surface)

    if any(Path(path).suffix in {".tsx", ".jsx"} for path in paths):
        surfaces.append("frontend-product")
    if any(Path(path).suffix == ".sql" for path in paths) and "database-migration" not in surfaces:
        surfaces.append("data-model")

    ordered = [surface for surface in PRODUCT_SURFACE_ORDER if surface in set(surfaces)]
    if "database-migration" in ordered:
        ordered = ["database-migration", *(surface for surface in ordered if surface != "database-migration")]
    return ordered


def detect_language_surfaces(paths: list[str], command: str = "", text: str = "") -> list[str]:
    evidence = _evidence(paths, command, text)
    languages: list[str] = []
    for language, extensions in LANGUAGE_FILE_EXTENSIONS.items():
        if any(Path(path).suffix.casefold() in extensions for path in paths):
            languages.append(language)
            continue
        if _text_mentions_extension(evidence, extensions):
            languages.append(language)
            continue
        if _signals_match(evidence, LANGUAGE_SURFACE_SIGNALS.get(language, ())):
            languages.append(language)
    return _unique(languages)


def detect_conditional_capabilities(paths: list[str], command: str = "", text: str = "") -> list[str]:
    """Return conditional capability candidates detected from bounded route evidence."""
    evidence = _evidence(paths, command, text)
    conditionals = _unique(
        capability
        for capabilities in STAGE_CONDITIONAL_CAPABILITIES.values()
        for capability in capabilities
    )
    detected: list[str] = []
    for capability in conditionals:
        signals = CAPABILITY_TRIGGERS.get(capability) or _capability_name_signals(capability)
        if _signals_match(evidence, signals):
            detected.append(capability)
    return _unique(detected)


def detect_domain_extensions(paths: list[str], command: str = "", text: str = "") -> list[str]:
    evidence = _evidence(paths, command, text)
    surfaces = detect_product_surfaces(paths, command, text)
    extensions = [DOMAIN_EXTENSION_BY_SURFACE[surface] for surface in surfaces if surface in DOMAIN_EXTENSION_BY_SURFACE]
    if _matches_any(evidence, (r"\bandroid\b", r"\bios\b", r"\bmobile app\b", r"\bpush notification\b", r"\bapp store\b", r"\bdeep link\b")):
        extensions.append("mobile-product-extension")
    if _matches_any(evidence, (r"\bspark\b", r"\bpyspark\b", r"\bflink\b", r"\bstream\b", r"\bbatch\b", r"\betl\b", r"\blineage\b", r"\bfeature store\b", r"\bab test\b")):
        extensions.append("bigdata-product-extension")
    if _matches_any(evidence, (r"\bdevice\b", r"\bfirmware\b", r"\bembedded\b", r"\bsensor\b", r"\bactuator\b", r"\bota\b")):
        extensions.append("iot-embedded-extension")
    return _unique(extensions)


def detect_risk_surfaces(paths: list[str], command: str = "", text: str = "") -> list[str]:
    evidence = _evidence(paths, command, text)
    risks: list[str] = []
    if _is_skill_authoring_evidence(paths, evidence):
        # Skill bodies often discuss product contracts; do not treat that as a user API/data surface.
        if _matches_any(evidence, SECURITY_RISK_PATTERNS):
            risks.append("security")
        return _unique(risks)
    if _matches_any(evidence, SECURITY_RISK_PATTERNS):
        risks.append("security")
    if _matches_any(evidence, (r"\bmigration\b", r"\bschema\b", r"\bapi\b", r"\bdto\b", r"\bcontract\b", r"\bsql\b")):
        risks.append("data-api")
    if _matches_any(
        evidence,
        (
            r"\bperformance\b",
            r"\breliability\b",
            r"\bin production\b(?!\s+code)",
            r"\bproduction\s+(?:behavior|incident|outage|traffic|deployment|environment|risk|data|database|system|service)\b",
            r"\bconcurrency\b",
            r"\brace\b",
            r"\bdeadlock\b",
            r"\bobservability\b",
        ),
    ):
        risks.append("reliability")
    if _matches_any(evidence, (r"\brelease\b", r"\bdeploy\b", r"\bdeployment\b", r"\brollback\b", r"\bkubernetes\b", r"\bhelm\b", r"\bci\b", r"\bcd\b", r"发布", r"部署")):
        risks.append("delivery")
    if "documentation-only" in detect_product_surfaces(paths, command, text):
        risks.append("documentation")
    return _unique(risks)


def build_active_skill_context(
    *,
    runtime: str,
    stage: str,
    surfaces: list[str] | None = None,
    event_name: str,
    state: dict | None = None,
    classification: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a bounded active context from a hook classification."""
    classification = classification if isinstance(classification, dict) else {}
    state = state if isinstance(state, dict) else {}
    action_stage = stage or str(classification.get("stage") or "unknown")
    product_surfaces = _unique(
        classification.get("product_surfaces")
        or classification.get("surfaces")
        or surfaces
        or []
    )
    language_surfaces = _unique(classification.get("language_surfaces") or [])
    risk_surfaces = _unique(classification.get("risk_surfaces") or [])
    domain_extensions = _unique(
        classification.get("domain_extensions")
        or [DOMAIN_EXTENSION_BY_SURFACE[surface] for surface in product_surfaces if surface in DOMAIN_EXTENSION_BY_SURFACE]
    )
    current_stage = _canonical_stage(action_stage, product_surfaces, state)
    owner = _owner_skill(action_stage, current_stage, product_surfaces, risk_surfaces, domain_extensions)
    reviewer = _reviewer_skill(owner, current_stage, product_surfaces, risk_surfaces)
    capabilities = _selected_capabilities(
        action_stage,
        current_stage,
        product_surfaces,
        language_surfaces,
        risk_surfaces,
        domain_extensions,
        state,
        classification,
    )
    selected_skills = _selected_skills(owner, reviewer, product_surfaces, risk_surfaces)
    quality_gates = _quality_gates(current_stage, product_surfaces, risk_surfaces, selected_skills)
    raw_references = _required_references(capabilities)
    budget_mode = context_budget_mode(current_stage, risk_surfaces, product_surfaces, classification)
    references, skipped_references = apply_reference_budget(
        raw_references,
        budget_mode,
        always_keep=_always_keep_references(capabilities),
    )
    skipped_capabilities = _skipped_capabilities(capabilities, action_stage, current_stage)
    skipped_skills = _skipped_skills(selected_skills, product_surfaces, current_stage)
    skipped_routes = _skipped_routes(action_stage, current_stage)
    skipped_domain_extensions = _skipped_domain_extensions(domain_extensions)
    primary_surface = product_surfaces[0] if product_surfaces else "none"
    primary_language = language_surfaces[0] if language_surfaces else "none"
    context = {
        "runtime": runtime,
        "event": event_name,
        "stage": current_stage,
        "current_stage": current_stage,
        "action_stage": action_stage,
        "product_surfaces": product_surfaces,
        "language_surfaces": language_surfaces,
        "product_surface": primary_surface,
        "language_surface": primary_language,
        "risk_surfaces": risk_surfaces,
        "selected_skills": selected_skills,
        "selected_capabilities": capabilities,
        "selected_domain_extensions": domain_extensions,
        "required_quality_gates": quality_gates,
        "required_references": references,
        "raw_required_references": raw_references,
        "skipped_capabilities": skipped_capabilities,
        "skipped_references": skipped_references,
        "skipped_skills": skipped_skills,
        "skipped_routes": skipped_routes,
        "skipped_domain_extensions": skipped_domain_extensions,
        "context_budget_mode": budget_mode,
        "context_budget_rationale": _context_budget_rationale(
            budget_mode,
            current_stage,
            product_surfaces,
            risk_surfaces,
        ),
        "owner_skill": owner,
        "reviewer_skill": reviewer,
        "next_gate": quality_gates[0] if quality_gates else "quality-test-gate",
        "route_reason": _route_reason(current_stage, primary_surface, primary_language, domain_extensions),
        "primary_product_surface": primary_surface,
        "primary_language_surface": primary_language,
        "prior_stage": state.get("turn_stage", ""),
    }
    context["context_control"] = build_context_control_record(
        {**context, "required_references": raw_references},
        state,
        classification,
    )
    return context


def context_lines(context: dict[str, Any]) -> list[str]:
    """Render the active context as stable, line-oriented guidance."""
    def joined(name: str) -> str:
        values = context.get(name, [])
        return ", ".join(values) if isinstance(values, list) else str(values or "")

    lines = [
        "ChangeForge Professional Skill Injection",
        f"- current_stage: {context.get('current_stage', context.get('stage', ''))}",
        f"- action_stage: {context.get('action_stage', '')}",
        f"- owner_skill: {context.get('owner_skill', '')}",
        f"- reviewer_skill: {context.get('reviewer_skill', '')}",
        f"- product_surfaces: {joined('product_surfaces') or 'none'}",
        f"- language_surfaces: {joined('language_surfaces') or 'none'}",
        f"- risk_surfaces: {joined('risk_surfaces') or 'none'}",
        f"- selected_skills: {_summary_count(context, 'selected_skills')}",
        f"- selected_capabilities: {_summary_count(context, 'selected_capabilities')}",
        f"- selected_domain_extensions: {joined('selected_domain_extensions') or 'none'}",
        f"- required_quality_gates: {joined('required_quality_gates')}",
        "- privacy: prompt text, environment variables, secrets, and full command output are not stored",
    ]
    control = context.get("context_control") if isinstance(context.get("context_control"), dict) else {}
    if control:
        mode = str(control.get("budget_mode") or context.get("context_budget_mode") or "minimal")
        limits = context_budget_limits(mode)
        lines.append(f"- context_budget_mode: {mode}")
        lines.append(
            "- context_control: "
            f"selected_capabilities={control.get('selected_capability_count', len(_as_list(context.get('selected_capabilities'))))}/"
            f"{control.get('max_selected_capabilities', limits['max_selected_capabilities'])}, "
            f"required_references={control.get('selected_reference_count', len(_as_list(context.get('required_references'))))}/"
            f"{control.get('max_required_references', limits['max_required_references'])}, "
            f"skipped_references={control.get('skipped_reference_count', 0)}"
        )
    refs = context.get("required_references", [])
    if isinstance(refs, list) and refs:
        shown = refs[:4]
        more = len(refs) - len(shown)
        suffix = f", +{more} more" if more > 0 else ""
        lines.append(f"- required_references: {', '.join(shown)}{suffix}")
    skipped_refs = control.get("skipped_references") if isinstance(control, dict) else []
    if isinstance(skipped_refs, list) and skipped_refs:
        rendered = [
            str(item.get("reference") or "unknown")
            for item in skipped_refs[:2]
            if isinstance(item, dict)
        ]
        more = len(skipped_refs) - len(rendered)
        suffix = f"; +{more} more" if more > 0 else ""
        if rendered:
            lines.append(f"- skipped_references: {len(skipped_refs)} skipped; {'; '.join(rendered)}{suffix}")
    skipped = context.get("skipped_capabilities", [])
    if isinstance(skipped, list) and skipped:
        rendered = [
            f"{item.get('capability')}: {item.get('reason')}"
            for item in skipped[:4]
            if isinstance(item, dict)
        ]
        if rendered:
            lines.append(f"- skipped_capabilities: {'; '.join(rendered)}")
    skipped_skills = context.get("skipped_skills", [])
    if isinstance(skipped_skills, list) and skipped_skills:
        rendered = [
            f"{item.get('skill')}: {item.get('reason')}"
            for item in skipped_skills[:4]
            if isinstance(item, dict)
        ]
        if rendered:
            lines.append(f"- skipped_skills: {'; '.join(rendered)}")
    skipped_routes = context.get("skipped_routes", [])
    if isinstance(skipped_routes, list) and skipped_routes:
        rendered = [
            f"{item.get('route')}: {item.get('reason')}"
            for item in skipped_routes[:4]
            if isinstance(item, dict)
        ]
        if rendered:
            lines.append(f"- skipped_routes: {'; '.join(rendered)}")
    lines.extend(_professional_focus_lines(context))
    return lines


def _summary_count(context: dict[str, Any], name: str) -> str:
    values = context.get(name, [])
    if not isinstance(values, list):
        return str(values or "")
    if len(values) <= 4:
        return ", ".join(str(value) for value in values)
    shown = ", ".join(str(value) for value in values[:3])
    return f"{len(values)} selected ({shown}, +{len(values) - 3} more)"


def _professional_focus_lines(context: dict[str, Any]) -> list[str]:
    """Return concise, route-derived implementation guidance for common risks."""
    capabilities = set(_as_list(context.get("selected_capabilities")))
    product_surfaces = set(_as_list(context.get("product_surfaces")))
    risk_surfaces = set(_as_list(context.get("risk_surfaces")))
    current_stage = str(context.get("current_stage") or context.get("stage") or "")

    lines: list[str] = []
    if "security" in risk_surfaces or {"input-validation", "web-security"} & capabilities:
        lines.append(
            "- security_focus: canonicalize before fetch, enforce allowlists, block private/metadata targets, recheck redirects, and redact secrets in errors/logs."
        )
    if "cache" in product_surfaces or "cache-design" in capabilities:
        lines.append(
            "- Reliability Gate: for Redis/cache stampede work, prove per-key coordination, bounded timeout, jittered TTL, degraded fallback, no live Redis/network dependency, and concurrent local tests before claiming completion."
        )
        lines.append(
            "- cache_focus: prove per-key coordination, TTL jitter, safe fallback, metrics, and concurrent fake-cache tests; no live Redis/network."
        )
    if (
        "implementation-structure-design" in capabilities
        or current_stage in {"implementation-planning", "refactoring", "code-review"}
    ):
        lines.append(
            "- structure_focus: keep public API tests, document object-method ownership/rejected alternatives, keep side effects in adapters, and keep helpers private."
        )
    if "code-element-professionalism" in capabilities:
        lines.append(
            "- code_element_focus: verify variable initialization/default semantics, expression truthiness/precedence/side effects, and statement cleanup/event-order behavior before approving local code."
        )
    return lines


def _as_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if isinstance(item, str)]


def _canonical_stage(action_stage: str, product_surfaces: list[str], state: dict[str, Any]) -> str:
    if action_stage in NO_INJECTION_STAGES:
        return "requirement-intake"
    if action_stage == "read":
        return "requirement-intake"
    if action_stage == "review":
        return "code-review"
    if action_stage == "refactor":
        return "refactoring"
    if action_stage == "test":
        return "testing"
    if action_stage == "release" or _has_any(product_surfaces, ("kubernetes-helm", "ci-cd", "infrastructure-deployment")):
        return "release-delivery"
    if action_stage == "skill_authoring" or "skill-authoring" in product_surfaces:
        return "skill-authoring"
    if "documentation-only" in product_surfaces:
        return "documentation-handoff"
    if action_stage == "repair":
        if state.get("repair_evidence_seen") or state.get("review_evidence_seen"):
            return "bug-fix"
        return "debugging-diagnosis"
    if action_stage == "edit":
        ready_for_code = bool(
            state.get("read_evidence_seen")
            and state.get("implementation_preflight_complete")
            and _test_plan_declared(state)
        )
        return "coding" if ready_for_code else "implementation-planning"
    if action_stage == "subagent":
        return "implementation-planning"
    if action_stage == "permission":
        return "release-delivery"
    return "requirement-intake"


def _owner_skill(
    action_stage: str,
    current_stage: str,
    product_surfaces: list[str],
    risk_surfaces: list[str],
    domain_extensions: list[str],
) -> str:
    if action_stage == "subagent":
        return "task-dag-planner"
    if current_stage == "requirement-intake" and action_stage == "read":
        return "change-impact-analyzer"
    if current_stage == "release-delivery":
        return "delivery-release-gate"
    if current_stage == "testing":
        return "quality-test-gate"
    if current_stage == "code-review":
        domain_owner = _domain_owner(domain_extensions)
        if domain_owner in {"security-privacy-gate", "reliability-observability-gate"}:
            return domain_owner
        if "security" in risk_surfaces:
            return "security-privacy-gate"
        if "reliability" in risk_surfaces:
            return "reliability-observability-gate"
        return "ai-code-review-refactor"
    if current_stage == "debugging-diagnosis":
        return "quality-test-gate"
    if current_stage == "refactoring":
        return "ai-code-review-refactor"
    if current_stage == "documentation-handoff":
        return "change-documentation-gate"
    if current_stage in {"implementation-planning", "coding", "bug-fix"}:
        for surface in product_surfaces:
            owner = PRODUCT_OWNER.get(surface)
            if owner:
                return owner
        if "security" in risk_surfaces:
            return "security-privacy-gate"
    domain_owner = _domain_owner(domain_extensions)
    if domain_owner:
        return domain_owner
    if "security" in risk_surfaces:
        return "security-privacy-gate"
    return "change-forge-router"


def _reviewer_skill(owner: str, current_stage: str, product_surfaces: list[str], risk_surfaces: list[str]) -> str:
    if owner == "quality-test-gate":
        return "ai-code-review-refactor"
    if owner == "security-privacy-gate":
        return "quality-test-gate"
    if owner == "change-documentation-gate":
        return "change-forge-router"
    if owner == "change-impact-analyzer":
        return "change-forge-router"
    if owner == "delivery-release-gate":
        return "quality-test-gate"
    if current_stage == "skill-authoring" and owner == "change-forge-router":
        return "quality-test-gate"
    if owner == "change-forge-router":
        return "change-impact-analyzer"
    if current_stage == "release-delivery" and owner != "delivery-release-gate":
        return "delivery-release-gate"
    if "security" in risk_surfaces and owner != "security-privacy-gate":
        return "security-privacy-gate"
    if current_stage in {"implementation-planning", "coding", "bug-fix", "refactoring"}:
        return "ai-code-review-refactor"
    return "quality-test-gate"


def _selected_skills(owner: str, reviewer: str, product_surfaces: list[str], risk_surfaces: list[str]) -> list[str]:
    skills = [owner, reviewer]
    for surface in product_surfaces:
        candidate = PRODUCT_OWNER.get(surface)
        if candidate:
            skills.append(candidate)
    if "security" in risk_surfaces:
        skills.append("security-privacy-gate")
    if "reliability" in risk_surfaces:
        skills.append("reliability-observability-gate")
    if "delivery" in risk_surfaces:
        skills.append("delivery-release-gate")
    if "documentation" in risk_surfaces:
        skills.append("change-documentation-gate")
    return _unique(skills)


def _selected_capabilities(
    action_stage: str,
    current_stage: str,
    product_surfaces: list[str],
    language_surfaces: list[str],
    risk_surfaces: list[str],
    domain_extensions: list[str],
    state: dict[str, Any] | None = None,
    classification: dict[str, Any] | None = None,
) -> list[str]:
    classification = classification or {}
    capabilities: list[str] = []
    if current_stage in STAGE_CAPABILITIES:
        capabilities.extend(STAGE_CAPABILITIES[current_stage])
    conditional_candidates = set(classification.get("conditional_capabilities") or [])
    for capability in STAGE_CONDITIONAL_CAPABILITIES.get(current_stage, ()):
        if capability in conditional_candidates:
            capabilities.append(capability)
    for surface in product_surfaces:
        surface_capabilities = SURFACE_CAPABILITIES.get(surface, ())
        if surface == "data-model" and "database-migration" in product_surfaces:
            surface_capabilities = tuple(
                capability
                for capability in surface_capabilities
                if capability != "data-model-design"
            )
        capabilities.extend(surface_capabilities)
    for language in language_surfaces:
        capability = LANGUAGE_CAPABILITIES.get(language)
        if capability and current_stage not in {"requirement-intake", "documentation-handoff", "release-delivery", "skill-authoring"}:
            capabilities.append(capability)
    if "security" in risk_surfaces and current_stage not in {"documentation-handoff", "skill-authoring"}:
        capabilities.append("threat-modeling")
    if "reliability" in risk_surfaces:
        capabilities.append("observability")
    if action_stage == "repair":
        capabilities.append("agent-execution-discipline")
    if domain_extensions and "low-level-systems-extension" in domain_extensions:
        capabilities.append("language-performance-safety")
    if _tool_permission_sandbox_required(
        action_stage,
        current_stage,
        product_surfaces,
        risk_surfaces,
        state or {},
        classification or {},
    ):
        capabilities.append("agent-tool-permission-sandbox")
    return _unique(capabilities)


def _tool_permission_sandbox_required(
    action_stage: str,
    current_stage: str,
    product_surfaces: list[str],
    risk_surfaces: list[str],
    state: dict[str, Any],
    classification: dict[str, Any],
) -> bool:
    """Return True when tool permission/sandbox evidence should be injected."""
    if action_stage == "permission":
        return True

    permission_keys = (
        "permission_gate_seen",
        "permission_decisions",
        "tool_permission_sandbox_seen",
        "command_risk_surfaces",
        "closure_risk_surfaces",
    )
    for key in permission_keys:
        if state.get(key):
            return True
        if classification.get(key):
            return True

    release_surfaces = (
        "database-migration",
        "infrastructure-deployment",
        "kubernetes-helm",
        "ci-cd",
    )
    if current_stage == "release-delivery" and (
        _has_any(product_surfaces, release_surfaces) or "delivery" in risk_surfaces
    ):
        return True

    return False


def _quality_gates(
    current_stage: str,
    product_surfaces: list[str],
    risk_surfaces: list[str],
    selected_skills: list[str],
) -> list[str]:
    gates: list[str] = []
    if current_stage in {"requirement-intake"}:
        gates.append("requirement gate")
    if current_stage in {"implementation-planning", "coding", "bug-fix", "code-review", "refactoring"}:
        gates.append("implementation gate")
    if current_stage in {"testing", "bug-fix", "refactoring"}:
        gates.append("test gate")
    if current_stage == "release-delivery":
        gates.append("delivery gate")
    if current_stage in {"documentation-handoff", "skill-authoring"}:
        gates.append("documentation gate")
    if "security" in risk_surfaces or "security-privacy-gate" in selected_skills:
        gates.append("security gate")
    if "reliability" in risk_surfaces or "reliability-observability-gate" in selected_skills:
        gates.append("reliability gate")
    if "delivery" in risk_surfaces or "delivery-release-gate" in selected_skills:
        gates.append("delivery gate")
    if "data-api" in risk_surfaces or _has_any(product_surfaces, ("api-contract", "data-model", "database-migration")):
        gates.append("API/data gate")
    if _has_any(product_surfaces, ("cache", "message-queue", "search-analytics")):
        gates.append("reliability gate")
    if "quality-test-gate" in selected_skills:
        gates.append("test gate")
    if "ai-code-review-refactor" in selected_skills and current_stage == "code-review":
        gates.append("AI review gate")
    return _unique(gates) or ["test gate"]


def _required_references(capabilities: list[str]) -> list[str]:
    refs = list(ROUTER_SELF_REFERENCES)
    for capability in capabilities:
        cap_id = CAPABILITY_IDS.get(capability)
        if cap_id:
            refs.append(f"references/capabilities/{cap_id}-{capability}.md")
    return _unique(refs)


def _always_keep_references(capabilities: list[str]) -> list[str]:
    refs = list(CONTEXT_CONTROL_ROUTER_REFERENCES)
    for capability in ("agent-tool-permission-sandbox", "context-control-plane"):
        if capability in capabilities:
            cap_id = CAPABILITY_IDS.get(capability)
            if cap_id:
                refs.append(f"references/capabilities/{cap_id}-{capability}.md")
    return _unique(refs)


def _skipped_capabilities(capabilities: list[str], action_stage: str, current_stage: str) -> list[dict[str, str]]:
    selected = set(capabilities)
    skipped: list[dict[str, str]] = []
    for capability, reason in (
        ("implementation-structure-design", "not a structure-changing action in the current canonical stage"),
        ("release-rollback", "not a release-delivery or migration rollout action"),
    ):
        if capability not in selected:
            skipped.append({"capability": capability, "reason": reason})
    return skipped


def _skipped_skills(
    selected_skills: list[str],
    product_surfaces: list[str],
    current_stage: str,
) -> list[dict[str, str]]:
    selected = set(selected_skills)
    skipped: list[dict[str, str]] = []
    if "backend-change-builder" not in selected and "backend-product" not in product_surfaces:
        skipped.append(
            {
                "skill": "backend-change-builder",
                "reason": "no backend product surface was detected",
            }
        )
    if "frontend-change-builder" not in selected and "frontend-product" not in product_surfaces:
        skipped.append(
            {
                "skill": "frontend-change-builder",
                "reason": "no frontend product surface was detected",
            }
        )
    if (
        "delivery-release-gate" not in selected
        and current_stage != "release-delivery"
        and not _has_any(product_surfaces, ("kubernetes-helm", "ci-cd", "infrastructure-deployment"))
    ):
        skipped.append(
            {
                "skill": "delivery-release-gate",
                "reason": "not a release-delivery or deployment surface",
            }
        )
    return skipped


def _skipped_routes(action_stage: str, current_stage: str) -> list[dict[str, str]]:
    if action_stage in {"read", "test", "review"} or current_stage not in {
        "implementation-planning",
        "coding",
        "bug-fix",
    }:
        return [
            {
                "route": "product-coding-owner",
                "reason": "current action is not an implementation owner stage",
            }
        ]
    return []


def _skipped_domain_extensions(selected: list[str]) -> list[dict[str, str]]:
    active = set(selected)
    return [
        {"extension": extension, "reason": "no matching domain signal in current paths or prompt"}
        for extension in ALL_DOMAIN_EXTENSIONS
        if extension not in active
    ]


def _route_reason(
    current_stage: str,
    primary_surface: str,
    primary_language: str,
    domain_extensions: list[str],
) -> str:
    domain = f", domain={','.join(domain_extensions)}" if domain_extensions else ""
    return (
        f"resolved from action evidence to canonical stage {current_stage}, "
        f"surface={primary_surface}, language={primary_language}{domain}"
    )


def _context_budget_rationale(
    mode: str,
    current_stage: str,
    product_surfaces: list[str],
    risk_surfaces: list[str],
) -> str:
    if mode == "minimal":
        return "minimal context budget for route without context-risk expansion"
    if mode == "single-stage":
        return f"single-stage budget for {current_stage} with bounded required references"
    surfaces = ", ".join(product_surfaces[:4]) or "no product surface"
    risks = ", ".join(risk_surfaces[:4]) or "no risk surface"
    return f"{mode} budget for {current_stage}; surfaces={surfaces}; risks={risks}"


def _domain_owner(domain_extensions: list[str]) -> str:
    for extension in domain_extensions:
        owner = DOMAIN_OWNER.get(extension)
        if owner:
            return owner
    return ""


def _test_plan_declared(state: dict[str, Any]) -> bool:
    if state.get("pre_edit_missing_test_plan") is False:
        return True
    if state.get("tdd_signal") or state.get("test_plan_declared"):
        return True
    summaries = state.get("implementation_preflights")
    if isinstance(summaries, list):
        return any(
            isinstance(summary, str)
            and re.search(r"\b(test_plan|tdd|validation_commands?)\b", summary, re.I)
            for summary in summaries
        )
    return False


def _docs_only(paths: list[str]) -> bool:
    if not paths:
        return False
    doc_suffixes = {".md", ".mdx", ".rst", ".adoc", ".txt"}
    doc_names = {"readme", "changelog", "contributing", "agents", "claude"}
    for path in paths:
        file_path = Path(path)
        lowered = path.casefold()
        if _is_skill_authoring_path(path):
            return False
        if lowered.startswith(("docs/", "documentation/")):
            continue
        if file_path.suffix.casefold() in doc_suffixes:
            continue
        if file_path.stem.casefold() in doc_names:
            continue
        return False
    return True


def _is_skill_authoring_evidence(paths: list[str], evidence: str) -> bool:
    return any(_is_skill_authoring_path(path) for path in paths) or _matches_any(
        evidence,
        SKILL_AUTHORING_TEXT_PATTERNS,
    )


def _is_skill_authoring_path(path: str) -> bool:
    lowered = path.replace("\\", "/").casefold()
    return (
        lowered.startswith(SKILL_AUTHORING_PREFIXES)
        or lowered.startswith(RUNTIME_AUTHORING_PREFIXES)
        or Path(lowered).name == "skill.md"
        or Path(lowered).name in {"routing-rules.yaml", "routing-rules.yml", "stage-model.yaml", "stage-model.yml"}
    )


def _text_docs_only(evidence: str) -> bool:
    return bool(DOCS_ONLY_TEXT_PATH_RE.search(evidence) and not CODE_TEXT_PATH_RE.search(evidence))


def _text_mentions_extension(evidence: str, extensions: tuple[str, ...]) -> bool:
    return any(
        re.search(rf"(?:^|[\s\"'`])[\w./-]+{re.escape(extension)}\b", evidence, re.I)
        for extension in extensions
    )


def _signals_match(evidence: str, signals: Iterable[str]) -> bool:
    return any(_signal_matches(evidence, signal) for signal in signals)


def _signal_matches(evidence: str, signal: str) -> bool:
    value = str(signal).strip()
    if not value:
        return False
    escaped = re.escape(value.casefold())
    separator_flexible = escaped.replace(r"\ ", r"[-_/.\s]+")
    pattern = rf"(?<![a-z0-9]){separator_flexible}s?(?![a-z0-9])"
    return bool(re.search(pattern, evidence, re.I))


def _capability_name_signals(capability: str) -> tuple[str, ...]:
    parts = [part for part in capability.split("-") if part not in {"design", "analysis"}]
    signals = [capability.replace("-", " ")]
    if len(parts) >= 2:
        signals.append(" ".join(parts[:2]))
    signals.extend(part for part in parts if len(part) > 4)
    return tuple(signals)


def _has_path_prefix(paths: Iterable[str], prefixes: tuple[str, ...]) -> bool:
    return any(str(path).casefold().startswith(prefix) for path in paths for prefix in prefixes)


def _matches_any(text: str, patterns: tuple[str, ...]) -> bool:
    return any(re.search(pattern, text, re.I) for pattern in patterns)


def _evidence(paths: list[str], command: str = "", text: str = "") -> str:
    parts = [*(path.replace("\\", "/") for path in paths), command, text]
    return "\n".join(part for part in parts if isinstance(part, str)).casefold()


def _has_any(values: Iterable[str], candidates: tuple[str, ...]) -> bool:
    existing = set(values)
    return any(candidate in existing for candidate in candidates)


def _unique(values: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for value in values:
        if not isinstance(value, str):
            continue
        item = value.strip()
        if not item or item in seen:
            continue
        seen.add(item)
        out.append(item)
    return out


__all__ = [
    "CODE_FILE_EXTENSIONS",
    "LANGUAGE_FILE_EXTENSIONS",
    "PRODUCT_SURFACE_ORDER",
    "build_active_skill_context",
    "context_lines",
    "detect_conditional_capabilities",
    "detect_domain_extensions",
    "detect_language_surfaces",
    "detect_product_surfaces",
    "detect_risk_surfaces",
]

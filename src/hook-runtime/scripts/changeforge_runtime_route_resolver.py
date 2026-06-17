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

LANGUAGE_STRONG_PATTERNS = {
    "go": (
        re.compile(r"\bgolang\b", re.I),
        re.compile(r"\bgo\s+test\b", re.I),
        re.compile(r"\bgo\s+channel\b", re.I),
        re.compile(r"\bgoroutine\b", re.I),
    ),
    "typescript": (
        re.compile(r"\btypescript\b", re.I),
        re.compile(r"\btsx\b", re.I),
        re.compile(r"\breact\b|\bvue\b|\bsvelte\b", re.I),
    ),
    "python": (
        re.compile(r"\bpython\b", re.I),
        re.compile(r"\bpytest\b", re.I),
        re.compile(r"\basyncio\b", re.I),
    ),
    "java-jvm": (
        re.compile(r"\bjava\b|\bjvm\b|\bkotlin\b|\bspring\b", re.I),
    ),
    "rust": (
        re.compile(r"\brust\b|\bcargo\b|\bborrow checker\b|\blifetime\b", re.I),
    ),
    "cpp": (
        re.compile(r"\bc\+\+\b|\bcpp\b|\braii\b|\bundefined behavior\b", re.I),
        re.compile(r"\bc\s+abi\b|\bnative\s+c\b|\bnative\s+c\+\+\b", re.I),
        re.compile(r"\babi\b|\bffi\b|\bsanitizer\b", re.I),
    ),
    "shell": (
        re.compile(r"\bshell\b|\bbash\b|\bzsh\b|\bset -euo pipefail\b", re.I),
    ),
    "sql": (
        re.compile(r"\bsql\b|\bpostgres\b|\bmysql\b|\bsqlite\b", re.I),
    ),
}

PRODUCT_SURFACE_ORDER = (
    "frontend-product",
    "backend-product",
    "api-contract",
    "data-model",
    "database-migration",
    "cache",
    "message-queue",
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
    "sdk-library",
    "cli-daemon",
    "documentation-only",
    "skill-authoring",
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
    "search-analytics": "data-middleware-change-builder",
    "external-integration": "integration-change-builder",
    "webhook": "integration-change-builder",
    "infrastructure-deployment": "delivery-release-gate",
    "kubernetes-helm": "delivery-release-gate",
    "ci-cd": "delivery-release-gate",
    "documentation-only": "change-documentation-gate",
    "skill-authoring": "change-forge-router",
    "sdk-library": "data-api-contract-changer",
    "cli-daemon": "backend-change-builder",
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
    "search-analytics": ("search-analytics-design", "indexing-query-optimization"),
    "external-integration": (
        "degradation-circuit-breaking",
        "idempotency-retry-design",
    ),
    "webhook": ("authentication-security", "idempotency-retry-design"),
    "infrastructure-deployment": ("containerization", "release-rollback", "ci-cd"),
    "kubernetes-helm": ("kubernetes-gateway", "ci-cd", "secret-configuration-security"),
    "ci-cd": ("ci-cd", "package-dependency-management"),
    "ai-rag-agent": ("threat-modeling", "observability", "test-strategy"),
    "web3": ("authentication-security", "threat-modeling"),
    "payment-trading": ("idempotency-retry-design", "transaction-consistency"),
    "low-level-systems": ("concurrency-control", "language-performance-safety"),
    "sdk-library": ("sdk-library-contract-design", "version-compatibility", "package-dependency-management"),
    "cli-daemon": ("cli-daemon-interface-design", "logging-error-handling"),
    "documentation-only": ("documentation-generation",),
    "skill-authoring": ("skill-authoring-expert", "engineering-stage-professionalism"),
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
        "implementation-structure-design",
        "module-boundary-design",
        "code-clarity-maintainability",
        "language-idiom-enforcement",
    ),
    "coding": ("language-idiom-enforcement", "input-validation", "logging-error-handling"),
    "debugging-diagnosis": ("failure-diagnosis", "agent-execution-discipline", "observability"),
    "bug-fix": ("agent-execution-discipline", "regression-testing", "code-review"),
    "code-review": (
        "code-review",
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
    "testing": ("test-strategy", "language-testing-strategy", "test-data-management"),
    "release-delivery": (
        "ci-cd",
        "release-rollback",
        "containerization",
        "kubernetes-gateway",
        "observability",
        "backup-recovery",
    ),
    "documentation-handoff": ("documentation-generation", "agent-execution-discipline"),
    "skill-authoring": (
        "skill-authoring-expert",
        "documentation-generation",
        "agent-execution-discipline",
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
    global PRODUCT_SURFACE_ORDER
    global DOMAIN_EXTENSION_BY_SURFACE
    global ALL_DOMAIN_EXTENSIONS
    global PRODUCT_OWNER
    global DOMAIN_OWNER
    global SURFACE_CAPABILITIES
    global STAGE_CAPABILITIES
    global CAPABILITY_IDS

    LANGUAGE_FILE_EXTENSIONS = _tuple_mapping(
        index.get("language_file_extensions"),
        LANGUAGE_FILE_EXTENSIONS,
    )
    LANGUAGE_CAPABILITIES = _string_mapping(index.get("language_capabilities"), LANGUAGE_CAPABILITIES)
    PRODUCT_SURFACE_ORDER = _string_tuple(index.get("product_surface_order"), PRODUCT_SURFACE_ORDER)
    DOMAIN_EXTENSION_BY_SURFACE = _string_mapping(
        index.get("domain_extension_by_surface"),
        DOMAIN_EXTENSION_BY_SURFACE,
    )
    ALL_DOMAIN_EXTENSIONS = _string_tuple(index.get("all_domain_extensions"), ALL_DOMAIN_EXTENSIONS)
    PRODUCT_OWNER = _string_mapping(index.get("product_owner"), PRODUCT_OWNER)
    DOMAIN_OWNER = _string_mapping(index.get("domain_owner"), DOMAIN_OWNER)
    SURFACE_CAPABILITIES = _tuple_mapping(index.get("surface_capabilities"), SURFACE_CAPABILITIES)
    STAGE_CAPABILITIES = _tuple_mapping(index.get("stage_capabilities"), STAGE_CAPABILITIES)
    CAPABILITY_IDS = _string_mapping(index.get("capability_ids"), CAPABILITY_IDS)


_apply_runtime_route_index()

NO_INJECTION_STAGES = {"question", "unknown", "no_engineering_action", "compaction"}


def detect_product_surfaces(paths: list[str], command: str = "", text: str = "") -> list[str]:
    evidence = _evidence(paths, command, text)
    surfaces: list[str] = []

    if _is_skill_authoring_evidence(paths, evidence):
        return ["skill-authoring"]

    if (_docs_only(paths) or _text_docs_only(evidence)) and not _matches_any(evidence, (r"\bapi\b", r"\bsecurity\b", r"\bmigration\b")):
        return ["documentation-only"]

    if _matches_any(evidence, (r"\bcomponents?/", r"\bpages?/", r"\broutes?/", r"\bapp/", r"\breact\b", r"\bvue\b", r"\bsvelte\b")) or any(Path(path).suffix in {".tsx", ".jsx"} for path in paths):
        surfaces.append("frontend-product")
    if _matches_any(evidence, (r"\bcontrollers?/", r"\bhandlers?/", r"\bservices?/", r"\busecases?/", r"\bworkers?/", r"\bjobs?/", r"\bvalidators?/", r"\bbackend\b", r"\bserver\b")):
        surfaces.append("backend-product")
    if _matches_any(evidence, (r"\bopenapi\b", r"\bgraphql\b", r"\bproto\b", r"\bdto\b", r"\brequest\b", r"\bresponse\b", r"\bcontract\b", r"\bapi\b")):
        surfaces.append("api-contract")
    if _matches_any(evidence, (r"\bmigrations?/", r"\bmigration\b", r"\bbackfill\b", r"\bschema change\b")):
        surfaces.append("database-migration")
    elif any(Path(path).suffix == ".sql" for path in paths) or _matches_any(evidence, (r"\bentity\b", r"\bpersistence\b", r"\bdatabase\b", r"\btable\b", r"\bcolumn\b")):
        surfaces.append("data-model")
    if _matches_any(evidence, (r"\bredis\b", r"\bmemcached\b", r"\bcache\b", r"\bttl\b", r"\binvalidation\b", r"\beviction\b")):
        surfaces.append("cache")
    if _matches_any(evidence, (r"\bkafka\b", r"\btopic\b", r"\bconsumer\b", r"\bproducer\b", r"\bdlq\b", r"\boffset\b", r"\breplay\b")):
        surfaces.append("message-queue")
    if _matches_any(evidence, (r"\bsearch\b", r"\banalytics\b", r"\bdashboard\b", r"\bwarehouse\b", r"\bfreshness\b", r"\bindex\b")):
        surfaces.append("search-analytics")
    if _matches_any(evidence, (r"\bwebhook\b", r"\bsignature\b.*\breplay\b", r"\bidempotency\b.*\bwebhook\b")):
        surfaces.append("webhook")
    if _matches_any(evidence, (r"\bthird[- ]party\b", r"\bintegrations?/", r"\bproviders?/", r"\badapters?/", r"\btimeout\b", r"\bretry\b")):
        surfaces.append("external-integration")
    if _matches_any(evidence, (r"\bdockerfile\b", r"\bdeployment\b", r"\bdeploy\b", r"\brollout\b", r"\bcontainer\b", r"\bterraform\b", r"\bpulumi\b", r"发布", r"部署")):
        surfaces.append("infrastructure-deployment")
    if _matches_any(evidence, (r"\bk8s\b", r"\bkubernetes\b", r"\bhelm\b", r"\bchart\.yaml\b", r"\bvalues\.ya?ml\b", r"\btemplates/", r"\bingress\b", r"\bserviceaccount\b", r"\brbac\b")):
        surfaces.append("kubernetes-helm")
    if _matches_any(evidence, (r"\b\.github/workflows/", r"\bworkflow\b", r"\bci\b", r"\bcd\b", r"\bpipeline\b", r"\blockfile\b", r"\bchart\.lock\b")):
        surfaces.append("ci-cd")
    if _matches_any(evidence, (r"\bllm\b", r"\brag\b", r"\bembedding\b", r"\bvector\b", r"\bprompt\b", r"\bmodel\b", r"\bagent\b")):
        surfaces.append("ai-rag-agent")
    if _matches_any(evidence, (r"\bweb3\b", r"\bwallet\b", r"\bsmart contract\b", r"\bblockchain\b", r"\bon[- ]chain\b", r"\beip-?712\b", r"\bnonce\b", r"\breorg\b", r"\bsolidity\b")):
        surfaces.append("web3")
    if _matches_any(evidence, (r"\bpayment\b", r"\bbilling\b", r"\bsubscription\b", r"\binvoice\b", r"\btrading\b", r"\bledger\b", r"\bsettlement\b", r"\bcheckout\b", r"\brefund\b", r"\bchargeback\b")):
        surfaces.append("payment-trading")
    if any(Path(path).suffix in LANGUAGE_FILE_EXTENSIONS["cpp"] for path in paths) or _matches_any(evidence, (r"\bkernel\b", r"\bdriver\b", r"\bffi\b", r"\babi\b", r"\bsyscall\b", r"\bmemory safety\b", r"\bnative performance\b", r"\braii\b", r"\bundefined behavior\b")):
        surfaces.append("low-level-systems")
    if _matches_any(evidence, (r"\bsdk\b", r"\bgenerated client\b", r"\bpublic client api\b", r"\bpackage\b", r"\bpublic api\b")):
        surfaces.append("sdk-library")
    if _matches_any(evidence, (r"\bcli\b", r"\bdaemon\b", r"\bstdout\b", r"\bstderr\b", r"\bexit code\b", r"\bdry[- ]run\b", r"\bsignal\b")):
        surfaces.append("cli-daemon")

    return [surface for surface in PRODUCT_SURFACE_ORDER if surface in set(surfaces)]


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
        if any(pattern.search(evidence) for pattern in LANGUAGE_STRONG_PATTERNS[language]):
            languages.append(language)
    return _unique(languages)


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
    )
    selected_skills = _selected_skills(owner, reviewer, product_surfaces, risk_surfaces)
    quality_gates = _quality_gates(current_stage, product_surfaces, risk_surfaces, selected_skills)
    references = _required_references(capabilities)
    skipped_capabilities = _skipped_capabilities(capabilities, action_stage, current_stage)
    skipped_skills = _skipped_skills(selected_skills, product_surfaces, current_stage)
    skipped_routes = _skipped_routes(action_stage, current_stage)
    skipped_domain_extensions = _skipped_domain_extensions(domain_extensions)
    primary_surface = product_surfaces[0] if product_surfaces else "none"
    primary_language = language_surfaces[0] if language_surfaces else "none"
    return {
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
        "skipped_capabilities": skipped_capabilities,
        "skipped_skills": skipped_skills,
        "skipped_routes": skipped_routes,
        "skipped_domain_extensions": skipped_domain_extensions,
        "owner_skill": owner,
        "reviewer_skill": reviewer,
        "next_gate": quality_gates[0] if quality_gates else "quality-test-gate",
        "route_reason": _route_reason(current_stage, primary_surface, primary_language, domain_extensions),
        "primary_product_surface": primary_surface,
        "primary_language_surface": primary_language,
        "prior_stage": state.get("turn_stage", ""),
    }


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
        f"- selected_skills: {joined('selected_skills')}",
        f"- selected_capabilities: {joined('selected_capabilities')}",
        f"- selected_domain_extensions: {joined('selected_domain_extensions') or 'none'}",
        f"- required_quality_gates: {joined('required_quality_gates')}",
        "- privacy: prompt text, environment variables, secrets, and full command output are not stored",
    ]
    refs = context.get("required_references", [])
    if isinstance(refs, list) and refs:
        lines.append(f"- required_references: {', '.join(refs[:8])}")
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
    return lines


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
) -> list[str]:
    capabilities: list[str] = []
    if current_stage in STAGE_CAPABILITIES:
        capabilities.extend(STAGE_CAPABILITIES[current_stage])
    for surface in product_surfaces:
        capabilities.extend(SURFACE_CAPABILITIES.get(surface, ()))
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
    return _unique(capabilities)


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
    "detect_domain_extensions",
    "detect_language_surfaces",
    "detect_product_surfaces",
    "detect_risk_surfaces",
]

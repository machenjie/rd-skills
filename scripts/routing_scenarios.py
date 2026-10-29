"""Source-owned expertise examples shared by routing and code-generation validation."""
from collections import Counter
from importlib import metadata as importlib_metadata
from pathlib import Path
import re
from typing import Any
from codegen_benchmark_manifest import EXPECTED_BENCHMARKS
from validation_utils import (
    ValidationProblem,
    load_yaml_file,
)

try:
    from markdown_it import MarkdownIt
except ImportError:
    MarkdownIt = None

EXPECTED_CODEGEN_CASE_IDS = {f"{category}/{case}" for category, cases in EXPECTED_BENCHMARKS.items() for case in cases}


def release_routing_scenario_errors(rows: list[dict[str, Any]]) -> list[str]:
    errors = []
    for field in ("id", "codegen_case_id"):
        values = [row.get(field) for row in rows]
        if any(not isinstance(value, str) or not value for value in values) or len(set(value for value in values if isinstance(value, str))) != len(values):
            errors.append(f"release routing {field} values must be unique non-empty identities")
    for row in rows:
        if not isinstance(row.get("codegen_case_id"), str) or row["codegen_case_id"] not in EXPECTED_CODEGEN_CASE_IDS:
            errors.append(f"{row.get('id')}: codegen case does not exist")
        router = row.get("router", {})
        expected = router.get("expected", {})
        if not router.get("trigger") or expected.get("profile") not in {"analysis-agent", "task-agent", "review-agent"} or not expected.get("primary"):
            errors.append(f"{row.get('id')}: missing expertise projection")
        for field in ("layer3",):
            selected = expected.get(field)
            if not isinstance(selected, list) or any(not isinstance(item, str) or not item for item in selected) or len(set(selected)) != len(selected):
                errors.append(f"{row.get('id')}: invalid Layer 3 selection")
        override = row.get("codegen_layer3", [])
        if not isinstance(override, list) or any(not isinstance(item, str) or not item for item in override) or len(set(override)) != len(override):
            errors.append(f"{row.get('id')}: invalid codegen Layer 3 selection")
    return errors


def load_release_routing_scenarios(path: Path) -> list[dict[str, Any]]:
    payload = load_yaml_file(path)
    rows = payload.get("scenarios") if isinstance(payload, dict) else None
    if not isinstance(rows, list) or not rows or payload.get("schema_version") != 2 or payload.get("kind") != "changeforge.release_routing_scenarios":
        raise ValidationProblem(f"{path}: invalid release routing examples")
    errors = release_routing_scenario_errors(rows)
    if errors:
        raise ValidationProblem(f"{path}: " + "; ".join(errors))
    return rows


def project_release_route_hints(scenario: dict[str, Any]) -> dict[str, Any]:
    expected = scenario["router"]["expected"]
    profile = expected["profile"]
    return {
        "work_path": "direct-task" if profile == "task-agent" else "review-only" if profile == "review-agent" else "diagnosis" if scenario["id"] == "diagnosis" else "analyzed-work",
        "agent_profile": profile,
        "primary_skill": expected["primary"],
        "layer3_skills": scenario.get("codegen_layer3", expected["layer3"]),
        "review_skill": expected["primary"] if profile == "review-agent" else None,
    }


# Authoring declarations, not a runtime router. Release rows retain their existing
# registry authority. The other Primary examples and Domain row groups are closed
# here and checked against the independent registries and oracle family contracts.
ROUTER_PATH = "src/control-skills/engineering-control-plane/references/professional-skill-router.md"
ROUTER_NON_DATA_LINE_BUDGET = 14
# Baseline 1b0892b2: reviewed cap 62 minus 34 Primary and 14 Domain rows.
# Inventory expansion adds declared data rows; it adds no prose allowance.
AUTHORING_PRIMARY_ROWS = (
    ('explicit standalone requirement clarification', 'analysis-agent', 'change-intake-compiler', 'ai-code-review-refactor'),
    ('explicit standalone acceptance definition', 'analysis-agent', 'acceptance-criteria-builder', 'ai-code-review-refactor'),
    ('browser SPA PWA or frontend component implementation', 'task-agent', 'frontend-change-builder', 'ai-code-review-refactor'),
    ('installed mobile or desktop application implementation', 'task-agent', 'installed-client-change-builder', 'ai-code-review-refactor'),
    ('native runtime or local firmware implementation including timing repair', 'task-agent', 'backend-change-builder', 'ai-code-review-refactor'),
    ('infrastructure definition reusable module template or render implementation', 'task-agent', 'platform-infrastructure-change-builder', 'ai-code-review-refactor'),
    ('bounded repository-owned generator plugin harness internal CLI monorepo automation or maintenance utility source change', 'task-agent', 'repository-tooling-change-builder', 'ai-code-review-refactor'),
    ('repository bootstrap toolchain build configuration dependency or Git collaboration implementation', 'task-agent', 'repository-tooling-change-builder', 'ai-code-review-refactor'),
    ('independently distributed library SDK internals public CLI or developer tool implementation with fixed public contract', 'task-agent', 'library-tool-product-builder', 'ai-code-review-refactor'),
    ('external technical facts version compatibility options or feasibility (`technical-investigation`)', 'analysis-agent', 'engineering-change-analysis', 'architecture-impact-reviewer'),
    ('source-backed engineering question (`source-backed-answer`)', 'analysis-agent', 'engineering-change-analysis', 'architecture-impact-reviewer'),
    ('explicit dependency-planning request with established decisions', 'analysis-agent', 'task-dag-planner', 'engineering-artifact-review'),
    ('explicit user-flow or interaction analysis', 'analysis-agent', 'experience-impact-modeler', 'ai-code-review-refactor'),
    ('explicit domain-rule or invariant analysis', 'analysis-agent', 'domain-impact-modeler', 'architecture-impact-reviewer'),
    ('explicit module ownership architecture artifact or architecture tradeoff analysis', 'analysis-agent', 'architecture-impact-reviewer', 'architecture-impact-reviewer'),
    ('internal runtime component or external provider shared-contract or delivery-boundary implementation', 'task-agent', 'integration-change-builder', 'ai-code-review-refactor'),
    ('explicit test-data or test-strategy analysis', 'analysis-agent', 'quality-test-gate', 'quality-test-gate'),
    ('standalone test or validation-infrastructure implementation or current proof execution', 'task-agent', 'quality-test-gate', 'ai-code-review-refactor'),
    ('explicit analysis of a proved reachable trust, privilege, permission, privacy, credential, secret, or authentication-authorization boundary, including hardening or review', 'analysis-agent', 'security-privacy-gate', 'security-privacy-gate'),
    ('security implementation', 'task-agent', 'security-privacy-gate', 'security-privacy-gate'),
    ('reliability implementation', 'task-agent', 'reliability-observability-gate', 'reliability-observability-gate'),
    ('explicit reliability or observability analysis', 'analysis-agent', 'reliability-observability-gate', 'reliability-observability-gate'),
    ('active multi-responder incident command mitigation coordination communications or handoff', 'analysis-agent', 'incident-response-coordinator', 'reliability-observability-gate'),
    ('logging implementation', 'task-agent', 'logging-design-gate', 'logging-design-gate'),
    ('explicit release rollout or rollback plan analysis', 'analysis-agent', 'delivery-release-gate', 'delivery-release-gate'),
    ('documentation implementation', 'task-agent', 'change-documentation-gate', 'change-documentation-gate'),
    ('bounded fixed-commit or current-code snapshot audit', 'review-agent', 'ai-code-review-refactor', 'ai-code-review-refactor'),
)

DOMAIN_ROUTER_ROW_GROUPS = (
    ('bigdata-product-extension', ('stream-cdc-replay', 'distributed-batch-schema'), 'batch, stream, data lake, distributed compute, schema evolution, or high-volume pipeline with checkpoint, downstream, partition, consumer, or schema compatibility boundaries; excluding ordinary transactional persistence and large-table work without a distributed pipeline'),
    ('iot-embedded-extension', ('firmware-update-recovery', 'device-physical-runtime'), 'device, firmware, edge, protocol, sensor, actuator, physical safety, or constrained runtime with recovery, activation, physical safety, timing, or hardware boundaries; excluding ordinary cloud work and APIs without device or firmware behavior'),
    ('low-level-systems-extension', ('abi-ffi-memory', 'kernel-realtime-concurrency'), 'kernel, driver, C, C++, Rust, memory, ABI, real-time, or systems concurrency with ownership, resource, deadline, or platform boundaries; excluding work with no systems boundary and C++ or Rust without a native ABI, OS, or resource boundary'),
    ('android-platform-extension', ('platform-lifecycle-authority', 'accessibility-platform-authority'), 'Android application lifecycle or platform accessibility behavior with application lifecycle or accessibility behavior; excluding Web PWA backend infrastructure non-Android Kotlin-only or framework-only work without a confirmed Android target and store rollout signing authorization or release approval'),
    ('ios-ipados-platform-extension', ('platform-lifecycle-authority',), 'iOS/iPadOS with application lifecycle; excluding Web PWA backend infrastructure non-Apple-mobile Swift-only or framework-only work without a confirmed iOS/iPadOS target and store rollout signing authorization or release approval'),
    ('windows-platform-extension', ('application-identity-authority',), 'Windows packaged desktop application with application identity; excluding Web PWA generic backend infrastructure non-Windows C#-only PowerShell-only or framework-only work without a confirmed Windows target and release signing or rollout authorization'),
    ('windows-platform-extension', ('service-lifecycle-authority',), 'Windows service with service lifecycle; excluding Web PWA generic backend infrastructure non-Windows C#-only PowerShell-only or framework-only work without a confirmed Windows target and release signing or rollout authorization'),
    ('macos-platform-extension', ('platform-lifecycle-authority',), 'macOS installed application with application lifecycle; excluding Web PWA backend infrastructure non-macOS Swift-only or framework-only work without a confirmed macOS target and release signing notarization or rollout authorization'),
    ('linux-desktop-platform-extension', ('desktop-session-authority',), 'Linux graphical desktop with desktop session; excluding Linux server service runtime Web PWA backend infrastructure language-only or framework-only work without a confirmed Linux desktop target and distribution rollout authorization or independent review'),
    ('cross-platform-client-extension', ('shared-target-ownership',), 'shared installed client with concrete platform targets; excluding framework name without repository build release or published-artifact target evidence and unknown target language-only Web PWA backend infrastructure or release authorization'),
    ('cloud-platform-extension', ('cloud-account-authority',), 'cloud control plane with account authority; excluding unknown cloud scope provider-name-only local Kubernetes or generic backend work without cloud control-plane dependency and release authorization or production mutation'),
    ('payment-trading-extension', ('money-ledger-settlement', 'trading-order-execution'), 'payment, ledger, balance, settlement, trading, order, wallet, or money movement with accounting, reconciliation, fill, or settlement boundaries; excluding work with no monetary invariant and orders without funds, ledger, settlement, or execution state'),
    ('web3-product-extension', ('chain-custody-finality', 'contract-cross-chain'), 'blockchain, smart contract, wallet, key, chain transaction, or custody behavior with finality, recovery, authority, upgrade, or replay boundaries; excluding ordinary non-Web3 work and terminology without chain or custody behavior'),
    ('ai-product-extension', ('retrieval-data',), 'prompt, retrieval, embedding, ai data with permission, model context; excluding no ai surface and without a model decision'),
    ('ai-product-extension', ('agent-model-authority',), 'model with delegated authority, consequential; excluding no ai surface and without a model decision'),
    ('ai-product-extension', ('retrieval-quality',), 'rag with chunking, reranking, recall, grounded answer, retrieval quality, citation; excluding no ai surface and without a model decision'),
    ('ai-product-extension', ('inference-performance',), 'llm with prefill, decode, kv cache, continuous batching, ttft, time to first token, token latency; excluding no ai surface and without a model decision'),
    ('ai-product-extension', ('ml-training',), 'model training, ml training, training pipeline with data split, label leakage, checkpoint recovery, distributed sampling, gradient accumulation, mixed precision, resume; excluding no ai surface and without a model decision'),
    ('ai-product-extension', ('evaluation-evidence',), 'evaluation with judge calibration, dataset contamination, provider regression; excluding no ai surface and without a model decision'),
    ('saas-product-extension', ('subscription-entitlement',), 'saas subscription, entitlement, billing event, usage correction, seat limit with grace, renewal, cancellation, effective time, duplicate, reordered, plan change, reconciliation; excluding without a subscription lifecycle'),
    ('hosted-app-extension', ('host-lifecycle-capability',), 'browser extension, ide extension, mini program, mini-program, hosted application with manifest, message identity, background lifetime, host permission, activation, revocation, uninstall, host api; excluding without an extension host contract'),
    ('commerce-fulfillment-extension', ('inventory-order-fulfillment',), 'inventory reservation, fulfillment, fulfilment, shipment, return merchandise with reservation, oversell, expiration, compensation, partial, duplicate, reordered, return, reconciliation; excluding without order or inventory state'),
    ('realtime-media-extension', ('media-clock-quality',), 'webrtc, audio stream, video stream, media pipeline, realtime media with jitter, clock, timestamp, backpressure, latency, packet loss, av sync, a/v sync, keyframe; excluding without media timing'),
    ('game-simulation-extension', ('simulation-authority-time',), 'game simulation, game loop, game server, simulation tick, physics simulation with fixed timestep, authority, prediction, reconciliation, replay, rollback, deterministic, tick order; excluding without simulation state'),
    ('graphics-compute-extension', ('device-resource-execution',), 'webgpu, vulkan, metal, cuda, hip kernel, gpu, shader with device loss, synchronization, buffer layout, shader interface, resource lifetime, compile options, pipeline cache, command submission, memory visibility; excluding cpu-only computation and css-only rendering'),
    ('scientific-computing-extension', ('scientific-model-evidence',), 'scientific computation, scientific computing, scientific model, numerical simulation, scientific solver with units, dimensions, conditioning, convergence, uncertainty, discretization, conservation, error oracle; excluding without a scientific model'),
)


def contains_contract_atom(text: str, atom: str) -> bool:
    """Match one contract atom without accepting identifier substrings."""
    right = r"(?![a-z0-9+])" if atom == "c" else r"(?![a-z0-9])"
    return re.search(rf"(?<![a-z0-9]){re.escape(atom)}{right}", text.casefold()) is not None


def authoring_router_contract(
    release_rows: list[dict[str, Any]],
    professional: dict[str, dict[str, Any]],
    domain: dict[str, dict[str, Any]],
    domain_specs: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    """Bind the closed Markdown rows and budget to independent declarations."""
    errors = release_routing_scenario_errors(release_rows)
    if errors:
        raise ValidationProblem("; ".join(errors))
    primary_rows = [
        (row["router"]["trigger"], *(
            row["router"]["expected"][field]
            for field in ("profile", "primary", "review")
        ))
        for row in release_rows
    ] + list(AUTHORING_PRIMARY_ROWS)
    if len(set(primary_rows)) != len(primary_rows) or len({row[0] for row in primary_rows}) != len(primary_rows):
        errors.append("authoring Primary declarations contain duplicate rows or signals")
    for signal, profile, owner, review in primary_rows:
        entry = professional.get(owner, {})
        reviewer = professional.get(review, {})
        if entry.get("task_routable") is not True or profile not in entry.get("role_support", []):
            errors.append(f"authoring Primary declaration has an unauthorized owner/profile: {signal}")
        if reviewer.get("task_routable") is not True or "review-agent" not in reviewer.get("role_support", []):
            errors.append(f"authoring Primary declaration has an unauthorized Review owner: {signal}")

    expected_families = {(name, family) for name, spec in domain_specs.items() for family in spec["families"]}
    declared_families = [(name, family) for name, families, _signal in DOMAIN_ROUTER_ROW_GROUPS for family in families]
    if set(domain) != set(domain_specs):
        errors.append("authoring Domain declarations differ from Registry/oracle membership")
    if Counter(declared_families) != Counter({identity: 1 for identity in expected_families}):
        errors.append("authoring Domain row groups must cover every family exactly once")
    domain_rows = []
    for name, families, signal in DOMAIN_ROUTER_ROW_GROUPS:
        domain_rows.append((signal, name))
        if not families or name not in domain_specs:
            errors.append(f"authoring Domain group is empty or unknown: {name}")
            continue
        if signal.count("; excluding ") != 1:
            errors.append(f"authoring Domain group lacks its anti-trigger partition: {name}")
            continue
        positive, negative = signal.split("; excluding ")
        if positive.count(" with ") != 1:
            errors.append(f"authoring Domain group lacks its boundary partition: {name}")
            continue
        trigger, boundary = positive.split(" with ")
        spec = domain_specs[name]
        for family in families:
            contract = spec["families"].get(family)
            if contract is None:
                continue
            for field, text in (("trigger_atoms", trigger), ("boundary_atoms", boundary)):
                if any(not contains_contract_atom(text, str(atom).casefold()) for atom in contract[field]):
                    errors.append(f"authoring Domain group omits {family} {field}: {name}")
        if any(not contains_contract_atom(negative, str(atom).casefold()) for atom in spec["anti_atoms"]):
            errors.append(f"authoring Domain group omits anti-trigger atoms: {name}")
    if len(set(domain_rows)) != len(domain_rows):
        errors.append("authoring Domain declarations contain duplicate rows")
    for name, spec in domain_specs.items():
        entry = domain.get(name, {})
        if entry.get("routing_mode") != "modifier-only":
            errors.append(f"authoring Domain is not modifier-only: {name}")
        for field, registry_field in (("trigger_atoms", "trigger_signals"), ("boundary_atoms", "boundary_signals")):
            atoms = {str(atom).casefold() for family in spec["families"].values() for atom in family[field]}
            declared = {str(atom).casefold() for atom in entry.get(registry_field, [])}
            if atoms != declared:
                errors.append(f"authoring Domain Registry/oracle {field} differ: {name}")
        registry_anti = " ".join(entry.get("anti_trigger_signals", []))
        if any(not contains_contract_atom(registry_anti, str(atom).casefold()) for atom in spec["anti_atoms"]):
            errors.append(f"authoring Domain Registry omits anti-trigger atoms: {name}")
    if errors:
        raise ValidationProblem("; ".join(errors))
    return {
        "primary_rows": tuple(primary_rows),
        "domain_rows": tuple(domain_rows),
        "non_data_line_budget": ROUTER_NON_DATA_LINE_BUDGET,
        "line_limit": len(primary_rows) + len(domain_rows) + ROUTER_NON_DATA_LINE_BUDGET,
    }


def load_authoring_router_contract(root: Path) -> dict[str, Any]:
    # The oracle is a validation fixture owner, not an installed runtime router.
    from deterministic_route_oracle import DOMAIN_ROUTE_SPECS

    professional = load_yaml_file(root / "src/registry/professional-skills.yaml")
    domain = load_yaml_file(root / "src/registry/domain-skills.yaml")
    return authoring_router_contract(
        load_release_routing_scenarios(root / "src/registry/release-routing-scenarios.yaml"),
        {entry["name"]: entry for entry in professional["professional_skills"]},
        {entry["name"]: entry for entry in domain["domain_skills"]},
        DOMAIN_ROUTE_SPECS,
    )


ROUTER_MARKDOWN_VERSIONS = {"markdown-it-py": "4.2.0", "mdurl": "0.1.2"}
ROUTER_TABLE_HEADERS = (
    ("Task signal", "Start profile", "Primary Professional Skill", "Review expertise when selected"),
    ("Active mechanism", "Domain modifier"),
)


def authoring_router_rows(text: str) -> list[tuple[str, ...]]:
    """Bind top-level rows to their header, rendered width, and authored cells."""
    for distribution, expected in ROUTER_MARKDOWN_VERSIONS.items():
        try:
            actual = importlib_metadata.version(distribution)
        except importlib_metadata.PackageNotFoundError as exc:
            raise ValidationProblem(f"authoring router requires {distribution}=={expected}") from exc
        if actual != expected:
            raise ValidationProblem(f"authoring router requires {distribution}=={expected}; found {actual}")
    if MarkdownIt is None:
        raise ValidationProblem("authoring router requires markdown-it-py==4.2.0")
    tokens = MarkdownIt(
        "commonmark", {"html": True, "linkify": False, "typographer": False, "breaks": False}
    ).enable("table").parse(text)
    # A raw HTML container can hide a later table even across blank lines. The
    # closed router uses Markdown tables; only complete HTML comments are allowed.
    for token in tokens:
        for part in (token, *(token.children or [])):
            if part.type in {"html_block", "html_inline"} and re.sub(
                r"<!--.*?-->", "", part.content, flags=re.DOTALL
            ).strip():
                raise ValidationProblem("authoring router permits HTML only as complete comments")
    lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    rows = []
    header = None
    cells = None
    row_map = None
    for token in tokens:
        if token.type == "table_open" and token.level == 0:
            header = ()
            continue
        if token.type == "table_close" and token.level == 0:
            header = None
            cells = None
            continue
        if header is None:
            continue
        if token.type == "tr_open" and token.level == 2:
            cells = []
            row_map = token.map
            continue
        if token.type == "inline" and token.level == 4 and cells is not None:
            cells.append(token.content.strip())
        if token.type != "tr_close" or token.level != 2 or cells is None:
            continue
        if row_map is None or row_map[1] != row_map[0] + 1 or not lines[row_map[0]].startswith("|"):
            raise ValidationProblem("authoring router requires one physical pipe-delimited line per row")
        authored = tuple(cell.strip() for cell in lines[row_map[0]].strip("|").split("|"))
        projected = tuple(cells)
        cells = None
        if authored != projected:
            raise ValidationProblem("authoring router authored cells differ from rendered columns")
        if not header:
            if projected not in ROUTER_TABLE_HEADERS:
                raise ValidationProblem("authoring router table header is not declared")
            header = projected
        else:
            if len(projected) != len(header):
                raise ValidationProblem("authoring router row width differs from its declared header")
            rows.append(projected)
    return rows


def authoring_router_markdown_errors(text: str, contract: dict[str, Any]) -> list[str]:
    """Reject undeclared, missing, duplicate, or hidden rows before budgeting prose."""
    try:
        rows = authoring_router_rows(text)
    except ValidationProblem as exc:
        return [str(exc)]
    expected = Counter((*contract["primary_rows"], *contract["domain_rows"]))
    observed = Counter(rows)
    errors = []
    for label, difference in (("missing", expected - observed), ("extra or duplicate", observed - expected)):
        if difference:
            errors.append(f"authoring router {label} declared rows: {list(difference.elements())}")
    non_data_lines = len(text.splitlines()) - len(rows)
    if non_data_lines > contract["non_data_line_budget"]:
        errors.append(f"authoring router non-data lines {non_data_lines} exceed {contract['non_data_line_budget']}")
    return errors

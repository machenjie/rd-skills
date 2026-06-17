#!/usr/bin/env python3
"""Warn when post-edit paths should trigger ChangeForge structure discipline.

This gate runs after edit tools. It is intentionally lightweight: it inspects
changed paths, sibling file names, and patch text with simple heuristics. It does
not parse a full AST, does not call any model, does not access the network, and
does not modify project source. This post-tool gate is advisory and fails open
on any error.
"""

from __future__ import annotations

import re
from pathlib import Path

from changeforge_common import (
    compact_name,
    cwd_from_event,
    debug_log,
    detect_runtime,
    emit_block,
    emit_warning,
    event_name,
    extract_changed_paths,
    hook_mode,
    is_post_tool_use,
    load_state,
    merge_state,
    normalize_path,
    read_event,
    repo_root,
    session_id_from_event,
    tool_name,
    write_telemetry_event,
)
from changeforge_runtime_route_resolver import CODE_FILE_EXTENSIONS


# Compacted (lowercase, alphanumeric-only) edit tool names across runtimes:
# Codex/Claude (edit, write, multiedit, apply_patch) and VS Code Copilot
# (editFiles, createFile/create_file, replace_string_in_file,
# insert_edit_into_file, multi_replace_string_in_file).
EDIT_TOOLS = {
    "edit",
    "write",
    "multiedit",
    "applypatch",
    "editfiles",
    "createfile",
    "replacestringinfile",
    "inserteditintofile",
    "multireplacestringinfile",
}
STRUCTURE_PATH_HINTS = [
    "/service/",
    "/services/",
    "/repository/",
    "/repositories/",
    "/adapter/",
    "/adapters/",
    "/client/",
    "/clients/",
    "/helper/",
    "/helpers/",
    "/utils/",
    "/common/",
    "/shared/",
    "/domain/",
    "/model/",
    "/models/",
]
DEPENDENCY_FILES = [
    "package.json",
    "pnpm-lock.yaml",
    "yarn.lock",
    "go.mod",
    "go.sum",
    "pyproject.toml",
    "requirements.txt",
    "Cargo.toml",
    "Cargo.lock",
    "pom.xml",
    "build.gradle",
]
STRUCTURAL_ROLE_HINTS = {
    "service",
    "services",
    "repository",
    "repositories",
    "adapter",
    "adapters",
    "client",
    "clients",
    "helper",
    "helpers",
    "parser",
    "parsers",
    "mapper",
    "mappers",
    "validator",
    "validators",
}
PUBLIC_INTERFACE_HINTS = {
    "api",
    "apis",
    "contract",
    "contracts",
    "interface",
    "interfaces",
    "sdk",
    "client",
    "clients",
    "adapter",
    "adapters",
}

# Roles that should trigger a reuse-ladder reminder before new structure lands.
REUSE_KEYWORDS = {
    "helper",
    "helpers",
    "util",
    "utils",
    "common",
    "shared",
    "service",
    "services",
    "repository",
    "repositories",
    "adapter",
    "adapters",
    "client",
    "clients",
    "parser",
    "parsers",
    "mapper",
    "mappers",
    "validator",
    "validators",
    "manager",
    "processor",
    "handler",
    "factory",
    "strategy",
    "interface",
}

# Advanced-structure keywords detected in new file names (token form).
ADVANCED_REFACTOR_NAME_KEYWORDS = {
    "interface",
    "abstract",
    "factory",
    "strategy",
    "reflection",
    "metadata",
    "decorator",
    "annotation",
    "protocol",
    "trait",
    "generic",
    "template",
}

# Advanced-structure keywords detected in added code lines.
ADVANCED_REFACTOR_PATTERNS = [
    (re.compile(r"\bclass\s+[A-Za-z_]"), "class"),
    (re.compile(r"\binterface\s+[A-Za-z_]"), "interface"),
    (re.compile(r"\babstract\b"), "abstract"),
    (re.compile(r"\bextends\b"), "inheritance (extends)"),
    (re.compile(r"\bimplements\b"), "interface (implements)"),
    (re.compile(r"\binheritance\b"), "inheritance"),
    (re.compile(r"\bsubclass(es|ing)?\b"), "subclass"),
    (re.compile(r"\b(reflection|reflect|getattr|setattr|metaclass)\b"), "reflection"),
    (re.compile(r"\bmetadata\b"), "metadata dispatch"),
    (re.compile(r"\b(decorator|annotation)\b"), "decorator/annotation"),
    (re.compile(r"\bfactory\b", re.IGNORECASE), "factory"),
    (re.compile(r"\bstrateg(y|ies)\b", re.IGNORECASE), "strategy"),
    (re.compile(r"\bpolymorph"), "polymorphism"),
    (re.compile(r"\bprotocol\b"), "protocol"),
    (re.compile(r"\btrait\b"), "trait"),
    (re.compile(r"\bgeneric\b", re.IGNORECASE), "generic"),
    (re.compile(r"\btemplate\s*<"), "template"),
]

# Complex internal logic that usually deserves a concise intent comment.
COMPLEX_LOGIC_KEYWORDS = (
    "retry",
    "fallback",
    "compatibility",
    "migration",
    "transaction",
    "lock",
    "mutex",
    "goroutine",
    "async",
    "cache",
    "idempotent",
    "idempotency",
    "permission",
    "auth",
    "security",
    "state transition",
    "rate limit",
    "backoff",
    "circuit breaker",
    "dedupe",
    "deduplication",
    "reconcile",
)

# Patch heuristics that mean existing logic is being extended in place.
EXTENSION_SIGNAL_PATTERNS = [
    (re.compile(r"(^|\s)case\s+\S"), "new switch/case branch"),
    (re.compile(r"\bswitch\b"), "new switch branch"),
    (re.compile(r"\belse\s+if\b|\belif\b"), "new conditional branch"),
    (re.compile(r"\bfallback\b", re.IGNORECASE), "new fallback path"),
    (
        re.compile(r"\b(backward|backwards|compat|compatibility|legacy|deprecat)\w*", re.IGNORECASE),
        "compatibility/legacy branch",
    ),
    (
        re.compile(r"\b(mode|kind|strategy|variant|flavor)\b", re.IGNORECASE),
        "mode/kind/strategy parameter or branch",
    ),
]
DEF_LINE_RE = re.compile(
    r"\b(def|func|function|fn)\s+\w+\s*\(|\b(public|private|protected)\b[^;{]*\w+\s*\("
)

CODE_EXTENSIONS = CODE_FILE_EXTENSIONS
IGNORABLE_SUFFIXES = {
    ".pyc",
    ".pyo",
    ".o",
    ".obj",
    ".class",
    ".exe",
    ".dll",
    ".so",
    ".dylib",
    ".bin",
    ".lock",
    ".map",
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".svg",
    ".ico",
    ".pdf",
    ".zip",
    ".gz",
}
MIN_SIBLINGS_FOR_NAMING = 3
NEW_FILE_LINE_THRESHOLD = 180
ADDED_FUNCTION_THRESHOLD = 6
ADDED_ADVANCED_STRUCTURE_THRESHOLD = 4
PUBLIC_EXPORT_THRESHOLD = 4
BRANCH_SIGNAL_THRESHOLD = 8
PARAMETER_COUNT_THRESHOLD = 4

BUSINESS_TOKENS = {
    "account",
    "auth",
    "booking",
    "cancellation",
    "entitlement",
    "invoice",
    "ledger",
    "order",
    "payment",
    "permission",
    "refund",
    "shipping",
    "subscription",
    "tenant",
    "user",
}
BRANCH_TOKENS = {"if", "else", "elif", "switch", "case", "fallback", "mode", "kind", "strategy"}
WEAK_TYPE_RE = re.compile(
    r"\b(any|Object|Record\s*<\s*string\s*,\s*any\s*>|map\s*\[\s*string\s*\]\s*(interface\s*\{\}|any)|interface\s*\{\})\b"
)
BOOLEAN_PARAM_RE = re.compile(
    r"(:\s*bool(?:ean)?\b|\bbool(?:ean)?\s+\w+|\b\w+\s+bool\b|\bBoolean\s+\w+)"
)
FUNCTION_WITH_PARAMS_RE = re.compile(
    r"\b(?:def|func|function|fn)\s+\w+\s*\(([^)]*)\)|\b(?:public|private|protected)\b[^;{()]*\w+\s*\(([^)]*)\)"
)
CONSTRUCTOR_WITH_PARAMS_RE = re.compile(
    r"\bconstructor\s*\(([^)]*)\)|\b__init__\s*\(([^)]*)\)"
)
PUBLIC_EXPORT_RE = re.compile(r"^\s*(export\s+|pub\s+|public\s+)")
CLEANUP_SIGNAL_RE = re.compile(
    r"\b(todo|deprecated|deprecation|compat|compatibility|legacy|feature\s*flag|flagged|flag)\b",
    re.IGNORECASE,
)
CLEANUP_OWNER_EXPIRY_RE = re.compile(
    r"\b(owner|expiry|expires|expire|sunset|remove\s+by|removal|ticket|issue|until)\b",
    re.IGNORECASE,
)

# Per-language declaration patterns for the comment-quality reminder. Each entry
# matches an exported/public/test declaration that usually needs a doc comment.
GO_DECL_PATTERNS = [
    (re.compile(r"^\s*func\s+(Test|Benchmark|Example)\w*\s*\("), "test/benchmark function"),
    (re.compile(r"^\s*func\s+\([^)]*\)\s+[A-Z]\w*\s*"), "exported method"),
    (re.compile(r"^\s*func\s+[A-Z]\w*\s*\("), "exported function"),
    (re.compile(r"^\s*type\s+[A-Z]\w*"), "exported type"),
    (re.compile(r"^\s*const\s+[A-Z]\w*"), "exported const"),
    (re.compile(r"^\s*var\s+[A-Z]\w*"), "exported var"),
]
TS_DECL_PATTERNS = [
    (re.compile(r"^\s*(export\s+)?(describe|it|test)\s*\("), "test declaration"),
    (re.compile(r"^\s*export\s+(default\s+)?(async\s+)?function\b"), "exported function"),
    (re.compile(r"^\s*export\s+(abstract\s+)?class\b"), "exported class"),
    (re.compile(r"^\s*export\s+interface\b"), "exported interface"),
    (re.compile(r"^\s*export\s+type\b"), "exported type"),
    (re.compile(r"^\s*export\s+(const|let|var)\b"), "exported binding"),
    (re.compile(r"^\s*export\s+default\b"), "exported default"),
]
PY_DECL_PATTERNS = [
    (re.compile(r"^\s*def\s+test_\w*\s*\("), "test function"),
    (re.compile(r"^\s*class\s+Test\w*"), "test class"),
    (re.compile(r"^def\s+(?!_)\w+\s*\("), "public function"),
    (re.compile(r"^class\s+(?!_)[A-Za-z]\w*"), "public class"),
]
JAVA_DECL_PATTERNS = [
    (re.compile(r"^\s*public\s+(abstract\s+|final\s+|static\s+)*(class|interface|enum)\b"), "public type"),
    (re.compile(r"^\s*public\s+[\w<>\[\],\s]+\s+\w+\s*\("), "public method"),
]
CPP_DECL_PATTERNS = [
    (re.compile(r"^\s*class\s+[A-Z]\w*"), "class"),
    (re.compile(r"^\s*struct\s+[A-Z]\w*"), "struct"),
    (re.compile(r"^\s*template\s*<"), "template"),
]
RUST_DECL_PATTERNS = [
    (re.compile(r"^\s*#\[test\]"), "test attribute"),
    (re.compile(r"^\s*pub\s+fn\b"), "public function"),
    (re.compile(r"^\s*pub\s+struct\b"), "public struct"),
    (re.compile(r"^\s*pub\s+enum\b"), "public enum"),
    (re.compile(r"^\s*pub\s+trait\b"), "public trait"),
]
COMMENT_PREFIXES = ("//", "#", "/*", "*", "///", "/**", '"""', "'''", "<!--")


def main() -> int:
    event = read_event()
    if not event:
        return 0
    runtime = detect_runtime(event)
    if runtime == "unknown":
        return 0
    mode = hook_mode()
    if mode == "off":
        return 0
    if not is_post_tool_use(event):
        return 0
    tool = compact_name(tool_name(event))
    if tool not in EDIT_TOOLS:
        return 0

    try:
        repo = repo_root(cwd_from_event(event))
        state_before = load_state(repo)
        paths = extract_changed_paths(event)
        if not paths:
            return 0
        added_paths = _added_paths(event)
        patch_text = _patch_text(event)
        added_by_file = _patch_file_added_lines(patch_text)

        structure_findings = _structure_findings(paths, tool, added_paths)
        file_naming_findings = _file_naming_findings(repo, added_paths, tool, paths)
        reuse_findings = _reuse_findings(paths, added_paths)
        extension_reuse_findings = _extension_reuse_findings(patch_text, added_paths, paths)
        advanced_refactor_findings = _advanced_refactor_findings(patch_text, added_paths)
        comment_findings = _comment_findings(added_by_file)
        structure_quality_findings = _structure_quality_findings(
            added_by_file,
            added_paths,
            paths,
        )

        any_findings = bool(
            structure_findings
            or file_naming_findings
            or reuse_findings
            or extension_reuse_findings
            or advanced_refactor_findings
            or comment_findings
            or structure_quality_findings
        )
        preflight_gap = bool(
            state_before.get("implementation_preflight_required")
            and not state_before.get("implementation_preflight_complete")
        )
        debug_log(
            repo,
            "structure gate runtime={runtime} event={event} tool={tool} paths={paths} "
            "naming={naming} reuse={reuse} extension={extension} advanced={advanced} comment={comment} quality={quality}".format(
                runtime=runtime,
                event=event_name(event),
                tool=tool_name(event),
                paths=paths,
                naming=file_naming_findings,
                reuse=reuse_findings,
                extension=extension_reuse_findings,
                advanced=advanced_refactor_findings,
                comment=comment_findings,
                quality=structure_quality_findings,
            ),
        )
        merge_state(
            repo,
            runtime,
            changed_paths=paths,
            structure_findings=structure_findings,
            file_naming_findings=file_naming_findings,
            reuse_findings=reuse_findings,
            extension_reuse_findings=extension_reuse_findings,
            advanced_refactor_findings=advanced_refactor_findings,
            comment_findings=comment_findings,
            structure_quality_findings=structure_quality_findings,
            edit_without_preflight_seen=preflight_gap,
            post_edit_confirmed_preflight_gap=preflight_gap,
            pre_edit_structure_findings=[
                "post-edit confirmed edit without implementation preflight"
            ]
            if preflight_gap
            else [],
            suggested_skills=_suggested_skills(any_findings),
            suggested_capabilities=_suggested_capabilities(
                structure_findings,
                file_naming_findings,
                reuse_findings,
                extension_reuse_findings,
                advanced_refactor_findings,
                comment_findings,
                structure_quality_findings,
            ),
            suggested_gates=["code-review"] if any_findings else [],
        )
        write_telemetry_event(
            repo,
            runtime=runtime,
            hook_name="post_edit_structure_gate",
            event_name=event_name(event),
            mode=mode,
            session_id=session_id_from_event(event),
            cwd=cwd_from_event(event),
            tool_name=tool_name(event),
            changed_paths=paths,
            added_paths=sorted(added_paths),
            hook_findings={
                "structure_findings": structure_findings,
                "file_naming_findings": file_naming_findings,
                "reuse_findings": reuse_findings,
                "extension_reuse_findings": extension_reuse_findings,
                "advanced_refactor_findings": advanced_refactor_findings,
                "comment_findings": comment_findings,
                "structure_quality_findings": structure_quality_findings,
            },
            suggested_skills=_suggested_skills(any_findings),
            suggested_capabilities=_suggested_capabilities(
                structure_findings,
                file_naming_findings,
                reuse_findings,
                extension_reuse_findings,
                advanced_refactor_findings,
                comment_findings,
                structure_quality_findings,
            ),
            suggested_gates=["code-review"] if any_findings else [],
            implementation_preflight_required=bool(
                state_before.get("implementation_preflight_required")
            ),
            implementation_preflight_seen=bool(state_before.get("implementation_preflight_seen")),
            implementation_preflight_complete=bool(
                state_before.get("implementation_preflight_complete")
            ),
            implementation_preflight_blocked=bool(
                state_before.get("implementation_preflight_blocked")
            ),
            edit_without_preflight_seen=preflight_gap,
            post_edit_confirmed_preflight_gap=preflight_gap,
        )
        if not any_findings or mode == "monitor":
            return 0
        message = _warning_message(
            structure_findings,
            file_naming_findings,
            reuse_findings,
            extension_reuse_findings,
            advanced_refactor_findings,
            comment_findings,
            structure_quality_findings,
        )
        if mode == "block":
            emit_block(runtime, event_name(event), message)
            return 0
        emit_warning(runtime, event_name(event), message)
        return 0
    except Exception as exc:
        emit_warning(
            runtime,
            event_name(event),
            f"ChangeForge Hook Runtime warning: structure gate failed open: {exc}",
        )
        return 0


def _structure_findings(paths: list[str], tool: str, added_paths: set[str]) -> list[str]:
    findings: list[str] = []
    for raw_path in paths:
        path = normalize_path(raw_path)
        normalized = f"/{path.casefold()}"
        name = Path(path).name
        parts = {part.casefold() for part in Path(path).parts}
        is_test_path = _is_test_or_fixture_path(path)

        reasons: list[str] = []
        if path in added_paths or tool == "write":
            if not is_test_path:
                reasons.append("new file")
        if name in DEPENDENCY_FILES:
            reasons.append("dependency or lockfile")
        if not is_test_path and any(hint in normalized for hint in STRUCTURE_PATH_HINTS):
            reasons.append("shared or structural path")
        if (
            not is_test_path
            and (path in added_paths or tool == "write")
            and parts.intersection(STRUCTURAL_ROLE_HINTS)
        ):
            reasons.append("new service/repository/adapter/client/helper/parser/mapper/validator")
        if not is_test_path and parts.intersection(PUBLIC_INTERFACE_HINTS):
            reasons.append("public interface, SDK, client, or adapter surface")

        if reasons:
            findings.append(f"{path}: {', '.join(_unique(reasons))}")
    return _unique(findings)


def _file_naming_findings(
    repo: Path,
    added_paths: set[str],
    tool: str,
    paths: list[str],
) -> list[str]:
    candidates: set[str] = set(added_paths)
    if tool == "write":
        candidates.update(normalize_path(path) for path in paths)
    findings: list[str] = []
    for path in sorted(candidates):
        finding = _check_file_naming(repo, path)
        if finding:
            findings.append(finding)
    return _unique(findings)


def _check_file_naming(repo: Path, path: str) -> str | None:
    file_path = Path(path)
    name = file_path.name
    if not name or _is_ignorable_file(name):
        return None
    suffix = file_path.suffix.casefold()
    stem = _case_stem(name)
    if not stem:
        return None
    parent_dir = repo / file_path.parent
    try:
        if not parent_dir.is_dir():
            return None
        entries = [entry.name for entry in parent_dir.iterdir() if entry.is_file()]
    except OSError:
        return None
    sibling_stems: list[str] = []
    sibling_names: list[str] = []
    for entry in entries:
        if entry == name or _is_ignorable_file(entry):
            continue
        if Path(entry).suffix.casefold() != suffix:
            continue
        sibling_stem = _case_stem(entry)
        if sibling_stem:
            sibling_stems.append(sibling_stem)
            sibling_names.append(entry)
    # Too few comparable siblings: do not make a strong naming judgment.
    if len(sibling_stems) < MIN_SIBLINGS_FOR_NAMING:
        return None
    mismatch = _naming_mismatch(stem, sibling_stems)
    if not mismatch:
        return None
    sample = ", ".join(sorted(sibling_names)[:4])
    return f"{path}: new filename '{name}' {mismatch}; sibling files: {sample}"


def _naming_mismatch(stem: str, sibling_stems: list[str]) -> str | None:
    target_upper = any(char.isupper() for char in stem)
    target_underscore = "_" in stem
    target_hyphen = "-" in stem
    total = len(sibling_stems)
    upper_siblings = sum(1 for sibling in sibling_stems if any(char.isupper() for char in sibling))
    underscore_siblings = sum(1 for sibling in sibling_stems if "_" in sibling)
    hyphen_siblings = sum(1 for sibling in sibling_stems if "-" in sibling)

    if target_upper and upper_siblings == 0:
        return "appears camelCase/PascalCase while sibling files use lowercase names"
    if not target_upper and upper_siblings == total:
        return "appears lowercase while sibling files use camelCase/PascalCase names"
    if target_hyphen and hyphen_siblings == 0 and underscore_siblings > 0:
        return "uses kebab-case while sibling files use snake_case"
    if target_underscore and underscore_siblings == 0 and hyphen_siblings > 0:
        return "uses snake_case while sibling files use kebab-case"
    return None


def _reuse_findings(paths: list[str], added_paths: set[str]) -> list[str]:
    findings: list[str] = []
    for raw in paths:
        path = normalize_path(raw)
        if not _is_code_file(path):
            continue
        if _is_test_or_fixture_path(path) and not BUSINESS_TOKENS.intersection(_path_tokens(path)):
            continue
        matched = sorted(REUSE_KEYWORDS.intersection(_path_tokens(path)))
        if matched:
            scope = "new file" if path in added_paths else "edited file"
            findings.append(f"{path}: {scope} touches reuse-sensitive role ({', '.join(matched)})")
    return _unique(findings)


def _extension_reuse_findings(
    patch_text: str,
    added_paths: set[str],
    paths: list[str],
) -> list[str]:
    if not patch_text:
        return []
    updated = [normalize_path(path) for path in paths if normalize_path(path) not in added_paths]
    if not updated:
        return []
    added = _added_lines(patch_text)
    removed = _removed_lines(patch_text)
    blob = "\n".join(added)
    signals: list[str] = []
    for pattern, label in EXTENSION_SIGNAL_PATTERNS:
        if pattern.search(blob):
            signals.append(label)
    if _signature_change(added, removed):
        signals.append("modified existing signature")
    signals = _unique(signals)
    if not signals:
        return []
    target = ", ".join(sorted(updated)[:4])
    return [f"{target}: existing logic extended ({', '.join(signals)})"]


def _advanced_refactor_findings(patch_text: str, added_paths: set[str]) -> list[str]:
    matched: list[str] = []
    for path in added_paths:
        for keyword in ADVANCED_REFACTOR_NAME_KEYWORDS.intersection(_path_tokens(path)):
            matched.append(keyword)
    for line in _added_lines(patch_text):
        for pattern, label in ADVANCED_REFACTOR_PATTERNS:
            if pattern.search(line):
                matched.append(label)
    matched = _unique(matched)
    if not matched:
        return []
    return [f"advanced structure keywords: {', '.join(sorted(matched))}"]


def _comment_findings(added_by_file: dict[str, list[str]]) -> list[str]:
    findings: list[str] = []
    for path, lines in added_by_file.items():
        if not _is_code_file(path):
            continue
        reasons: list[str] = []
        declaration = _declaration_signal(path, lines)
        if declaration:
            reasons.append(declaration)
        logic = _complex_logic_signal(lines)
        if logic:
            reasons.append(f"complex logic ({', '.join(logic)})")
        if reasons:
            findings.append(f"{path}: {', '.join(reasons)}")
    return _unique(findings)


def _structure_quality_findings(
    added_by_file: dict[str, list[str]],
    added_paths: set[str],
    paths: list[str],
) -> list[str]:
    findings: list[str] = []
    changed_paths = {normalize_path(path) for path in paths}
    for path in sorted(changed_paths):
        if not _is_code_file(path):
            continue
        lines = added_by_file.get(path, [])
        if not lines:
            continue
        is_test_path = _is_test_or_fixture_path(path)
        reasons: list[str] = []
        nonblank_count = sum(1 for line in lines if line.strip())
        if path in added_paths and nonblank_count > NEW_FILE_LINE_THRESHOLD:
            reasons.append(f"new file adds {nonblank_count} lines")

        function_count = sum(1 for line in lines if DEF_LINE_RE.search(line))
        if not is_test_path and function_count > ADDED_FUNCTION_THRESHOLD:
            reasons.append(f"adds {function_count} functions")

        advanced_count = _advanced_structure_count(lines)
        if not is_test_path and advanced_count > ADDED_ADVANCED_STRUCTURE_THRESHOLD:
            reasons.append(f"adds {advanced_count} class/interface/factory/strategy signals")

        signature_reasons = _signature_quality_reasons(lines)
        reasons.extend(signature_reasons)

        public_exports = sum(1 for line in lines if PUBLIC_EXPORT_RE.search(line))
        if not is_test_path and public_exports > PUBLIC_EXPORT_THRESHOLD:
            reasons.append(f"adds {public_exports} public exports")

        branch_count = _branch_signal_count(lines)
        if not is_test_path and branch_count > BRANCH_SIGNAL_THRESHOLD:
            reasons.append(f"adds {branch_count} branch/mode/fallback signals")

        if _shared_path_with_business_terms(path, lines):
            reasons.append("shared/common/utils contains business vocabulary")

        cleanup_lines = [
            line.strip()
            for line in lines
            if CLEANUP_SIGNAL_RE.search(line) and not CLEANUP_OWNER_EXPIRY_RE.search(line)
        ]
        if cleanup_lines:
            reasons.append("cleanup/deprecation/feature flag signal lacks owner or expiry")

        role_tokens = sorted({"manager", "processor", "helper", "util", "common", "shared"}.intersection(_path_tokens(path)))
        if role_tokens and not is_test_path:
            reasons.append(f"filename uses broad role token ({', '.join(role_tokens)})")

        if reasons:
            findings.append(f"{path}: {', '.join(_unique(reasons))}")
    return _unique(findings)


def _advanced_structure_count(lines: list[str]) -> int:
    count = 0
    for line in lines:
        for pattern, _label in ADVANCED_REFACTOR_PATTERNS:
            if pattern.search(line):
                count += 1
    return count


def _signature_quality_reasons(lines: list[str]) -> list[str]:
    reasons: list[str] = []
    for line in lines:
        params = _parameter_lists(line)
        for param_list in params:
            parameter_count = _parameter_count(param_list)
            if parameter_count > PARAMETER_COUNT_THRESHOLD:
                reasons.append(f"signature has {parameter_count} parameters")
            if BOOLEAN_PARAM_RE.search(param_list):
                reasons.append("boolean parameter")
            if WEAK_TYPE_RE.search(param_list):
                reasons.append("weakly typed parameter bag")
    blob = "\n".join(lines)
    if WEAK_TYPE_RE.search(blob):
        reasons.append("weak type usage")
    return _unique(reasons)


def _parameter_lists(line: str) -> list[str]:
    params: list[str] = []
    for pattern in (FUNCTION_WITH_PARAMS_RE, CONSTRUCTOR_WITH_PARAMS_RE):
        for match in pattern.finditer(line):
            for group in match.groups():
                if group is not None:
                    params.append(group)
    return params


def _parameter_count(param_list: str) -> int:
    items = [
        item.strip()
        for item in param_list.split(",")
        if item.strip() and item.strip() not in {"self", "this"}
    ]
    return len(items)


def _branch_signal_count(lines: list[str]) -> int:
    count = 0
    for line in lines:
        for word in re.split(r"[^A-Za-z0-9]+", line):
            for piece in _split_camel(word):
                if piece and piece.casefold() in BRANCH_TOKENS:
                    count += 1
    return count


def _shared_path_with_business_terms(path: str, lines: list[str]) -> bool:
    path_tokens = _path_tokens(path)
    if not {"shared", "common", "utils", "util"}.intersection(path_tokens):
        return False
    return bool(BUSINESS_TOKENS.intersection(path_tokens | _code_tokens(lines)))


def _declaration_signal(path: str, lines: list[str]) -> str:
    patterns = _declaration_patterns_for(path)
    if not patterns:
        return ""
    labels: list[str] = []
    for index, line in enumerate(lines):
        for pattern, label in patterns:
            if pattern.search(line):
                if not _has_adjacent_comment(lines, index):
                    labels.append(label)
                break
    labels = _unique(labels)
    if not labels:
        return ""
    return "uncommented " + "/".join(labels)


def _declaration_patterns_for(path: str) -> list[tuple[re.Pattern[str], str]]:
    ext = Path(path).suffix.casefold()
    if ext == ".go":
        return GO_DECL_PATTERNS
    if ext in {".ts", ".tsx", ".js", ".jsx", ".mts", ".cts"}:
        return TS_DECL_PATTERNS
    if ext == ".py":
        return PY_DECL_PATTERNS
    if ext in {".java", ".kt", ".kts"}:
        return JAVA_DECL_PATTERNS
    if ext in {".cpp", ".cc", ".cxx", ".hpp", ".hh", ".h"}:
        return CPP_DECL_PATTERNS
    if ext == ".rs":
        return RUST_DECL_PATTERNS
    return []


def _has_adjacent_comment(lines: list[str], index: int) -> bool:
    # A doc comment may sit immediately before (Go/Rust/TS/Java) or immediately
    # after (Python docstring) the declaration line within the added block.
    for neighbor in (index - 1, index + 1):
        if 0 <= neighbor < len(lines) and _is_comment_or_doc(lines[neighbor]):
            return True
    return False


def _is_comment_or_doc(line: str) -> bool:
    stripped = line.strip()
    if not stripped:
        return False
    return stripped.startswith(COMMENT_PREFIXES)


def _complex_logic_signal(lines: list[str]) -> list[str]:
    blob = "\n".join(lines).casefold()
    tokens = _code_tokens(lines)
    hits: list[str] = []
    for keyword in COMPLEX_LOGIC_KEYWORDS:
        if " " in keyword:
            # Multi-word phrases are matched as substrings of the added text.
            if keyword in blob:
                hits.append(keyword)
        elif keyword in tokens:
            # Single-word keywords match an identifier token (camelCase and
            # snake_case are split) so `retryCount` matches but `block` does not
            # falsely match `lock`.
            hits.append(keyword)
    return hits


def _code_tokens(lines: list[str]) -> set[str]:
    tokens: set[str] = set()
    for line in lines:
        for word in re.split(r"[^A-Za-z0-9]+", line):
            for piece in _split_camel(word):
                if piece:
                    tokens.add(piece.casefold())
    return tokens


def _signature_change(added: list[str], removed: list[str]) -> bool:
    return any(DEF_LINE_RE.search(line) for line in added) and any(
        DEF_LINE_RE.search(line) for line in removed
    )


def _added_paths(event: dict) -> set[str]:
    paths: set[str] = set()

    def visit(value: object) -> None:
        if isinstance(value, dict):
            for child in value.values():
                visit(child)
            return
        if isinstance(value, list):
            for child in value:
                visit(child)
            return
        if isinstance(value, str) and "*** Begin Patch" in value:
            for line in value.splitlines():
                stripped = line.strip()
                prefix = "*** Add File:"
                if stripped.startswith(prefix):
                    paths.add(normalize_path(stripped[len(prefix) :].strip()))

    visit(event)
    return paths


def _patch_text(event: dict) -> str:
    chunks: list[str] = []

    def visit(value: object) -> None:
        if isinstance(value, dict):
            for child in value.values():
                visit(child)
            return
        if isinstance(value, list):
            for child in value:
                visit(child)
            return
        if isinstance(value, str) and (
            "*** Begin Patch" in value
            or "*** Add File:" in value
            or "*** Update File:" in value
            or "diff --git" in value
        ):
            chunks.append(value)

    visit(event)
    return "\n".join(chunks)


def _patch_file_added_lines(patch_text: str) -> dict[str, list[str]]:
    sections: dict[str, list[str]] = {}
    current: str | None = None
    if not patch_text:
        return sections
    for raw in patch_text.splitlines():
        stripped = raw.strip()
        apply_match = re.match(r"\*\*\* (?:Add|Update) File:\s+(.+)", stripped)
        if apply_match:
            current = normalize_path(apply_match.group(1))
            sections.setdefault(current, [])
            continue
        if stripped.startswith("*** Delete File:") or stripped in {"*** Begin Patch", "*** End Patch"}:
            current = None
            continue
        diff_match = re.match(r"diff --git a/(.+?) b/(.+)$", raw)
        if diff_match:
            current = normalize_path(diff_match.group(2))
            sections.setdefault(current, [])
            continue
        if raw.startswith("+++ "):
            candidate = raw[4:].strip()
            if candidate.startswith("b/"):
                candidate = candidate[2:]
            if candidate and candidate != "/dev/null":
                current = normalize_path(candidate)
                sections.setdefault(current, [])
            continue
        if raw.startswith("@@"):
            continue
        if raw.startswith("+") and not raw.startswith("+++"):
            if current is not None:
                sections[current].append(raw[1:])
    return sections


def _added_lines(patch_text: str) -> list[str]:
    return [
        raw[1:]
        for raw in patch_text.splitlines()
        if raw.startswith("+") and not raw.startswith("+++")
    ]


def _removed_lines(patch_text: str) -> list[str]:
    return [
        raw[1:]
        for raw in patch_text.splitlines()
        if raw.startswith("-") and not raw.startswith("---")
    ]


def _path_tokens(path: str) -> set[str]:
    tokens: set[str] = set()
    for part in re.split(r"[\\/]", path):
        if not part:
            continue
        stem = part.split(".")[0]
        for chunk in re.split(r"[_\-]", stem):
            for piece in _split_camel(chunk):
                if piece:
                    tokens.add(piece.casefold())
    return tokens


def _split_camel(token: str) -> list[str]:
    pieces = re.findall(r"[A-Z]+(?=[A-Z][a-z])|[A-Z]?[a-z]+|[A-Z]+|[0-9]+", token)
    return pieces or [token]


def _case_stem(name: str) -> str:
    stem = Path(name).stem
    if "." in stem:
        stem = stem.split(".", 1)[0]
    return stem


def _is_ignorable_file(name: str) -> bool:
    if name.startswith("."):
        return True
    if name.endswith(("~", ".tmp", ".bak", ".swp", ".orig")):
        return True
    return Path(name).suffix.casefold() in IGNORABLE_SUFFIXES


def _is_code_file(path: str) -> bool:
    return Path(path).suffix.casefold() in CODE_EXTENSIONS


def _is_test_or_fixture_path(path: str) -> bool:
    normalized = f"/{normalize_path(path).casefold()}"
    name = Path(path).name.casefold()
    tokens = _path_tokens(path)
    return bool(
        {"test", "tests", "fixture", "fixtures", "__tests__"}.intersection(tokens)
        or "/__tests__/" in normalized
        or name.endswith(("_test.go", ".test.ts", ".test.tsx", ".spec.ts", ".spec.tsx"))
    )


def _suggested_skills(any_findings: bool) -> list[str]:
    if not any_findings:
        return []
    return ["change-forge-router", "ai-code-review-refactor"]


def _suggested_capabilities(
    structure_findings: list[str],
    file_naming_findings: list[str],
    reuse_findings: list[str],
    extension_reuse_findings: list[str],
    advanced_refactor_findings: list[str],
    comment_findings: list[str],
    structure_quality_findings: list[str],
) -> list[str]:
    capabilities: list[str] = []
    if (
        structure_findings
        or file_naming_findings
        or reuse_findings
        or extension_reuse_findings
        or advanced_refactor_findings
        or structure_quality_findings
    ):
        capabilities.append("implementation-structure-design")
    if structure_quality_findings:
        capabilities.append("code-clarity-maintainability")
    if any("shared/common/utils" in finding for finding in structure_quality_findings):
        capabilities.append("module-boundary-design")
    if any("cleanup/deprecation/feature flag" in finding for finding in structure_quality_findings):
        capabilities.append("refactoring")
    if comment_findings or advanced_refactor_findings:
        capabilities.append("language-idiom-enforcement")
    if (
        structure_findings
        or file_naming_findings
        or reuse_findings
        or extension_reuse_findings
        or advanced_refactor_findings
        or comment_findings
        or structure_quality_findings
    ):
        capabilities.append("agent-execution-discipline")
    return _unique(capabilities)


def _warning_message(
    structure_findings: list[str],
    file_naming_findings: list[str],
    reuse_findings: list[str],
    extension_reuse_findings: list[str],
    advanced_refactor_findings: list[str],
    comment_findings: list[str],
    structure_quality_findings: list[str],
) -> str:
    sections: list[str] = []
    for title, findings in (
        ("structural paths", structure_findings),
        ("file naming findings", file_naming_findings),
        ("reuse findings", reuse_findings),
        ("extension reuse findings", extension_reuse_findings),
        ("advanced refactor findings", advanced_refactor_findings),
        ("comment findings", comment_findings),
        ("structure quality findings", structure_quality_findings),
    ):
        if findings:
            sections.append(_section(title, findings))
    detected = "\n".join(sections)
    return f"""ChangeForge Structure Gate triggered.

Detected:
{detected}

Before continuing, provide:
- reuse ladder record (direct reuse, extension reuse, composition/wrapper, extraction, new-code justification)
- file naming convention evidence (same-directory and parent-module naming scan, selected filename rationale, rejected alternatives)
- extension safety record (old behavior preserved, compatibility risk, old and new behavior tests)
- advanced refactor decision (object/function/module choice, class/interface/inheritance/reflection justification, public behavior tests)
- comment quality evidence (exported/public doc comments, complex-logic comments, non-trivial test comments, redundant comments removed)
- code clarity review (main flow, nested branches, signature traps, weak type bags, side-effect boundary, cleanup/deprecation owner and expiry)
- placement rationale, module ownership, and dependency direction
- same-pattern scan
- validation commands and results

Expected ChangeForge route:
- implementation-structure-design
- code-clarity-maintainability
- module-boundary-design when shared/common or directory boundary risk is present
- refactoring when cleanup, deprecation, feature flag, or compatibility branch risk is present
- agent-execution-discipline
- language-idiom-enforcement
- code-review
- ai-code-review-refactor when AI-generated implementation is material"""


def _section(title: str, findings: list[str]) -> str:
    body = "\n".join(f"  - {finding}" for finding in findings)
    return f"- {title}:\n{body}"


def _unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result


if __name__ == "__main__":
    raise SystemExit(main())

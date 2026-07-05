"""Parse AI-visible Markdown implementation plans into internal task objects."""

from __future__ import annotations

import re
from collections.abc import Iterable

from .task_contract_model import InternalTaskGraph, InternalTaskNode


TASK_HEADING_RE = re.compile(r"^##+\s+Task\s+([A-Za-z0-9_.-]+)\s*(?::|-)?\s*(.*)$", re.IGNORECASE)
TITLE_RE = re.compile(r"^#\s+(.+?)\s*$")
LABEL_RE = re.compile(r"^([^:：\n]{1,49})[:：]\s*(.*)$")

LABEL_ALIASES = {
    "goal": "goal",
    "目标": "goal",
    "files": "files",
    "file": "files",
    "文件": "files",
    "files to inspect": "files_to_inspect",
    "inspect": "files_to_inspect",
    "inspect files": "files_to_inspect",
    "检查文件": "files_to_inspect",
    "读取文件": "files_to_inspect",
    "files to change": "files_to_change",
    "files to modify": "files_to_change",
    "modify": "files_to_change",
    "change": "files_to_change",
    "create": "files_to_change",
    "delete": "files_to_change",
    "修改文件": "files_to_change",
    "变更文件": "files_to_change",
    "test": "files_to_inspect",
    "tests": "files_to_inspect",
    "test files": "files_to_inspect",
    "acceptance criteria": "acceptance_criteria",
    "acceptance criterion": "acceptance_criteria",
    "criteria": "acceptance_criteria",
    "验收标准": "acceptance_criteria",
    "verify": "verify",
    "verification": "verify",
    "validation": "verify",
    "validation command": "verify",
    "验证": "verify",
    "expected": "expected_output",
    "expected output": "expected_output",
    "预期结果": "expected_output",
    "预期输出": "expected_output",
    "review": "review_scope",
    "review scope": "review_scope",
    "审查": "review_scope",
    "审查范围": "review_scope",
    "stop conditions": "stop_conditions",
    "stop condition": "stop_conditions",
    "停止条件": "stop_conditions",
    "rollback": "rollback_note",
    "rollback note": "rollback_note",
    "revert note": "rollback_note",
    "回滚": "rollback_note",
    "dependencies": "dependencies",
    "depends on": "dependencies",
    "依赖": "dependencies",
    "residual risk": "residual_risk",
    "residual risks": "residual_risk",
    "残余风险": "residual_risk",
}

FILE_ROLE_ALIASES = {
    "inspect": "inspect",
    "检查": "inspect",
    "查看": "inspect",
    "read": "inspect",
    "读取": "inspect",
    "阅读": "inspect",
    "test": "inspect",
    "tests": "inspect",
    "测试": "inspect",
    "modify": "change",
    "修改": "change",
    "change": "change",
    "变更": "change",
    "update": "change",
    "更新": "change",
    "edit": "change",
    "编辑": "change",
    "create": "change",
    "创建": "change",
    "add": "change",
    "添加": "change",
    "新增": "change",
    "delete": "change",
    "删除": "change",
    "remove": "change",
    "移除": "change",
}
FILE_ROLE_RE = re.compile(
    rf"^({'|'.join(re.escape(label) for label in FILE_ROLE_ALIASES)})\s*[:：]\s*(.+)$",
    re.IGNORECASE,
)


def parse_visible_plan(markdown: str) -> InternalTaskGraph:
    """Parse the visible Markdown contract without exposing internal schemas."""

    lines = markdown.splitlines()
    title = _title(lines)
    tasks: list[InternalTaskNode] = []
    current: _TaskBuilder | None = None

    for line_number, line in enumerate(lines, start=1):
        match = TASK_HEADING_RE.match(line.strip())
        if match:
            if current is not None:
                tasks.append(current.build())
            current = _TaskBuilder(
                task_id=f"Task {match.group(1).strip()}",
                title=match.group(2).strip() or f"Task {match.group(1).strip()}",
                line_start=line_number,
            )
            continue
        if current is not None:
            current.add_line(line)

    if current is not None:
        tasks.append(current.build())

    return InternalTaskGraph(title=title, tasks=tuple(tasks))


def planned_files_from_visible_plan(markdown: str) -> tuple[str, ...]:
    """Return canonical file paths declared by a visible plan or Plan Handoff."""

    graph = parse_visible_plan(markdown)
    if graph.tasks:
        return _dedupe(path for task in graph.tasks for path in task.declared_files)
    handoff = parse_plan_handoff(markdown)
    return handoff.declared_files


def parse_plan_handoff(markdown: str) -> InternalTaskNode:
    """Parse a taskless L1/L2 Plan Handoff into the same internal task shape."""

    builder = _TaskBuilder(task_id="Plan Handoff", title="Plan Handoff", line_start=1)
    for line in markdown.splitlines():
        stripped = line.strip()
        if TASK_HEADING_RE.match(stripped):
            break
        if TITLE_RE.match(stripped):
            continue
        builder.add_line(line)
    return builder.build()


def canonicalize_plan_path(value: str) -> str:
    """Normalize a visible plan path token for plan-vs-diff comparisons."""

    item = str(value or "").strip()
    if not item:
        return ""
    role_match = FILE_ROLE_RE.match(item)
    if role_match:
        item = role_match.group(2).strip()
    backtick_match = re.search(r"`([^`]+)`", item)
    if backtick_match:
        item = backtick_match.group(1).strip()
    else:
        item = re.split(r"\s+(?:--?|#|//)\s+", item, maxsplit=1)[0].strip()
        item = re.split(r"\s+\(", item, maxsplit=1)[0].strip()
        item = item.strip("`'\"")
    return item.strip()


class _TaskBuilder:
    def __init__(self, *, task_id: str, title: str, line_start: int) -> None:
        self.task_id = task_id
        self.title = title
        self.line_start = line_start
        self.sections: dict[str, list[str]] = {}
        self.current_label = "description"

    def add_line(self, line: str) -> None:
        stripped = line.strip()
        label_match = LABEL_RE.match(stripped)
        if label_match:
            label = _normalize_label(label_match.group(1))
            if label:
                self.current_label = label
                remainder = label_match.group(2).strip()
                self.sections.setdefault(label, [])
                if remainder:
                    self.sections[label].append(remainder)
                return
        self.sections.setdefault(self.current_label, []).append(line.rstrip())

    def build(self) -> InternalTaskNode:
        section_text: dict[str, str] = {}
        for label, lines in self.sections.items():
            text = _clean_block(lines)
            if text:
                section_text[label] = text
        generic_files, inspected_files, changed_files = _file_values(section_text.get("files", ""))
        return InternalTaskNode(
            task_id=self.task_id,
            title=self.title,
            goal=section_text.get("goal", ""),
            files=generic_files,
            files_to_inspect=_dedupe(
                (*inspected_files, *_path_list_values(section_text.get("files_to_inspect", "")))
            ),
            files_to_change=_dedupe(
                (*changed_files, *_path_list_values(section_text.get("files_to_change", "")))
            ),
            acceptance_criteria=_list_values(section_text.get("acceptance_criteria", "")),
            verify=section_text.get("verify", ""),
            expected_output=section_text.get("expected_output", ""),
            review_scope=section_text.get("review_scope", ""),
            stop_conditions=section_text.get("stop_conditions", ""),
            rollback_note=section_text.get("rollback_note", ""),
            residual_risk=section_text.get("residual_risk", ""),
            dependencies=_list_values(section_text.get("dependencies", "")),
            raw_sections=section_text,
            line_start=self.line_start,
        )


def _title(lines: Iterable[str]) -> str:
    for line in lines:
        match = TITLE_RE.match(line.strip())
        if match:
            return match.group(1).strip()
    return ""


def _normalize_label(label: str) -> str:
    normalized = re.sub(r"\s+", " ", label.strip().lower())
    return LABEL_ALIASES.get(normalized, "")


def _clean_block(lines: list[str]) -> str:
    lines = list(lines)
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()
    return "\n".join(line.rstrip() for line in lines).strip()


def _list_values(text: str) -> tuple[str, ...]:
    values: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        item = re.sub(r"^[-*]\s+", "", stripped)
        item = re.sub(r"^\d+[.)]\s+", "", item).strip()
        if item:
            values.append(item)
    return tuple(values)


def _path_list_values(text: str) -> tuple[str, ...]:
    return _dedupe(canonicalize_plan_path(value) for value in _list_values(text))


def _file_values(text: str) -> tuple[tuple[str, ...], tuple[str, ...], tuple[str, ...]]:
    generic: list[str] = []
    inspect: list[str] = []
    change: list[str] = []
    for value in _list_values(text):
        role, path = _file_role_and_path(value)
        if not path:
            continue
        if role == "inspect":
            inspect.append(path)
        elif role == "change":
            change.append(path)
        else:
            generic.append(path)
    return _dedupe(generic), _dedupe(inspect), _dedupe(change)


def _file_role_and_path(value: str) -> tuple[str, str]:
    item = str(value or "").strip()
    role = ""
    role_match = FILE_ROLE_RE.match(item)
    if role_match:
        role = FILE_ROLE_ALIASES.get(role_match.group(1).casefold(), "")
    return role, canonicalize_plan_path(item)


def _dedupe(values: Iterable[str]) -> tuple[str, ...]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        item = str(value or "").strip()
        if not item or item in seen:
            continue
        seen.add(item)
        result.append(item)
    return tuple(result)

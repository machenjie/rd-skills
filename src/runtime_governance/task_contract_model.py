"""Internal task contract objects derived from visible Markdown plans."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class InternalTaskNode:
    """A parsed task from an AI-visible implementation plan."""

    task_id: str
    title: str
    goal: str = ""
    files: tuple[str, ...] = ()
    files_to_inspect: tuple[str, ...] = ()
    files_to_change: tuple[str, ...] = ()
    acceptance_criteria: tuple[str, ...] = ()
    verify: str = ""
    expected_output: str = ""
    review_scope: str = ""
    stop_conditions: str = ""
    rollback_note: str = ""
    residual_risk: str = ""
    dependencies: tuple[str, ...] = ()
    raw_sections: dict[str, str] = field(default_factory=dict)
    line_start: int = 0

    @property
    def all_text(self) -> str:
        parts = [
            self.title,
            self.goal,
            *self.files,
            *self.files_to_inspect,
            *self.files_to_change,
            *self.acceptance_criteria,
            self.verify,
            self.expected_output,
            self.review_scope,
            self.stop_conditions,
            self.rollback_note,
            self.residual_risk,
            *self.dependencies,
            *self.raw_sections.values(),
        ]
        return "\n".join(part for part in parts if part)

    @property
    def declared_files(self) -> tuple[str, ...]:
        seen: set[str] = set()
        ordered: list[str] = []
        for value in (*self.files, *self.files_to_inspect, *self.files_to_change):
            if value and value not in seen:
                seen.add(value)
                ordered.append(value)
        return tuple(ordered)


@dataclass(frozen=True)
class InternalTaskGraph:
    """A parsed visible implementation plan."""

    title: str = ""
    tasks: tuple[InternalTaskNode, ...] = ()


@dataclass(frozen=True)
class PlanContractFinding:
    """A human-facing plan quality finding."""

    code: str
    message: str
    severity: str = "error"
    task_id: str = ""


@dataclass(frozen=True)
class PlanQualityReport:
    """Validation report for a visible Markdown implementation plan."""

    status: str
    findings: tuple[PlanContractFinding, ...]
    task_count: int

    @property
    def passed(self) -> bool:
        return self.status == "pass"

    def human_readable_lines(self) -> list[str]:
        if not self.findings:
            return ["Implementation plan quality: pass."]

        lines = ["Implementation plan quality gaps:"]
        for finding in self.findings:
            prefix = f"{finding.task_id}: " if finding.task_id else ""
            lines.append(f"- {prefix}{finding.message}")
        return lines

    def to_human_readable_text(self) -> str:
        return "\n".join(self.human_readable_lines())

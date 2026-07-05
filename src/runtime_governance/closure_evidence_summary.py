"""Public-facing closure evidence checks derived from ordinary text."""

from __future__ import annotations

import re
from dataclasses import dataclass


STRONG_GATE_RE = re.compile(
    r"\b(gate|prove|demonstrate|acceptance test|smoke test|e2e|before proceeding|"
    r"do not continue until|make sure\b.+\bbefore moving on|first on one.+then all|"
    r"one first.+then all)\b|先在.+(证明|验证).+再推广|不要跳过",
    re.IGNORECASE,
)
WEAK_VERIFY_RE = re.compile(r"\b(verify|check|validate)\b|验证|检查", re.IGNORECASE)
PROOF_SCOPE_RE = re.compile(
    r"\b(proven by|proof|before|after|baseline|sample|one first|then all|"
    r"all samples|all files|acceptance criterion|ac:)\b|证明|样本|全部|推广",
    re.IGNORECASE,
)
ONE_THEN_ALL_RE = re.compile(
    r"\b(first on one|one first|single sample|one sample).+\b(then all|all samples|all files)\b|"
    r"先在.+(一个|单个|样本).+再推广",
    re.IGNORECASE,
)
PROVEN_BY_RE = re.compile(r"\bAC\s*:.+\bPROVEN BY\b.+", re.IGNORECASE)

REVIEW_REQUIRED_TERMS = {
    "spec_compliance": re.compile(r"\bspec compliance\b|验收|需求符合", re.IGNORECASE),
    "code_quality": re.compile(r"\bcode quality\b|代码质量", re.IGNORECASE),
    "reviewed_scope": re.compile(r"\b(reviewed files|review scope|approved scope|scope)\b|审查范围", re.IGNORECASE),
    "severity_findings": re.compile(r"\b(critical|important|minor|high|medium|low|severity|findings)\b|严重|重要|发现", re.IGNORECASE),
    "required_next_action": re.compile(r"\b(required next action|next action|repair|proceed|blocked)\b|下一步|修复", re.IGNORECASE),
    "residual_risk": re.compile(r"\bresidual risk\b|残余风险", re.IGNORECASE),
}
GENERIC_REVIEW_RE = re.compile(r"^\s*(reviewed[,.;:\s-]*looks good|looks good|lgtm)\s*\.?\s*$", re.IGNORECASE)
HIGH_SEVERITY_RE = re.compile(r"\b(critical|important|high|p0|p1)\b", re.IGNORECASE)
FINDING_WORD_RE = re.compile(r"\b(issues?|findings?|defects?|blockers?)\b", re.IGNORECASE)
NEGATED_FINDING_RE = re.compile(
    r"\b(no|none|without)\b.{0,60}\b(critical|important|high|p0|p1)\b.{0,60}"
    r"\b(issues?|findings?|defects?|blockers?)\b|"
    r"\b(findings?|issues?|defects?|blockers?)\b\s*:\s*\b(no|none)\b",
    re.IGNORECASE,
)
SEVERITY_LABEL_RE = re.compile(r"^\s*(?:[-*]\s*)?(critical|important|high|p0|p1)\s*[:#-]", re.IGNORECASE)
REPAIR_DONE_RE = re.compile(r"\b(fixed|repaired|resolved|implemented|changed)\b|修复|已解决", re.IGNORECASE)
REREVIEW_RE = re.compile(r"\b(re-review|rereview|reviewed again|targeted review|second review)\b|复审|重新审查", re.IGNORECASE)

INTERNAL_UNAWARENESS_PATTERNS = (
    re.compile(r"\brd-skills task ledger\b|\bChangeForge task ledger\b", re.IGNORECASE),
    re.compile(r"\bprocess_phase_ledgers\b", re.IGNORECASE),
    re.compile(r"\.changeforge\s+hook state|\.changeforge/.*hook state", re.IGNORECASE),
    re.compile(r"\binternal task metadata\b", re.IGNORECASE),
    re.compile(r"\bjson:metadata\b", re.IGNORECASE),
    re.compile(r"\bchangeforge-[-\w]+\s+internal script\b", re.IGNORECASE),
)


@dataclass(frozen=True)
class UserRequestedGate:
    status: str
    gate_scope: str = ""
    evidence_required: tuple[str, ...] = ()

    @property
    def is_user_requested(self) -> bool:
        return self.status == "user_requested_gate"


@dataclass(frozen=True)
class TextValidationResult:
    status: str
    missing: tuple[str, ...] = ()
    violations: tuple[str, ...] = ()

    @property
    def passed(self) -> bool:
        return self.status == "pass"


def classify_user_requested_gate(text: str) -> UserRequestedGate:
    """Classify user gate wording without requiring metadata."""

    source = str(text or "")
    strong = bool(STRONG_GATE_RE.search(source))
    weak_with_scope = bool(WEAK_VERIFY_RE.search(source) and PROOF_SCOPE_RE.search(source))
    if not (strong or weak_with_scope):
        return UserRequestedGate(status="normal_validation")
    scope = "one first, then all" if ONE_THEN_ALL_RE.search(source) else "explicit user gate"
    return UserRequestedGate(
        status="user_requested_gate",
        gate_scope=scope,
        evidence_required=("AC: <criterion> - PROVEN BY <observed result>",),
    )


def validate_task_review_text(text: str) -> TextValidationResult:
    """Reject ceremonial reviews and require spec/quality gates."""

    source = str(text or "").strip()
    missing = [name for name, pattern in REVIEW_REQUIRED_TERMS.items() if not pattern.search(source)]
    if GENERIC_REVIEW_RE.match(source):
        missing = sorted(set([*missing, "non_generic_review"]))
    return TextValidationResult(status="pass" if not missing else "fail", missing=tuple(missing))


def validate_repair_rereview_text(text: str) -> TextValidationResult:
    """Require re-review after repairing important findings."""

    source = str(text or "")
    if _has_positive_high_severity_finding(source) and REPAIR_DONE_RE.search(source) and not REREVIEW_RE.search(source):
        return TextValidationResult(status="fail", missing=("re_review_after_repair",))
    return TextValidationResult(status="pass")


def _has_positive_high_severity_finding(text: str) -> bool:
    for line in str(text or "").splitlines() or [str(text or "")]:
        source = line.strip()
        if not source or NEGATED_FINDING_RE.search(source):
            continue
        has_severity = bool(HIGH_SEVERITY_RE.search(source))
        if not has_severity:
            continue
        if SEVERITY_LABEL_RE.search(source):
            return True
        if FINDING_WORD_RE.search(source):
            return True
    return False


def find_internal_unawareness_violations(text: str) -> tuple[str, ...]:
    """Return public-boundary violations in ordinary agent output."""

    source = str(text or "")
    violations: list[str] = []
    for pattern in INTERNAL_UNAWARENESS_PATTERNS:
        match = pattern.search(source)
        if match:
            violations.append(match.group(0))
    return tuple(dict.fromkeys(violations))


def ac_proven_by_lines(text: str) -> tuple[str, ...]:
    """Extract AC -> PROVEN BY evidence lines from ordinary text."""

    return tuple(line.strip() for line in str(text or "").splitlines() if PROVEN_BY_RE.search(line))

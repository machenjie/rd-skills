from pathlib import Path
import json
import os
import re


REQUIRED_FIELDS = {
    "route_id",
    "selected_skills",
    "selected_capabilities",
    "required_quality_gates",
    "current_stage",
    "pdd_summary",
    "ddd_invariants",
    "sdd_decisions",
    "tdd_validation_plan",
    "changed_paths",
    "validation_results",
    "validation_freshness",
    "review_findings",
    "repair_events",
    "rereview_events",
    "residual_risk",
    "memory_references",
    "active_skill_context",
}


def _candidate_root() -> Path:
    return Path(os.environ.get("CHANGEFORGE_CODEGEN_CANDIDATE_DIR", Path.cwd()))


def _load_context() -> dict:
    path = _candidate_root() / "COMPACTION_CONTEXT.json"
    assert path.is_file(), "COMPACTION_CONTEXT.json is required; markdown-only evidence is not enough"
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(payload, dict), "COMPACTION_CONTEXT.json must be a JSON object"
    return payload


def test_required_context_survives_compaction_and_continuation() -> None:
    payload = _load_context()
    missing = sorted(field for field in REQUIRED_FIELDS if not payload.get(field))
    assert not missing, f"missing required context fields: {missing}"
    assert payload.get("pre_compact_snapshot_written") is True
    assert payload.get("post_compact_reinject_emitted") is True
    assert payload.get("compact_after_repair_continuation_status") == "pass"
    assert payload.get("context_retention_status") == "pass"
    assert payload.get("privacy_redaction_status") == "pass"
    assert payload.get("validation_freshness") in {
        "fresh_after_latest_material_change",
        "rerun_after_material_change",
    }
    assert payload.get("compressed_state_not_overwritten_by_session_bootstrap") is True


def test_final_handoff_references_preserved_context() -> None:
    root = _candidate_root()
    evidence = root / "CAPABILITY_EVIDENCE.md"
    assert evidence.is_file(), "CAPABILITY_EVIDENCE.md is auxiliary but still expected"
    text = evidence.read_text(encoding="utf-8", errors="ignore").casefold()
    required_terms = [
        "acceptance criteria",
        "ddd invariant",
        "sdd decision",
        "tdd validation",
        "changed files",
        "validation freshness",
        "review finding",
        "repair",
        "re-review",
        "residual risk",
        "selected skills",
        "selected capabilities",
        "quality gates",
    ]
    missing = [term for term in required_terms if term not in text]
    assert not missing, f"handoff does not reference preserved context: {missing}"


def test_no_sensitive_or_raw_context_persisted() -> None:
    root = _candidate_root()
    text = "\n".join(
        path.read_text(encoding="utf-8", errors="ignore")
        for path in root.rglob("*")
        if path.is_file() and path.suffix.lower() in {".md", ".txt", ".json", ".yaml", ".yml", ".py"}
    )
    forbidden = [
        r"/Users/",
        r"/home/",
        r"/private/var/",
        r"/var/folders/",
        r"OPENAI_API_KEY",
        r"CODEX_API_KEY",
        r"sk-[A-Za-z0-9_-]{10,}",
        r"raw prompt",
        r"raw assistant",
        r"raw command output",
        r"full diff body",
        r"full file contents",
    ]
    assert not [pattern for pattern in forbidden if re.search(pattern, text, flags=re.IGNORECASE)]

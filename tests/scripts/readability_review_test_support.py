"""Domain-owned Readability review fixtures shared by Expert Panel tests."""

from __future__ import annotations

import copy
import functools
import hashlib
import json
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from .expert_panel_source_test_support import (
    AUDIT,
    PANEL,
    ROOT,
    write_json,
)


@functools.lru_cache(maxsize=1)
def _current_audit_cached() -> dict:
    audit = json.loads(
        (ROOT / "reports/skill-content-audit.json").read_text(encoding="utf-8")
    )
    auditor = PANEL._load_skill_content_auditor()
    audit["ai_readability"] = auditor._collect_ai_readability(
        auditor._ai_readability_documents()
    )
    return audit


def current_audit() -> dict:
    return copy.deepcopy(_current_audit_cached())


@functools.lru_cache(maxsize=1)
def _current_packet_cached() -> dict:
    return PANEL.prepare_packet(
        audit=_current_audit_cached(),
        review_id="actionability-v2-fixture",
        created_on="2026-07-17",
    )


def current_packet() -> dict:
    """Return a mutable copy of the immutable current Readability fixture."""

    return copy.deepcopy(_current_packet_cached())


def _first_substantive_window_line(target: dict) -> tuple[int, str, str]:
    for row in target["front_window"]["lines"]:
        tokens = sorted(PANEL._evidence_tokens(row["text"]))
        if (
            PANEL._actionability_window_line_is_substantive(
                target["front_window"], row["line"]
            )
            and tokens
        ):
            return row["line"], row["text"], tokens[0]
    raise AssertionError("front window lacks substantive actionability evidence")


def ballot(
    packet: dict,
    packet_sha256: str,
    voter: int,
    *,
    actionability_decision: str = "accepted-current-actionability",
) -> dict:
    value = PANEL.prepare_readability_ballot_template(
        packet=packet,
        packet_sha256=packet_sha256,
        voter_id=f"actionability-expert-{voter}",
        agent_id=f"actionability-agent-{voter}",
        role=f"senior AI instruction actionability reviewer {voter}",
        expertise=["AI instruction semantics and executable action design"],
        created_on="2026-07-17",
    )
    for vote in value["content_votes"]:
        vote.update(
            decision="accepted-current-density",
            reason_code="bounded-density-preserves-professional-coverage",
            rationale=(
                "This bounded density preserves one complete and coherent "
                "professional decision model."
            ),
        )
    for vote in value["readability_votes"]:
        for finding_review in vote["finding_reviews"]:
            finding_review.update(
                decision="accepted-current-readability",
                reason_code="single-indivisible-decision",
                rationale=(
                    "This sentence preserves one complete and coherent decision "
                    "without separable instructions."
                ),
            )
    targets = {target["target_id"]: target for target in packet["actionability_targets"]}
    reason_code = {
        "accepted-current-actionability": "explicit-domain-actions-are-front-loaded",
        "detector-false-positive": "equivalent-action-verb-not-recognized",
        "rewrite-required": "primary-action-not-front-loaded",
    }[actionability_decision]
    for vote in value["actionability_votes"]:
        line, source_line, source_token = _first_substantive_window_line(
            targets[vote["target_id"]]
        )
        vote.update(
            decision=actionability_decision,
            reason_code=reason_code,
            rationale=(
                "The reviewed opening lines provide concrete evidence for "
                "this actionability disposition."
            ),
            evidence=[
                {
                    "line": line,
                    "source_line": source_line,
                    "claim": (
                        f"The {source_token} opening instruction provides concrete "
                        "actionability review evidence."
                    ),
                }
            ],
        )
    return value


@contextmanager
def historical_decision() -> Iterator[tuple[dict, Path]]:
    current = current_packet()
    current["review_id"] = "historical-readability-fixture"
    packet = copy.deepcopy(current)
    packet["panel_contract"].pop("content_source_binding_contract", None)
    for target in packet["content_targets"]:
        for field in (
            "document_id",
            "owner",
            "document_part",
            "source_selector",
            "document_context",
            "content_fingerprint",
        ):
            target.pop(field, None)
    with tempfile.TemporaryDirectory(dir=ROOT) as raw:
        root = Path(raw)
        packet_path = root / "packet.json"
        write_json(packet_path, packet)
        digest = hashlib.sha256(packet_path.read_bytes()).hexdigest()
        ballots = []
        for voter in range(1, 4):
            value = ballot(current, digest, voter)
            value["review_id"] = packet["review_id"]
            ballot_path = root / f"readability-voter-{voter}.json"
            write_json(ballot_path, value)
            ballots.append((ballot_path, value))
        decision = PANEL.aggregate_ballots(
            packet=packet,
            packet_path=packet_path,
            ballot_values=ballots,
            decided_on="2026-08-10",
            validation_mode=PANEL.VALIDATION_MODE_HISTORICAL,
        )
        decision_path = root / "decision.json"
        write_json(decision_path, decision)
        yield decision, decision_path

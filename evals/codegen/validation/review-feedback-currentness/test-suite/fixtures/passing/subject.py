"""Bounded review-evidence records; no Git, files, network, or thread effects."""
from copy import deepcopy


def triage(head, sources, findings, proofs, decisions):
    results, verified = {}, []
    kinds = {"defect", "suggestion", "preference", "question", "out-of-scope"}
    if len({item["id"] for item in findings}) != len(findings):
        raise ValueError("duplicate feedback id")
    for finding in findings:
        identity, path, kind = finding["id"], finding["path"], finding["kind"]
        if kind not in kinds:
            raise ValueError("unknown feedback kind")
        result = {"kind": kind, "commit": head, "origin_commit": finding["commit"],
                  "anchor": None, "status": "needs-validation", "reason": "current proof is missing"}
        results[identity] = result
        source, proof = sources.get(path), proofs.get(path)
        if source is None:
            result.update(status="obsolete", reason="referenced file no longer exists")
            continue
        if kind in {"question", "out-of-scope"}:
            result.update(status=kind, reason=("answer the question before proposing a fix" if kind == "question"
                                             else "requested behavior is outside the supplied task scope"))
            continue
        if kind == "preference":
            decision = decisions.get(identity, {})
            if decision.get("choice") == "reject" and decision.get("reason", "").strip():
                result.update(status="rejected", reason=decision["reason"])
            else:
                result.update(status="preference", reason="style preference requires a separate project decision")
            continue
        if not proof or proof.get("commit") != head or proof.get("source") != source:
            result["reason"] = "proof must bind the current commit and exact source"
            continue
        lines = source.splitlines()
        line, anchor = proof.get("line", 0), proof.get("anchor")
        if not isinstance(line, int) or not 1 <= line <= len(lines) or lines[line - 1] != anchor:
            result["reason"] = "proof anchor does not identify the current code"
            continue
        if finding["anchor"] != anchor and proof.get("relocates_from") != finding["anchor"]:
            result.update(status="obsolete", reason="old anchor changed without a verified relocation")
            continue
        result["anchor"] = {"path": path, "line": line, "text": anchor}
        minimum = finding["minimum"]
        observations = proof.get("observations", [])
        samples = {sample["units"]: sample["accepted"] for sample in observations}
        required = {minimum - 1, minimum, minimum + 1}
        if (len(samples) != len(observations) or not required <= samples.keys()
                or any(type(value) is not bool for value in samples.values())):
            result["reason"] = "boundary observations are missing, duplicated, or invalid"
            continue
        violated = any(samples[units] != (units >= minimum) for units in required)
        verified.append(finding)
        if not violated:
            result.update(status="resolved", reason="current boundary observations satisfy the claimed rule")
            continue
        result.update(status="verified", reason="current observations violate the supplied acceptance rule")
    groups = {}
    for finding in verified:
        groups.setdefault((finding["path"], finding["subject"]), []).append(finding)
    for group in groups.values():
        if len({finding["minimum"] for finding in group}) > 1:
            for finding in group:
                results[finding["id"]].update(status="conflicting", reason="same acceptance predicate has incompatible minimums")
            continue
        canonical = group[0]["id"]
        for finding in group[1:]:
            results[finding["id"]].update(status="duplicate", reason="same verified rule as " + canonical, canonical=canonical)
        finding = group[0]
        result, decision = results[canonical], decisions.get(canonical, {})
        if result["status"] == "resolved":
            continue
        choice, reason = decision.get("choice"), decision.get("reason", "").strip()
        if choice == "reject" and reason:
            result.update(status="rejected", reason=reason)
            continue
        if choice not in {"accept", "alternative"} or not reason:
            result.update(status="needs-decision", reason="accept, reject, or alternative requires a concrete reason")
            continue
        edit, validation = decision.get("edit", {}), decision.get("validation", {})
        bound = result["anchor"]
        if (edit.get("path") != bound["path"] or edit.get("line") != bound["line"]
                or edit.get("before") != bound["text"] or not edit.get("after")
                or edit["after"] == edit["before"] or "\n" in edit["after"]
                or not validation.get("check")
                or not {finding["minimum"] - 1, finding["minimum"], finding["minimum"] + 1} <= set(validation.get("inputs", []))
                or not decision.get("remaining_risk", "").strip()):
            result.update(status="needs-plan", reason="bounded current edit, boundary proof plan, and remaining risk are required")
            continue
        result.update(status="accepted" if choice == "accept" else "alternative", reason=reason,
                      edit=deepcopy(edit), validation=deepcopy(validation), remaining_risk=decision["remaining_risk"])
    return results


def action_permissions(role, grants, disposition):
    """Return independent permission records, never perform an action."""
    names = ("judge", "edit", "reply", "resolve", "request-rereview")
    if role not in {"analysis-agent", "task-agent", "review-agent"} or set(grants) - set(names):
        raise ValueError("unknown role or grant")
    result = {}
    for name in names:
        allowed = name in grants and (name == "judge" or role == "task-agent")
        if name == "edit":
            allowed = allowed and disposition.get("status") in {"accepted", "alternative"}
        result[name] = {"authorized": allowed,
                        "reason": "explicit grant within role" if allowed else "missing grant, role authority, or accepted edit"}
    return result

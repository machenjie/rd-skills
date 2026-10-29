def triage(head, sources, findings, proofs, decisions):
    return {item["id"]: {"kind": item["kind"], "status": "needs-validation", "reason": "not implemented"} for item in findings}

def action_permissions(role, grants, disposition):
    return {name: {"authorized": False, "reason": "not implemented"} for name in ("judge", "edit", "reply", "resolve", "request-rereview")}

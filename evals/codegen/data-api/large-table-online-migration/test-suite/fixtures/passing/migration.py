def split_full_name(value: str) -> tuple[str, str | None]:
    first, separator, rest = value.strip().partition(" ")
    return first, rest or None


def expand_row(row: dict) -> dict:
    expanded = dict(row)
    expanded.setdefault("first_name", None)
    expanded.setdefault("last_name", None)
    return expanded


def write_profile(row: dict, payload: dict) -> dict:
    updated = expand_row(row)
    if "full_name" in payload:
        updated["full_name"] = payload["full_name"]
        updated["first_name"], updated["last_name"] = split_full_name(payload["full_name"])
    if "first_name" in payload or "last_name" in payload:
        updated["first_name"] = payload.get("first_name", updated.get("first_name"))
        updated["last_name"] = payload.get("last_name", updated.get("last_name"))
        updated["full_name"] = " ".join(
            value for value in (updated["first_name"], updated["last_name"]) if value
        )
    return updated


def read_profile(row: dict, client: str) -> dict:
    current = expand_row(row)
    if current["first_name"] is None:
        current["first_name"], current["last_name"] = split_full_name(current["full_name"])
    if client == "old":
        return {"full_name": current["full_name"]}
    if client == "new":
        return {"first_name": current["first_name"], "last_name": current["last_name"]}
    raise ValueError("unknown client contract")


def backfill_batch(rows: list[dict], cursor: int, limit: int, tenant_id: str) -> tuple[int, int]:
    eligible = sorted(
        (
            row
            for row in rows
            if row["id"] > cursor and row["tenant_id"] == tenant_id
        ),
        key=lambda row: row["id"],
    )[:limit]
    for row in eligible:
        if row.get("first_name") is None and row.get("last_name") is None:
            row["first_name"], row["last_name"] = split_full_name(row["full_name"])
    return (eligible[-1]["id"] if eligible else cursor, len(eligible))


def rollback_before_cleanup(row: dict) -> dict:
    rolled_back = dict(row)
    if not rolled_back.get("full_name"):
        rolled_back["full_name"] = " ".join(
            value for value in (rolled_back.get("first_name"), rolled_back.get("last_name")) if value
        )
    return rolled_back


def contract_cleanup(rows: list[dict], *, approved: bool) -> list[dict]:
    if not approved:
        raise RuntimeError("cleanup gate is not approved")
    return [{key: value for key, value in row.items() if key != "full_name"} for row in rows]

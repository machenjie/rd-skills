LEGACY_TO_NORMALIZED = {"P": "pending", "S": "shipped", "C": "cancelled"}
NORMALIZED_TO_LEGACY = {value: key for key, value in LEGACY_TO_NORMALIZED.items()}


def write_status(row: dict, status: str, *, writer: str) -> dict:
    updated = dict(row)
    audit = list(updated.get("audit", []))
    if writer == "old":
        legacy = status
        normalized = LEGACY_TO_NORMALIZED[legacy]
    elif writer == "new":
        normalized = status
        legacy = NORMALIZED_TO_LEGACY[normalized]
    else:
        raise ValueError("unknown writer")
    updated["legacy_status"] = legacy
    updated["normalized_status"] = normalized
    audit.append({"legacy": legacy, "normalized": normalized})
    updated["audit"] = audit
    return updated


def read_status(row: dict, *, reader: str) -> str:
    if reader == "old":
        return row.get("legacy_status") or NORMALIZED_TO_LEGACY[row["normalized_status"]]
    if reader == "new":
        return row.get("normalized_status") or LEGACY_TO_NORMALIZED[row["legacy_status"]]
    raise ValueError("unknown reader")


def backfill_batch(rows: list[dict], cursor: int, limit: int) -> tuple[int, int]:
    eligible = sorted((row for row in rows if row["id"] > cursor), key=lambda row: row["id"])[:limit]
    for row in eligible:
        if not row.get("normalized_status"):
            row["normalized_status"] = LEGACY_TO_NORMALIZED[row["legacy_status"]]
    return (eligible[-1]["id"] if eligible else cursor, len(eligible))


def rollback_to_legacy(row: dict) -> dict:
    rolled_back = dict(row)
    if not rolled_back.get("legacy_status"):
        rolled_back["legacy_status"] = NORMALIZED_TO_LEGACY[rolled_back["normalized_status"]]
    return rolled_back


def cleanup(rows: list[dict], *, approved: bool) -> list[dict]:
    if not approved:
        raise RuntimeError("cleanup gate is not approved")
    return [{key: value for key, value in row.items() if key != "legacy_status"} for row in rows]

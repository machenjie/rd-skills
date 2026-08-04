"""Keyword-complete starter that breaks the old reader during cutover."""

LEGACY_TO_NORMALIZED = {"P": "pending", "S": "shipped", "C": "cancelled"}
NORMALIZED_TO_LEGACY = {value: key for key, value in LEGACY_TO_NORMALIZED.items()}


def write_status(row: dict, status: str, *, writer: str) -> dict:
    updated = dict(row)
    if writer == "old":
        updated["legacy_status"] = status
    else:
        updated["normalized_status"] = status
    return updated


def read_status(row: dict, *, reader: str) -> str:
    return row["legacy_status"] if reader == "old" else row["normalized_status"]


def backfill_batch(rows: list[dict], cursor: int, limit: int) -> tuple[int, int]:
    for row in rows:
        row["normalized_status"] = LEGACY_TO_NORMALIZED[row["legacy_status"]]
    return (rows[-1]["id"] if rows else cursor, len(rows))


def rollback_to_legacy(row: dict) -> dict:
    return dict(row)


def cleanup(rows: list[dict], *, approved: bool) -> list[dict]:
    return [{key: value for key, value in row.items() if key != "legacy_status"} for row in rows]

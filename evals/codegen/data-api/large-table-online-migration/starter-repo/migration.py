"""Keyword-correct starter with an unsafe, non-resumable backfill."""


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
    updated.update(payload)
    return updated


def read_profile(row: dict, client: str) -> dict:
    return dict(row)


def backfill_batch(rows: list[dict], cursor: int, limit: int, tenant_id: str) -> tuple[int, int]:
    processed = 0
    checkpoint = cursor
    for row in rows:
        if row["id"] <= cursor or row["tenant_id"] != tenant_id:
            continue
        row["first_name"], row["last_name"] = split_full_name(row["full_name"])
        checkpoint = row["id"]
        processed += 1
    return checkpoint, processed


def rollback_before_cleanup(row: dict) -> dict:
    return dict(row)


def contract_cleanup(rows: list[dict], *, approved: bool) -> list[dict]:
    return [{key: value for key, value in row.items() if key != "full_name"} for row in rows]

"""Keyword-complete starter with a backward-compatibility defect."""

ALLOWED_CONTACT_METHODS = {"email", "phone", "sms", None}


def serialize_profile(record: dict) -> dict:
    return {
        "name": record["name"],
        "email": record["email"],
        "phone": record["phone"],
        "marketing": record["marketing"],
        "preferred_contact_method": record["preferred_contact_method"],
    }


def patch_profile(record: dict, payload: dict) -> dict:
    value = payload["preferred_contact_method"]
    if value not in ALLOWED_CONTACT_METHODS:
        raise ValueError("invalid preferred_contact_method; allowed values email, phone, sms, null")
    record.update(payload)
    return serialize_profile(record)

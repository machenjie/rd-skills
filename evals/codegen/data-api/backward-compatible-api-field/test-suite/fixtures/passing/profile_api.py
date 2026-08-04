ALLOWED_CONTACT_METHODS = {"email", "phone", "sms", None}


def serialize_profile(record: dict) -> dict:
    return {
        "name": record["name"],
        "email": record["email"],
        "phone": record["phone"],
        "marketing": record["marketing"],
        "preferred_contact_method": record.get("preferred_contact_method"),
    }


def patch_profile(record: dict, payload: dict) -> dict:
    updated = dict(record)
    if "preferred_contact_method" in payload:
        value = payload["preferred_contact_method"]
        if value not in ALLOWED_CONTACT_METHODS:
            raise ValueError("invalid preferred_contact_method")
    updated.update(payload)
    return serialize_profile(updated)

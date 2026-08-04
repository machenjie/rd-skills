"""Correct behavior for the null-profile same-pattern scan."""


def public_profile(user: dict, *, authorized: bool) -> dict:
    if not authorized:
        raise PermissionError("authorization denied")
    profile = user.get("profile")
    return {"display_name": None if profile is None else profile["name"]}


def notification_preview(user: dict) -> str:
    profile = user.get("profile")
    return "Welcome" if profile is None else f"Welcome {profile['name']}"


def strict_export(user: dict) -> str:
    profile = user.get("profile")
    if profile is None:
        raise ValueError("invalid profile: absence is a data quality error")
    return profile["name"]

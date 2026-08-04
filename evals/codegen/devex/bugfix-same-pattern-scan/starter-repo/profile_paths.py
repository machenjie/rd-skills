"""Profile boundaries used by the same-pattern bugfix benchmark.

The comments deliberately name the requested scan terms.  They are not proof:
the executable tests require the public and sibling paths to handle an absent
profile while authorization and strict data-quality behavior remain intact.
"""


def public_profile(user: dict, *, authorized: bool) -> dict:
    if not authorized:
        raise PermissionError("authorization denied")
    return {"display_name": user["profile"]["name"]}


def notification_preview(user: dict) -> str:
    return f"Welcome {user['profile']['name']}"


def strict_export(user: dict) -> str:
    profile = user.get("profile")
    if profile is None:
        raise ValueError("invalid profile: absence is a data quality error")
    return profile["name"]

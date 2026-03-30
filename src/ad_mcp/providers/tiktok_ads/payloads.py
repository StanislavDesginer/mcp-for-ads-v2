from __future__ import annotations


def _wrap(resource: str, action: str, body: dict) -> dict:
    method = {"create": "POST", "update": "POST", "delete_or_archive": "POST"}.get(action, "POST")
    return {
        "resource": resource,
        "operation": action,
        "http_method": method,
        "endpoint": f"/tiktok/{resource}",
        "body": body,
    }


def build_tiktok_ads_payload(action: str, object_type: str, payload: dict) -> dict:
    base = _wrap(object_type, action, {})
    if object_type == "campaign":
        base["body"] = {
                "campaign_name": payload.get("name"),
                "objective_type": payload.get("objective_type", "TRAFFIC"),
                "budget_mode": payload.get("budget_mode", "BUDGET_MODE_DAY"),
                "budget": payload.get("budget"),
                "status": payload.get("status", "DISABLE"),
        }
    elif object_type in {"adgroup", "ad_group"}:
        base["resource"] = "adgroup"
        base["endpoint"] = "/tiktok/adgroup"
        base["body"] = {
                "adgroup_name": payload.get("name"),
                "campaign_id": payload.get("campaign_id"),
                "placement_type": payload.get("placement_type"),
                "schedule_type": payload.get("schedule_type"),
                "targeting": payload.get("targeting", {}),
                "budget": payload.get("budget"),
                "status": payload.get("status", "DISABLE"),
        }
    elif object_type == "ad":
        base["body"] = {
                "ad_name": payload.get("name"),
                "adgroup_id": payload.get("adgroup_id"),
                "creative_material_mode": payload.get("creative_material_mode"),
                "creative_payload": payload.get("creative_payload", {}),
                "status": payload.get("status", "DISABLE"),
        }
    elif object_type == "audience":
        base["body"] = {
            "name": payload.get("name"),
            "locations": payload.get("locations", []),
            "interests": payload.get("interests", []),
            "behaviors": payload.get("behaviors", []),
            "age_min": payload.get("age_min"),
            "age_max": payload.get("age_max"),
            "genders": payload.get("genders", []),
        }
    elif object_type == "schedule":
        base["body"] = {
            "days": payload.get("days", []),
            "windows": payload.get("windows", []),
            "timezone": payload.get("timezone"),
            "schedule_type": payload.get("schedule_type"),
        }
    else:
        base["body"] = payload
    return base

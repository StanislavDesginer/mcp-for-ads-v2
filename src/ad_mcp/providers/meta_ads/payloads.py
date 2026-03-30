from __future__ import annotations


def _wrap(resource: str, action: str, body: dict) -> dict:
    method = {"create": "POST", "update": "POST", "delete_or_archive": "DELETE"}.get(action, "POST")
    return {
        "resource": resource,
        "operation": action,
        "http_method": method,
        "endpoint": f"/meta/{resource}",
        "body": body,
    }


def build_meta_ads_payload(action: str, object_type: str, payload: dict) -> dict:
    if object_type == "campaign":
        return _wrap("campaign", action, {
            "name": payload.get("name"),
            "objective": payload.get("objective", "OUTCOME_SALES"),
            "status": payload.get("status", "PAUSED"),
            "special_ad_categories": payload.get("special_ad_categories", []),
            "daily_budget": payload.get("daily_budget"),
            "lifetime_budget": payload.get("lifetime_budget"),
        })
    if object_type in {"adset", "ad_group"}:
        return _wrap("adset", action, {
            "name": payload.get("name"),
            "campaign_id": payload.get("campaign_id"),
            "billing_event": payload.get("billing_event"),
            "optimization_goal": payload.get("optimization_goal"),
            "bid_strategy": payload.get("bid_strategy"),
            "daily_budget": payload.get("daily_budget"),
            "targeting": payload.get("targeting", {}),
            "promoted_object": payload.get("promoted_object", {}),
            "status": payload.get("status", "PAUSED"),
        })
    if object_type == "ad":
        return _wrap("ad", action, {
            "name": payload.get("name"),
            "adset_id": payload.get("adset_id"),
            "creative": payload.get("creative", {}),
            "status": payload.get("status", "PAUSED"),
            "tracking_specs": payload.get("tracking_specs", []),
        })
    if object_type == "audience":
        return _wrap("custom_audience", action, {
            "name": payload.get("name"),
            "subtype": payload.get("subtype", "CUSTOM"),
            "rule": payload.get("rule", {}),
            "retention_days": payload.get("retention_days"),
            "locations": payload.get("locations", []),
            "interests": payload.get("interests", []),
            "behaviors": payload.get("behaviors", []),
            "age_min": payload.get("age_min"),
            "age_max": payload.get("age_max"),
            "genders": payload.get("genders", []),
        })
    if object_type == "schedule":
        return _wrap("adset_schedule", action, {
            "days": payload.get("days", []),
            "windows": payload.get("windows", []),
            "timezone": payload.get("timezone"),
        })
    return _wrap(object_type, action, payload)

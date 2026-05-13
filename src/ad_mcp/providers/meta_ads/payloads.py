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


def _value(payload: dict, key: str, action: str, create_default=None):
    if key in payload:
        return payload.get(key)
    if action == "create":
        return create_default
    return None


def build_meta_ads_payload(action: str, object_type: str, payload: dict) -> dict:
    if object_type == "campaign":
        body = {
            "id": payload.get("id"),
            "name": payload.get("name"),
            "objective": _value(payload, "objective", action, "OUTCOME_SALES"),
            "status": _value(payload, "status", action, "PAUSED"),
            "special_ad_categories": _value(payload, "special_ad_categories", action, []),
            "daily_budget": payload.get("daily_budget"),
            "lifetime_budget": payload.get("lifetime_budget"),
            "spend_cap": payload.get("spend_cap"),
            "budget_delta_percent": payload.get("budget_delta_percent"),
            "start_time": payload.get("start_time"),
            "stop_time": payload.get("stop_time"),
            "buying_type": payload.get("buying_type"),
            "bid_strategy": payload.get("bid_strategy"),
            "source_campaign_id": payload.get("source_campaign_id"),
            "clone_options": payload.get("clone_options", {}),
            "ids": payload.get("ids"),
        }
        body.update(payload.get("extra_fields", {}))
        return _wrap("campaign", action, body)
    if object_type in {"adset", "ad_group"}:
        body = {
            "id": payload.get("id"),
            "name": payload.get("name"),
            "campaign_id": payload.get("campaign_id"),
            "billing_event": payload.get("billing_event"),
            "optimization_goal": payload.get("optimization_goal"),
            "optimization_sub_event": payload.get("optimization_sub_event"),
            "bid_strategy": payload.get("bid_strategy"),
            "bid_amount": payload.get("bid_amount"),
            "daily_budget": payload.get("daily_budget"),
            "lifetime_budget": payload.get("lifetime_budget"),
            "budget_delta_percent": payload.get("budget_delta_percent"),
            "targeting": payload.get("targeting", {}),
            "placements": payload.get("placements", {}),
            "promoted_object": payload.get("promoted_object", {}),
            "status": _value(payload, "status", action, "PAUSED"),
            "start_time": payload.get("start_time"),
            "end_time": payload.get("end_time"),
            "source_adset_id": payload.get("source_adset_id"),
            "clone_options": payload.get("clone_options", {}),
            "ids": payload.get("ids"),
        }
        body.update(payload.get("extra_fields", {}))
        return _wrap("adset", action, body)
    if object_type == "ad":
        body = {
            "id": payload.get("id"),
            "name": payload.get("name"),
            "adset_id": payload.get("adset_id"),
            "creative": payload.get("creative", {}),
            "creative_id": payload.get("creative_id"),
            "existing_creative_id": payload.get("existing_creative_id"),
            "status": _value(payload, "status", action, "PAUSED"),
            "tracking_specs": payload.get("tracking_specs", []),
            "url_tags": payload.get("url_tags"),
            "source_ad_id": payload.get("source_ad_id"),
            "clone_options": payload.get("clone_options", {}),
            "ids": payload.get("ids"),
        }
        body.update(payload.get("extra_fields", {}))
        return _wrap("ad", action, body)
    if object_type == "audience":
        body = {
            "id": payload.get("id"),
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
            "lookalike_spec": payload.get("lookalike_spec", {}),
            "customer_file_source": payload.get("customer_file_source"),
            "ids": payload.get("ids"),
        }
        body.update(payload.get("extra_fields", {}))
        return _wrap("custom_audience", action, body)
    if object_type == "schedule":
        body = {
            "id": payload.get("id"),
            "days": payload.get("days", []),
            "windows": payload.get("windows", []),
            "timezone": payload.get("timezone"),
            "ids": payload.get("ids"),
        }
        body.update(payload.get("extra_fields", {}))
        return _wrap("adset_schedule", action, body)
    return _wrap(object_type, action, payload)

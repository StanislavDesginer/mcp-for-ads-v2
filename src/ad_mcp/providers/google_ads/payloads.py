from __future__ import annotations


def _wrap(resource: str, action: str, body: dict) -> dict:
    method = {"create": "POST", "update": "PATCH", "delete_or_archive": "DELETE"}.get(action, "POST")
    return {
        "resource": resource,
        "operation": action,
        "http_method": method,
        "endpoint": f"/googleads/{resource}",
        "body": body,
        **body,
    }


def build_google_ads_payload(action: str, object_type: str, payload: dict) -> dict:
    if object_type == "campaign":
        return _wrap("campaign", action, {
            "name": payload.get("name"),
            "campaign_type": payload.get("campaign_type", "search"),
            "status": payload.get("status", "PAUSED"),
            "budget_micros": payload.get("budget_micros"),
            "bidding_strategy": payload.get("bidding_strategy"),
            "start_date": payload.get("start_date"),
            "end_date": payload.get("end_date"),
            "network_settings": payload.get("network_settings", {}),
        })
    if object_type == "ad_group":
        return _wrap("ad_group", action, {
            "name": payload.get("name"),
            "campaign_id": payload.get("campaign_id"),
            "type": payload.get("type", "SEARCH_STANDARD"),
            "cpc_bid_micros": payload.get("cpc_bid_micros"),
            "status": payload.get("status", "ENABLED"),
            "targeting": payload.get("targeting", {}),
        })
    if object_type == "ad":
        return _wrap("ad_group_ad", action, {
            "ad_group_id": payload.get("ad_group_id"),
            "status": payload.get("status", "PAUSED"),
            "final_urls": payload.get("final_urls", []),
            "headlines": payload.get("headlines", []),
            "descriptions": payload.get("descriptions", []),
            "path1": payload.get("path1"),
            "path2": payload.get("path2"),
        })
    if object_type == "keyword":
        return _wrap("ad_group_criterion.keyword", action, {
            "ad_group_id": payload.get("ad_group_id"),
            "text": payload.get("text"),
            "match_type": payload.get("match_type", "PHRASE"),
            "cpc_bid_micros": payload.get("cpc_bid_micros"),
            "status": payload.get("status", "ENABLED"),
        })
    if object_type == "audience":
        return _wrap("audience", action, {
            "name": payload.get("name"),
            "subtype": payload.get("subtype"),
            "locations": payload.get("locations", []),
            "interests": payload.get("interests", []),
            "custom_segments": payload.get("custom_segments", []),
            "remarketing_lists": payload.get("remarketing_lists", []),
        })
    if object_type == "schedule":
        return _wrap("campaign_criterion.schedule", action, {
            "days": payload.get("days", []),
            "windows": payload.get("windows", []),
            "timezone": payload.get("timezone"),
        })
    if object_type in {"asset", "extension"}:
        return _wrap("asset", action, {
            "asset_type": payload.get("asset_type"),
            "text": payload.get("text"),
            "final_urls": payload.get("final_urls", []),
            "call_to_action_text": payload.get("call_to_action_text"),
        })
    return _wrap(object_type, action, payload)

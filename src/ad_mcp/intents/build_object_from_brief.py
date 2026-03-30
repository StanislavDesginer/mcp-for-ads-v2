from __future__ import annotations

from typing import Any


def _compact(payload: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in payload.items() if value is not None}


def build_ad_group_payload_from_brief(provider: str, brief: dict[str, Any]) -> dict[str, Any]:
    payload = {
        "name": brief.get("name"),
        "campaign_id": brief.get("campaign_id"),
        "status": brief.get("status", "PAUSED" if provider != "google_ads" else "ENABLED"),
        "type": brief.get("type"),
        "placement_type": brief.get("placement_type"),
        "schedule_type": brief.get("schedule_type"),
        "cpc_bid_micros": brief.get("cpc_bid_micros"),
        "budget": brief.get("budget"),
        "daily_budget": brief.get("daily_budget"),
        "billing_event": brief.get("billing_event"),
        "optimization_goal": brief.get("optimization_goal"),
        "bid_strategy": brief.get("bid_strategy"),
        "targeting": brief.get("targeting", {}),
        "promoted_object": brief.get("promoted_object", {}),
        "region_ids": brief.get("region_ids", []),
    }
    return _compact(payload)


def build_ad_payload_from_brief(provider: str, brief: dict[str, Any]) -> dict[str, Any]:
    payload = {
        "name": brief.get("name"),
        "status": brief.get("status", "PAUSED"),
        "ad_group_id": brief.get("ad_group_id"),
        "adset_id": brief.get("adset_id"),
        "adgroup_id": brief.get("adgroup_id"),
        "final_urls": brief.get("final_urls", []),
        "headlines": brief.get("headlines", []),
        "descriptions": brief.get("descriptions", []),
        "path1": brief.get("path1"),
        "path2": brief.get("path2"),
        "creative": brief.get("creative", {}),
        "tracking_specs": brief.get("tracking_specs", []),
        "creative_material_mode": brief.get("creative_material_mode"),
        "creative_payload": brief.get("creative_payload", {}),
        "text_ad": brief.get("text_ad", {}),
    }
    return _compact(payload)


def build_keyword_payload_from_brief(brief: dict[str, Any]) -> dict[str, Any]:
    payload = {
        "text": brief.get("text"),
        "match_type": brief.get("match_type", "PHRASE"),
        "status": brief.get("status", "ENABLED"),
        "ad_group_id": brief.get("ad_group_id"),
        "cpc_bid_micros": brief.get("cpc_bid_micros"),
        "bid": brief.get("bid"),
        "priority": brief.get("priority"),
    }
    return _compact(payload)


def build_audience_payload_from_brief(provider: str, brief: dict[str, Any]) -> dict[str, Any]:
    payload = {
        "name": brief.get("name"),
        "subtype": brief.get("subtype"),
        "rule": brief.get("rule", {}),
        "retention_days": brief.get("retention_days"),
        "locations": brief.get("locations", []),
        "interests": brief.get("interests", []),
        "behaviors": brief.get("behaviors", []),
        "age_min": brief.get("age_min"),
        "age_max": brief.get("age_max"),
        "genders": brief.get("genders", []),
        "custom_segments": brief.get("custom_segments", []),
        "remarketing_lists": brief.get("remarketing_lists", []),
    }
    if provider == "google_ads":
        payload["subtype"] = payload.get("subtype", "custom_segment")
    elif provider == "meta_ads":
        payload["subtype"] = payload.get("subtype", "CUSTOM")
    return _compact(payload)


def build_schedule_payload_from_brief(brief: dict[str, Any]) -> dict[str, Any]:
    payload = {
        "timezone": brief.get("timezone"),
        "days": brief.get("days", []),
        "windows": brief.get("windows", []),
        "schedule_type": brief.get("schedule_type"),
        "start_time": brief.get("start_time"),
        "end_time": brief.get("end_time"),
    }
    return _compact(payload)

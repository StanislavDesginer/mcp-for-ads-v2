from __future__ import annotations

from typing import Any


def build_campaign_payload_from_brief(provider: str, brief: dict[str, Any]) -> dict[str, Any]:
    payload = {
        "name": brief.get("name"),
        "status": brief.get("status", "PAUSED"),
        "budget_micros": brief.get("budget_micros"),
        "daily_budget": brief.get("daily_budget"),
        "lifetime_budget": brief.get("lifetime_budget"),
        "campaign_type": brief.get("campaign_type"),
        "objective": brief.get("objective"),
        "objective_type": brief.get("objective_type"),
        "bidding_strategy": brief.get("bidding_strategy"),
        "start_date": brief.get("start_date"),
        "end_date": brief.get("end_date"),
        "targeting": brief.get("targeting", {}),
        "network_settings": brief.get("network_settings", {}),
    }
    if provider == "meta_ads" and not payload.get("objective"):
        payload["objective"] = "OUTCOME_SALES"
    if provider == "google_ads" and not payload.get("campaign_type"):
        payload["campaign_type"] = "search"
    if provider == "tiktok_ads" and not payload.get("objective_type"):
        payload["objective_type"] = "TRAFFIC"
    return {key: value for key, value in payload.items() if value is not None}

from __future__ import annotations


def _wrap(resource: str, action: str, body: dict) -> dict:
    method = {"create": "POST", "update": "PUT", "delete_or_archive": "POST"}.get(action, "POST")
    return {
        "resource": resource,
        "operation": action,
        "http_method": method,
        "endpoint": f"/yandex/{resource}",
        "body": body,
    }


def build_yandex_direct_payload(action: str, object_type: str, payload: dict) -> dict:
    if object_type == "campaign":
        return _wrap("Campaigns", action, {
            "Name": payload.get("name"),
            "StartDate": payload.get("start_date"),
            "TextCampaign": payload.get("text_campaign", {}),
            "DailyBudget": payload.get("daily_budget"),
        })
    if object_type == "ad_group":
        return _wrap("AdGroups", action, {
            "Name": payload.get("name"),
            "CampaignId": payload.get("campaign_id"),
            "RegionIds": payload.get("region_ids", []),
        })
    if object_type == "ad":
        return _wrap("Ads", action, {
            "AdGroupId": payload.get("ad_group_id"),
            "TextAd": payload.get("text_ad", {}),
            "Status": payload.get("status"),
        })
    if object_type == "keyword":
        return _wrap("Keywords", action, {
            "AdGroupId": payload.get("ad_group_id"),
            "Keyword": payload.get("text"),
            "Bid": payload.get("bid"),
            "StrategyPriority": payload.get("priority"),
        })
    if object_type == "audience":
        return _wrap("RetargetingLists", action, {
            "Name": payload.get("name"),
            "Rules": payload.get("rule", {}),
            "InterestCategories": payload.get("interests", []),
        })
    if object_type == "schedule":
        return _wrap("CampaignsSchedule", action, {
            "Days": payload.get("days", []),
            "Windows": payload.get("windows", []),
            "Timezone": payload.get("timezone"),
        })
    return _wrap(object_type, action, payload)

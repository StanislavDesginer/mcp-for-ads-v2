from __future__ import annotations

from typing import Any

from ad_mcp.core.models import ReportRequest, ReportResponse
from ad_mcp.core.normalization import split_requested_fields
from ad_mcp.providers.meta_ads.auth import MetaAccountCredentials

try:
    from facebook_business.adobjects.adaccount import AdAccount
    from facebook_business.adobjects.adsinsights import AdsInsights
    from facebook_business.api import FacebookAdsApi
except ImportError:  # pragma: no cover
    AdAccount = None
    AdsInsights = None
    FacebookAdsApi = None


META_FIELD_MAP = {
    "reach": "reach",
    "impressions": "impressions",
    "clicks": "inline_link_clicks",
    "spend": "spend",
    "ctr": "ctr",
}

ENTITY_NAME_FIELD = {
    "account": None,
    "campaign": "campaign_name",
    "adset": "adset_name",
    "ad": "ad_name",
}


def _safe_number(value: Any) -> float:
    if value in (None, ""):
        return 0.0
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _sum_action_values(actions: list[dict[str, Any]], allowed_types: list[str] | None = None) -> float:
    total = 0.0
    for action in actions:
        action_type = action.get("action_type")
        if allowed_types and action_type not in allowed_types:
            continue
        total += _safe_number(action.get("value"))
    return total


def _sum_video_values(video_actions: list[dict[str, Any]], allowed_types: list[str] | None = None) -> float:
    total = 0.0
    for action in video_actions:
        action_type = action.get("action_type")
        if allowed_types and action_type not in allowed_types:
            continue
        total += _safe_number(action.get("value"))
    return total


def fetch_meta_report(
    credentials: MetaAccountCredentials,
    request: ReportRequest,
    supported_metrics: list[str],
) -> ReportResponse:
    matched, unsupported = split_requested_fields(
        request.fields or supported_metrics,
        supported_metrics,
    )

    if FacebookAdsApi is None or AdAccount is None or AdsInsights is None:
        return ReportResponse(
            provider="meta_ads",
            entity_level=request.entity_level,
            date_range=request.date_range,
            rows=[],
            normalized_metrics=matched,
            native_metrics=[],
            unsupported_requested_fields=unsupported,
            source_api="meta_marketing_api",
            preview=True,
        )

    entity_name_key = ENTITY_NAME_FIELD.get(request.entity_level, "campaign_name")
    fields = [
        AdsInsights.Field.date_start,
        AdsInsights.Field.impressions,
        AdsInsights.Field.inline_link_clicks,
        AdsInsights.Field.spend,
        AdsInsights.Field.ctr,
        AdsInsights.Field.actions,
        AdsInsights.Field.video_thruplay_watched_actions,
        AdsInsights.Field.reach,
    ]
    if entity_name_key == "campaign_name":
        fields.append(AdsInsights.Field.campaign_name)
    elif entity_name_key == "adset_name":
        fields.append(AdsInsights.Field.adset_name)
    elif entity_name_key == "ad_name":
        fields.append(AdsInsights.Field.ad_name)

    FacebookAdsApi.init(
        credentials.app_id,
        credentials.app_secret,
        credentials.access_token,
        api_version=credentials.api_version,
    )
    insights = AdAccount(f"act_{credentials.account_id}").get_insights(
        fields=fields,
        params={
            "level": request.entity_level,
            "time_increment": 1,
            "time_range": {
                "since": request.date_range.start_date,
                "until": request.date_range.end_date,
            },
        },
    )

    rows: list[dict[str, Any]] = []
    for insight in insights:
        actions = insight.get(AdsInsights.Field.actions, [])
        video_actions = insight.get(AdsInsights.Field.video_thruplay_watched_actions, [])
        clicks = _safe_number(insight.get(AdsInsights.Field.inline_link_clicks))
        impressions = _safe_number(insight.get(AdsInsights.Field.impressions))
        spend = _safe_number(insight.get(AdsInsights.Field.spend))
        conversions = _sum_action_values(actions, credentials.action_metrics)
        interactions = clicks + _sum_video_values(video_actions, credentials.video_metrics)
        ctr = _safe_number(insight.get(AdsInsights.Field.ctr))
        cr = (conversions / clicks) if clicks else 0.0

        row: dict[str, Any] = {
            "date": insight.get(AdsInsights.Field.date_start),
            "account_id": credentials.account_id,
            "account_name": credentials.name,
            "reach": _safe_number(insight.get(AdsInsights.Field.reach)),
            "impressions": impressions,
            "interactions": interactions,
            "clicks": clicks,
            "spend": spend,
            "ctr": ctr,
            "cr": cr,
            "conversions": conversions,
        }
        if entity_name_key:
            row[request.entity_level] = insight.get(entity_name_key)
        rows.append({key: value for key, value in row.items() if key in matched or key in {"date", request.entity_level, "account_id", "account_name"}})

    return ReportResponse(
        provider="meta_ads",
        entity_level=request.entity_level,
        date_range=request.date_range,
        rows=rows,
        normalized_metrics=matched,
        native_metrics=[],
        unsupported_requested_fields=unsupported,
        source_api="meta_marketing_api",
        preview=False,
    )

from __future__ import annotations

from ad_mcp.core.models import ReportRequest, ReportResponse
from ad_mcp.core.models import CapabilityMap
from ad_mcp.providers.base.client import BaseAdsProvider
from ad_mcp.providers.tiktok_ads.payloads import build_tiktok_ads_payload
from ad_mcp.providers.tiktok_ads.reporting import build_tiktok_report_preview


class TikTokAdsProvider(BaseAdsProvider):
    def __init__(self, config: dict | None = None) -> None:
        super().__init__(
            capabilities=CapabilityMap(
                provider="tiktok_ads",
                read_objects=["account", "campaign", "adgroup", "ad", "audience"],
                write_objects=["campaign", "adgroup", "ad", "audience", "schedule"],
                supported_metrics=[
                    "reach",
                    "impressions",
                    "clicks",
                    "spend",
                    "ctr",
                    "cr",
                    "conversions",
                ],
                supported_dimensions=["date", "campaign", "adgroup", "ad", "placement"],
                supported_campaign_types=["traffic", "web_conversion", "app_promotion", "lead_generation", "product_sales"],
                supported_audience_types=["custom", "lookalike", "interest", "behavior"],
                notes=[
                    "Provider shape is based on current TikTok Marketing API patterns and external MCP references.",
                ],
            ),
            source_api="tiktok_marketing_api",
            config=config,
        )

    def get_report(self, request: ReportRequest) -> ReportResponse:
        return build_tiktok_report_preview(request, self.capabilities.supported_metrics)

    def build_provider_payload(self, action: str, account_id: str, object_type: str, payload: dict) -> dict:
        provider_payload = build_tiktok_ads_payload(action, object_type, payload)
        provider_payload["account_id"] = account_id
        return provider_payload

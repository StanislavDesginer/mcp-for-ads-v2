from __future__ import annotations

from ad_mcp.core.models import ReportRequest, ReportResponse
from ad_mcp.core.models import CapabilityMap
from ad_mcp.providers.base.client import BaseAdsProvider
from ad_mcp.providers.meta_ads.auth import credentials_from_config
from ad_mcp.providers.meta_ads.payloads import build_meta_ads_payload
from ad_mcp.providers.meta_ads.reporting import fetch_meta_report


class MetaAdsProvider(BaseAdsProvider):
    def __init__(self, config: dict | None = None) -> None:
        super().__init__(
            capabilities=CapabilityMap(
                provider="meta_ads",
                read_objects=["account", "campaign", "adset", "ad", "audience"],
                write_objects=["campaign", "adset", "ad", "creative", "audience", "schedule"],
                supported_metrics=[
                    "reach",
                    "impressions",
                    "interactions",
                    "clicks",
                    "spend",
                    "ctr",
                    "cr",
                    "conversions",
                ],
                supported_dimensions=["date", "campaign", "adset", "ad", "placement", "device_platform"],
                supported_campaign_types=["awareness", "traffic", "engagement", "leads", "sales", "app_promotion"],
                supported_audience_types=["saved", "custom", "lookalike"],
                notes=[
                    "Seeded from local reports-holymedia Meta scripts.",
                    "Real creative and audience creation still needs provider-native translators.",
                ],
            ),
            source_api="meta_marketing_api",
            config=config,
        )

    def get_report(self, request: ReportRequest) -> ReportResponse:
        account_config = self.get_account_config(request.account_id)
        if not account_config:
            return super().get_report(request)
        credentials = credentials_from_config(account_config)
        return fetch_meta_report(credentials, request, self.capabilities.supported_metrics)

    def build_provider_payload(self, action: str, account_id: str, object_type: str, payload: dict) -> dict:
        provider_payload = build_meta_ads_payload(action, object_type, payload)
        provider_payload["account_id"] = account_id
        return provider_payload

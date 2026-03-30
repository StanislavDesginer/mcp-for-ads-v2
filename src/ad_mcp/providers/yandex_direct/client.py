from __future__ import annotations

from ad_mcp.core.models import ReportRequest, ReportResponse
from ad_mcp.core.models import CapabilityMap
from ad_mcp.providers.base.client import BaseAdsProvider
from ad_mcp.providers.yandex_direct.payloads import build_yandex_direct_payload
from ad_mcp.providers.yandex_direct.reporting import build_yandex_report_preview


class YandexDirectProvider(BaseAdsProvider):
    def __init__(self, config: dict | None = None) -> None:
        super().__init__(
            capabilities=CapabilityMap(
                provider="yandex_direct",
                read_objects=["account", "campaign", "ad_group", "ad", "keyword"],
                write_objects=["campaign", "ad_group", "ad", "keyword", "schedule"],
                supported_metrics=[
                    "impressions",
                    "clicks",
                    "spend",
                    "ctr",
                    "cr",
                    "conversions",
                ],
                supported_dimensions=["date", "campaign", "ad_group", "ad", "keyword", "device"],
                supported_campaign_types=["text", "mobile_app", "smart_banner", "master_campaign", "performance"],
                supported_audience_types=["retargeting", "interests", "geo"],
                notes=[
                    "Seeded from local Yandex reporting script.",
                    "Capabilities are intentionally conservative until the native provider is implemented.",
                ],
            ),
            source_api="yandex_direct_api",
            config=config,
        )

    def get_report(self, request: ReportRequest) -> ReportResponse:
        return build_yandex_report_preview(request, self.capabilities.supported_metrics)

    def build_provider_payload(self, action: str, account_id: str, object_type: str, payload: dict) -> dict:
        provider_payload = build_yandex_direct_payload(action, object_type, payload)
        provider_payload["account_id"] = account_id
        return provider_payload

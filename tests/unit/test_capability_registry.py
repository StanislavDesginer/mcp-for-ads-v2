from ad_mcp.core.capability_registry import CapabilityRegistry
from ad_mcp.providers.google_ads.client import GoogleAdsProvider
from ad_mcp.providers.meta_ads.client import MetaAdsProvider
from ad_mcp.providers.tiktok_ads.client import TikTokAdsProvider
from ad_mcp.providers.yandex_direct.client import YandexDirectProvider


def test_registry_lists_all_providers() -> None:
    registry = CapabilityRegistry(
        {
            "google_ads": GoogleAdsProvider(),
            "meta_ads": MetaAdsProvider(),
            "tiktok_ads": TikTokAdsProvider(),
            "yandex_direct": YandexDirectProvider(),
        }
    )

    assert registry.list_providers() == [
        "google_ads",
        "meta_ads",
        "tiktok_ads",
        "yandex_direct",
    ]


def test_google_capabilities_include_quality_metrics() -> None:
    registry = CapabilityRegistry({"google_ads": GoogleAdsProvider()})

    capabilities = registry.get_capabilities("google_ads")

    assert "quality_score" in capabilities.supported_metrics
    assert "lost_impression_share" in capabilities.supported_metrics

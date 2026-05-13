from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from ad_mcp.core.auth_manager import AuthManager
from ad_mcp.core.audit_logger import AuditLogger
from ad_mcp.core.capability_registry import CapabilityRegistry
from ad_mcp.core.config_loader import load_provider_from_connections, load_safety_policy
from ad_mcp.core.policy import PolicyManager
from ad_mcp.core.preview_manager import PreviewManager
from ad_mcp.providers.google_ads.client import GoogleAdsProvider
from ad_mcp.providers.meta_ads.client import MetaAdsProvider
from ad_mcp.providers.tiktok_ads.client import TikTokAdsProvider
from ad_mcp.providers.yandex_direct.client import YandexDirectProvider
from ad_mcp.settings import Settings
from ad_mcp.tools.account_read import build_account_read_tools
from ad_mcp.tools.analytics_read import build_analytics_read_tools
from ad_mcp.tools.billing import build_billing_tools
from ad_mcp.tools.discovery import build_discovery_tools
from ad_mcp.tools.intents import build_intent_tools
from ad_mcp.tools.meta_specialist import build_meta_specialist_tools
from ad_mcp.tools.objects import build_object_tools
from ad_mcp.tools.reporting import build_reporting_tools
from ad_mcp.tools.write_commit import build_write_commit_tools
from ad_mcp.tools.write_preview import build_write_preview_tools


def create_server() -> FastMCP:
    settings = Settings()
    settings.audit_log_file.parent.mkdir(parents=True, exist_ok=True)
    audit_logger = AuditLogger(settings.audit_log_file)
    policy_manager = PolicyManager(load_safety_policy(settings.policy_config_path))

    provider_configs = {
        "google_ads": load_provider_from_connections(settings.connections_config_path, "google_ads"),
        "meta_ads": load_provider_from_connections(settings.connections_config_path, "meta_ads"),
        "tiktok_ads": load_provider_from_connections(settings.connections_config_path, "tiktok_ads"),
        "yandex_direct": load_provider_from_connections(settings.connections_config_path, "yandex_direct"),
    }
    providers = {
        "google_ads": GoogleAdsProvider(config=provider_configs["google_ads"]),
        "meta_ads": MetaAdsProvider(config=provider_configs["meta_ads"]),
        "tiktok_ads": TikTokAdsProvider(config=provider_configs["tiktok_ads"]),
        "yandex_direct": YandexDirectProvider(config=provider_configs["yandex_direct"]),
    }
    registry = CapabilityRegistry(providers=providers)
    preview_manager = PreviewManager()
    auth_manager = AuthManager(
        secrets_dir=settings.project_root / "secrets",
        tokens_dir=settings.project_root / "tokens",
    )

    mcp = FastMCP("mcp-for-ads")
    toolsets = [
        build_discovery_tools(registry),
        build_billing_tools(registry, policy_manager),
        build_account_read_tools(registry, policy_manager),
        build_analytics_read_tools(registry, policy_manager),
        build_reporting_tools(registry, policy_manager),
        build_object_tools(registry, policy_manager),
        build_write_preview_tools(registry, preview_manager, audit_logger, policy_manager),
        build_write_commit_tools(registry, preview_manager, audit_logger, policy_manager),
        build_intent_tools(registry, preview_manager, policy_manager),
        build_meta_specialist_tools(registry, preview_manager, policy_manager),
    ]
    for toolset in toolsets:
        for name, func in toolset.items():
            mcp.tool(name=name)(func)

    @mcp.tool(name="describe_auth_strategy")
    def describe_auth_strategy(provider: str) -> dict:
        return auth_manager.describe_auth_strategy(provider)

    return mcp


def main() -> None:
    create_server().run()


if __name__ == "__main__":
    main()

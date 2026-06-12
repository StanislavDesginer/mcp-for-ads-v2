from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

from ad_mcp.core.auth_manager import AuthManager
from ad_mcp.core.audit_logger import AuditLogger
from ad_mcp.core.capability_registry import CapabilityRegistry
from ad_mcp.core.config_loader import load_safety_policy
from ad_mcp.core.connection_store import load_runtime_provider_configs
from ad_mcp.core.policy import PolicyManager
from ad_mcp.core.preview_manager import PreviewManager
from ad_mcp.providers.google_ads.client import GoogleAdsProvider
from ad_mcp.providers.meta_ads.client import MetaAdsProvider
from ad_mcp.providers.tiktok_ads.client import TikTokAdsProvider
from ad_mcp.providers.yandex_direct.client import YandexDirectProvider
from ad_mcp.mcp_auth import build_mcp_auth
from ad_mcp.settings import Settings
from ad_mcp.tools.account_read import build_account_read_tools
from ad_mcp.tools.analytics_read import build_analytics_read_tools
from ad_mcp.tools.beta_read import build_beta_read_tools
from ad_mcp.tools.billing import build_billing_tools
from ad_mcp.tools.discovery import build_discovery_tools
from ad_mcp.tools.intents import build_intent_tools
from ad_mcp.tools.meta_specialist import build_meta_specialist_tools
from ad_mcp.tools.mcp_skill_presets import build_mcp_skill_preset_tools
from ad_mcp.tools.objects import build_object_tools
from ad_mcp.tools.reporting import build_reporting_tools
from ad_mcp.tools.write_commit import build_write_commit_tools
from ad_mcp.tools.write_preview import build_write_preview_tools


def _safe_account_summary(account: dict[str, Any]) -> dict[str, Any]:
    return {
        "name": account.get("name"),
        "account_id": account.get("account_id"),
        "status": account.get("status"),
    }


def _provider_diagnostics(registry: CapabilityRegistry, provider_configs: dict[str, dict[str, Any]]) -> dict[str, Any]:
    diagnostics: dict[str, Any] = {}
    for provider_name, provider_config in provider_configs.items():
        accounts = provider_config.get("accounts", [])
        capabilities = registry.get_capabilities(provider_name)
        diagnostics[provider_name] = {
            "account_count": len(accounts),
            "accounts": [_safe_account_summary(account) for account in accounts],
            "capability_counts": {
                "read_objects": len(capabilities.read_objects),
                "write_objects": len(capabilities.write_objects),
                "supported_metrics": len(capabilities.supported_metrics),
                "supported_dimensions": len(capabilities.supported_dimensions),
                "supported_campaign_types": len(capabilities.supported_campaign_types),
                "supported_audience_types": len(capabilities.supported_audience_types),
            },
            "notes": capabilities.notes,
        }
    return diagnostics


def create_server(settings: Settings | None = None, *, hosted_http: bool = False) -> FastMCP:
    settings = settings or Settings()
    settings.audit_log_file.parent.mkdir(parents=True, exist_ok=True)
    audit_logger = AuditLogger(settings.audit_log_file)
    policy_manager = PolicyManager(load_safety_policy(settings.policy_config_path))

    provider_configs, provider_sources = load_runtime_provider_configs(settings)
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

    auth_settings = None
    token_verifier = None
    if hosted_http:
        auth_settings, token_verifier = build_mcp_auth(settings)
    mcp = FastMCP(
        "AdForge MCP",
        host=settings.mcp_http_host,
        port=settings.mcp_http_port,
        streamable_http_path=settings.mcp_route_path,
        auth=auth_settings,
        token_verifier=token_verifier,
    )
    toolsets = [
        build_discovery_tools(registry),
        build_beta_read_tools(registry, policy_manager, settings),
        build_billing_tools(registry, policy_manager),
        build_account_read_tools(registry, policy_manager),
        build_analytics_read_tools(registry, policy_manager),
        build_reporting_tools(registry, policy_manager),
        build_object_tools(registry, policy_manager),
        build_write_preview_tools(registry, preview_manager, audit_logger, policy_manager),
        build_write_commit_tools(registry, preview_manager, audit_logger, policy_manager),
        build_intent_tools(registry, preview_manager, policy_manager),
        build_meta_specialist_tools(registry, preview_manager, policy_manager),
        build_mcp_skill_preset_tools(registry, policy_manager),
    ]
    for toolset in toolsets:
        for name, func in toolset.items():
            mcp.tool(name=name)(func)

    @mcp.tool(name="describe_auth_strategy")
    def describe_auth_strategy(provider: str) -> dict:
        return auth_manager.describe_auth_strategy(provider)

    @mcp.tool(name="get_beta_diagnostics")
    def get_beta_diagnostics() -> dict:
        return {
            "status": "ok",
            "environment": settings.env,
            "config": {
                "connections_config": {
                    "file": settings.connections_config_path.name,
                    "exists": settings.connections_config_path.exists(),
                },
                "connection_store": {
                    "file": settings.connection_store_file.name,
                    "exists": settings.connection_store_file.exists(),
                    "fallback_to_local": settings.connections_fallback_to_local,
                    "provider_sources": provider_sources,
                },
                "policy_config": {
                    "file": settings.policy_config_path.name,
                    "exists": settings.policy_config_path.exists(),
                },
            },
            "security": {
                "web_api_token_configured": bool(settings.web_api_token),
                "write_mode": policy_manager.policy.write_mode,
                "execution_mode": policy_manager.policy.execution_mode,
                "allow_unknown_accounts": policy_manager.policy.allow_unknown_accounts,
                "require_confirm_for": policy_manager.policy.require_confirm_for,
            },
            "providers": _provider_diagnostics(registry, provider_configs),
            "smoke_checks": {
                "server_imports": True,
                "tools_register": True,
                "diagnostics_available": True,
                "live_writes_enabled": policy_manager.policy.execution_mode != "simulated_no_write",
            },
        }

    return mcp


def main() -> None:
    create_server().run()


if __name__ == "__main__":
    main()

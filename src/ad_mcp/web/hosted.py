from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ad_mcp.core.config_loader import load_provider_from_connections
from ad_mcp.settings import Settings


@dataclass(frozen=True)
class PlatformDescriptor:
    provider: str
    label: str
    beta_priority: str
    oauth_target: bool


PLATFORMS = (
    PlatformDescriptor("meta_ads", "Meta Ads", "beta", True),
    PlatformDescriptor("google_ads", "Google Ads", "beta", True),
    PlatformDescriptor("tiktok_ads", "TikTok Ads", "later", False),
    PlatformDescriptor("yandex_direct", "Yandex Direct", "later", False),
)

OAUTH_REDIRECT_SETTINGS = {
    "meta_ads": "meta_oauth_redirect_path",
    "google_ads": "google_oauth_redirect_path",
}

SECRET_KEYS = {
    "access_token",
    "app_secret",
    "client_secret",
    "developer_token",
    "oauth_client_secret",
    "refresh_token",
    "secret",
}


def _route_path(path: str) -> str:
    clean = (path or "/mcp").strip()
    if not clean.startswith("/"):
        clean = f"/{clean}"
    return clean


def _join_url(base_url: str, path: str) -> str:
    base = base_url.rstrip("/")
    route = _route_path(path)
    if not base:
        return route
    return f"{base}{route}"


def _safe_account(account: dict[str, Any]) -> dict[str, Any]:
    safe: dict[str, Any] = {}
    for key in ("name", "account_id", "customer_id", "login_customer_id", "advertiser_id", "login", "status"):
        value = account.get(key)
        if value is not None:
            safe[key] = str(value)
    safe["credentials_present"] = any(account.get(key) for key in SECRET_KEYS)
    return safe


def _load_json_file(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8")) or {}
    except (OSError, json.JSONDecodeError):
        return {"_error": "connection_store_unreadable"}


class HostedConnectionService:
    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or Settings()

    def _public_base_url(self) -> str:
        return self._settings.public_base_or_local_mcp_url

    def mcp_connection_info(self) -> dict[str, Any]:
        endpoint_path = self._settings.mcp_route_path
        public_url = self._settings.public_mcp_url
        return {
            "name": "AdForge MCP",
            "transport": "streamable_http",
            "endpoint_path": endpoint_path,
            "url": public_url,
            "auth": {
                "type": "bearer",
                "header": "Authorization",
                "token_env": "ADFORGE_MCP_CLIENT_TOKEN",
            },
            "client_notes": {
                "codex": "Use the Streamable HTTP/custom MCP server option and set the URL plus bearer token.",
                "claude": "Add AdForge MCP as a custom connector with Name and URL, then allow the requested tools.",
                "gemini": "Use the client-specific custom connector flow once available.",
            },
            "status": "transport_available",
            "message": "Hosted Streamable HTTP MCP transport is available at this URL.",
        }

    def connections(self) -> dict[str, Any]:
        store = _load_json_file(self._settings.connection_store_file)
        stored_connections = store.get("connections", {}) if isinstance(store.get("connections", {}), dict) else {}
        platforms = [self._platform_status(platform, stored_connections.get(platform.provider, {})) for platform in PLATFORMS]
        return {
            "mode": "hosted_oauth_beta",
            "mcp": self.mcp_connection_info(),
            "connection_store": {
                "configured": self._settings.connection_store_file.exists(),
                "path": self._settings.connection_store_path,
                "readable": "_error" not in store,
            },
            "platforms": platforms,
        }

    def oauth_start_preview(self, provider: str) -> dict[str, Any]:
        known = {platform.provider: platform for platform in PLATFORMS}
        if provider not in known:
            return {"provider": provider, "status": "unsupported_provider"}
        platform = known[provider]
        if not platform.oauth_target:
            return {
                "provider": platform.provider,
                "label": platform.label,
                "status": "planned_later",
                "message": "This platform is outside the first beta OAuth scope.",
            }
        return {
            "provider": platform.provider,
            "label": platform.label,
            "status": "oauth_not_configured",
            "redirect_url": _join_url(self._public_base_url(), self._oauth_redirect_path(platform.provider)),
            "message": "OAuth app credentials and callback handling are the next implementation step.",
        }

    def mcp_transport_placeholder(self) -> dict[str, Any]:
        info = self.mcp_connection_info()
        return {
            "error": "This legacy web process does not serve MCP traffic. Run ad-mcp-http or route /mcp to the hosted MCP process.",
            "code": "mcp_transport_on_separate_process",
            "mcp": info,
        }

    def _platform_status(self, platform: PlatformDescriptor, stored: Any) -> dict[str, Any]:
        provider_config = load_provider_from_connections(self._settings.connections_config_path, platform.provider)
        accounts = provider_config.get("accounts", [])
        safe_accounts = [_safe_account(account) for account in accounts if isinstance(account, dict)]
        stored_accounts = stored.get("accounts", []) if isinstance(stored, dict) else []
        has_oauth_connection = bool(stored_accounts)
        has_dev_config = bool(safe_accounts)
        if has_oauth_connection:
            status = "connected"
            source = "oauth_store"
        elif has_dev_config:
            status = "development_configured"
            source = "ads_config"
        elif platform.oauth_target:
            status = "ready_for_oauth"
            source = "none"
        else:
            status = "planned_later"
            source = "none"
        return {
            "provider": platform.provider,
            "label": platform.label,
            "beta_priority": platform.beta_priority,
            "oauth_target": platform.oauth_target,
            "status": status,
            "source": source,
            "accounts": safe_accounts,
        }

    def _oauth_redirect_path(self, provider: str) -> str:
        setting_name = OAUTH_REDIRECT_SETTINGS.get(provider)
        if not setting_name:
            return f"/oauth/{provider}/callback"
        return str(getattr(self._settings, setting_name))

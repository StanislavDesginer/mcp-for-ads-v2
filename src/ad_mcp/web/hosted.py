from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ad_mcp.core.config_loader import load_provider_from_connections
from ad_mcp.core.connection_store import HostedConnectionStore, safe_account_summary
from ad_mcp.settings import Settings
from ad_mcp.web.meta_oauth import MetaOAuthService
from ad_mcp.web.partner_oauth import GoogleOAuthService, TikTokOAuthService, YandexOAuthService


@dataclass(frozen=True)
class PlatformDescriptor:
    provider: str
    label: str
    beta_priority: str
    oauth_target: bool


PLATFORMS = (
    PlatformDescriptor("meta_ads", "Meta Ads", "beta", True),
    PlatformDescriptor("google_ads", "Google Ads", "beta", True),
    PlatformDescriptor("tiktok_ads", "TikTok Ads", "next", True),
    PlatformDescriptor("yandex_direct", "Yandex Direct", "next", True),
)

OAUTH_REDIRECT_SETTINGS = {
    "meta_ads": "meta_oauth_redirect_path",
    "google_ads": "google_oauth_redirect_path",
    "tiktok_ads": "tiktok_oauth_redirect_path",
    "yandex_direct": "yandex_oauth_redirect_path",
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


class HostedConnectionService:
    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or Settings()
        self._store = HostedConnectionStore(self._settings.connection_store_file)
        self._meta_oauth = MetaOAuthService(self._settings)
        self._google_oauth = GoogleOAuthService(self._settings)
        self._tiktok_oauth = TikTokOAuthService(self._settings)
        self._yandex_oauth = YandexOAuthService(self._settings)

    def _public_base_url(self) -> str:
        return self._settings.public_base_or_local_web_url

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
        platforms = [self._platform_status(platform) for platform in PLATFORMS]
        return {
            "mode": "hosted_oauth_beta",
            "mcp": self.mcp_connection_info(),
            "connection_store": self._store.status() | {"path": self._settings.connection_store_path},
            "platforms": platforms,
        }

    def import_local_provider(self, provider: str) -> dict[str, Any]:
        if provider not in {platform.provider for platform in PLATFORMS}:
            return {"provider": provider, "status": "unsupported_provider"}
        if not self._settings.connections_config_path.exists():
            return {"provider": provider, "status": "no_local_config"}
        provider_config = load_provider_from_connections(self._settings.connections_config_path, provider)
        accounts = provider_config.get("accounts", [])
        if not accounts:
            return {"provider": provider, "status": "no_local_accounts"}
        saved = self._store.save_provider_config(provider, provider_config, source="local_import")
        return {
            "provider": provider,
            "status": "imported",
            "source": "local_connections_config",
            "accounts": saved["accounts"],
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
        service = self._oauth_service(provider)
        configured = service.configured() if service is not None else False
        return {
            "provider": platform.provider,
            "label": platform.label,
            "status": "oauth_ready" if configured else "oauth_not_configured",
            "redirect_url": _join_url(self._public_base_url(), self._oauth_redirect_path(platform.provider)),
            "message": "OAuth can start when app credentials are configured.",
        }

    def meta_oauth_redirect_url(self) -> str:
        return self._meta_oauth.authorization_url()

    def meta_oauth_callback(self, query: dict[str, str]) -> dict[str, Any]:
        return self._meta_oauth.handle_callback(query)

    def meta_oauth_pending(self, pending_id: str) -> dict[str, Any]:
        return self._meta_oauth.pending_selection(pending_id)

    def meta_oauth_select(self, payload: dict[str, Any]) -> dict[str, Any]:
        pending_id = str(payload["pending_id"])
        account_ids = payload.get("account_ids") or []
        return self._meta_oauth.select_accounts(pending_id, [str(item) for item in account_ids])

    def oauth_redirect_url(self, provider: str) -> str:
        service = self._require_oauth_service(provider)
        return service.authorization_url()

    def oauth_authorization_info(self, provider: str) -> dict[str, Any]:
        service = self._require_oauth_service(provider)
        return {
            "provider": provider,
            "status": "oauth_ready",
            "authorization_url": service.authorization_url(),
        }

    def oauth_callback(self, provider: str, query: dict[str, str]) -> dict[str, Any]:
        service = self._require_oauth_service(provider)
        return service.handle_callback(query)

    def oauth_pending(self, provider: str, pending_id: str) -> dict[str, Any]:
        service = self._require_oauth_service(provider)
        return service.pending_selection(pending_id)

    def oauth_select(self, provider: str, payload: dict[str, Any]) -> dict[str, Any]:
        service = self._require_oauth_service(provider)
        pending_id = str(payload["pending_id"])
        account_ids = payload.get("account_ids") or []
        return service.select_accounts(pending_id, [str(item) for item in account_ids])

    def mcp_transport_placeholder(self) -> dict[str, Any]:
        info = self.mcp_connection_info()
        return {
            "error": "This legacy web process does not serve MCP traffic. Run ad-mcp-http or route /mcp to the hosted MCP process.",
            "code": "mcp_transport_on_separate_process",
            "mcp": info,
        }

    def _platform_status(self, platform: PlatformDescriptor) -> dict[str, Any]:
        hosted_config = self._store.provider_config(platform.provider)
        hosted_accounts = hosted_config.get("accounts", [])
        provider_config = load_provider_from_connections(self._settings.connections_config_path, platform.provider)
        accounts = provider_config.get("accounts", [])
        safe_accounts = [safe_account_summary(account) for account in hosted_accounts if isinstance(account, dict)]
        local_safe_accounts = [safe_account_summary(account) for account in accounts if isinstance(account, dict)]
        has_oauth_connection = bool(hosted_accounts)
        if has_oauth_connection:
            status = "connected"
            source = "hosted_connection_store"
        elif local_safe_accounts and self._settings.connections_fallback_to_local:
            status = "development_configured"
            source = "local_connections_config"
            safe_accounts = local_safe_accounts
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

    def _oauth_service(self, provider: str):
        services = {
            "meta_ads": self._meta_oauth,
            "google_ads": self._google_oauth,
            "tiktok_ads": self._tiktok_oauth,
            "yandex_direct": self._yandex_oauth,
        }
        return services.get(provider)

    def _require_oauth_service(self, provider: str):
        service = self._oauth_service(provider)
        if service is None:
            raise ValueError(f"OAuth flow is not implemented for provider: {provider}")
        return service

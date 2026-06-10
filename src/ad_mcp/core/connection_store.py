from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Any

from ad_mcp.core.config_loader import load_provider_from_connections

if TYPE_CHECKING:
    from ad_mcp.settings import Settings


PROVIDER_NAMES = ("google_ads", "meta_ads", "tiktok_ads", "yandex_direct")

SECRET_KEYS = {
    "access_token",
    "app_secret",
    "client_secret",
    "developer_token",
    "oauth_client_secret",
    "refresh_token",
    "secret",
}

SAFE_ACCOUNT_KEYS = (
    "name",
    "account_id",
    "customer_id",
    "login_customer_id",
    "advertiser_id",
    "login",
    "status",
)


def safe_account_summary(account: dict[str, Any]) -> dict[str, Any]:
    safe: dict[str, Any] = {}
    for key in SAFE_ACCOUNT_KEYS:
        value = account.get(key)
        if value is not None:
            safe[key] = str(value)
    credentials = account.get("credentials") if isinstance(account.get("credentials"), dict) else {}
    safe["credentials_present"] = any(account.get(key) for key in SECRET_KEYS) or any(credentials.get(key) for key in SECRET_KEYS)
    return safe


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8")) or {}
    except (OSError, json.JSONDecodeError):
        return {"_error": "connection_store_unreadable"}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _normalize_account(provider: str, account: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(account)
    if provider == "google_ads" and not normalized.get("account_id") and normalized.get("customer_id"):
        normalized["account_id"] = normalized["customer_id"]
    if provider == "tiktok_ads" and not normalized.get("account_id") and normalized.get("advertiser_id"):
        normalized["account_id"] = normalized["advertiser_id"]
    return normalized


def _runtime_account(provider: str, account: dict[str, Any]) -> dict[str, Any]:
    account = _normalize_account(provider, account)
    credentials = account.get("credentials") if isinstance(account.get("credentials"), dict) else {}
    flattened = {key: value for key, value in account.items() if key != "credentials"}
    flattened.update(credentials)
    return flattened


def _stored_account(provider: str, account: dict[str, Any]) -> dict[str, Any]:
    account = _normalize_account(provider, account)
    stored: dict[str, Any] = {}
    credentials: dict[str, Any] = {}
    for key, value in account.items():
        if key in SECRET_KEYS:
            credentials[key] = value
        else:
            stored[key] = value
    existing_credentials = account.get("credentials")
    if isinstance(existing_credentials, dict):
        credentials.update(existing_credentials)
    if credentials:
        stored["credentials"] = credentials
    return stored


class HostedConnectionStore:
    def __init__(self, path: Path) -> None:
        self.path = path

    def read(self) -> dict[str, Any]:
        return _read_json(self.path)

    def status(self) -> dict[str, Any]:
        data = self.read()
        return {
            "configured": self.path.exists(),
            "path": str(self.path),
            "readable": "_error" not in data,
            "version": data.get("version") if isinstance(data, dict) else None,
        }

    def provider_config(self, provider: str) -> dict[str, Any]:
        data = self.read()
        connection = (data.get("connections", {}) if isinstance(data.get("connections", {}), dict) else {}).get(provider, {})
        if not isinstance(connection, dict):
            return {"provider": provider, "accounts": []}
        config = {key: value for key, value in connection.items() if key not in {"accounts", "created_at", "updated_at", "source"}}
        config["provider"] = provider
        accounts = connection.get("accounts", [])
        config["accounts"] = [_runtime_account(provider, account) for account in accounts if isinstance(account, dict)]
        return config

    def safe_provider_status(self, provider: str) -> dict[str, Any]:
        config = self.provider_config(provider)
        return {
            "provider": provider,
            "accounts": [safe_account_summary(account) for account in config.get("accounts", [])],
        }

    def save_provider_config(self, provider: str, provider_config: dict[str, Any], source: str = "dashboard_oauth") -> dict[str, Any]:
        if provider not in PROVIDER_NAMES:
            raise ValueError(f"Unsupported provider: {provider}")
        data = self.read()
        if "_error" in data:
            data = {}
        connections = data.setdefault("connections", {})
        if not isinstance(connections, dict):
            connections = {}
            data["connections"] = connections
        previous = connections.get(provider, {}) if isinstance(connections.get(provider, {}), dict) else {}
        stored = {key: value for key, value in provider_config.items() if key not in {"accounts"}}
        stored["provider"] = provider
        stored["source"] = source
        stored["created_at"] = previous.get("created_at") or _now_iso()
        stored["updated_at"] = _now_iso()
        stored["accounts"] = [_stored_account(provider, account) for account in provider_config.get("accounts", []) if isinstance(account, dict)]
        connections[provider] = stored
        data["version"] = int(data.get("version") or 1)
        self._write(data)
        return self.safe_provider_status(provider)

    def _write(self, data: dict[str, Any]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = self.path.with_suffix(f"{self.path.suffix}.tmp")
        tmp_path.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        tmp_path.replace(self.path)


def load_runtime_provider_configs(settings: "Settings") -> tuple[dict[str, dict[str, Any]], dict[str, str]]:
    store = HostedConnectionStore(settings.connection_store_file)
    configs: dict[str, dict[str, Any]] = {}
    sources: dict[str, str] = {}
    for provider in PROVIDER_NAMES:
        hosted_config = store.provider_config(provider)
        if hosted_config.get("accounts"):
            configs[provider] = hosted_config
            sources[provider] = "hosted_connection_store"
            continue
        if settings.connections_fallback_to_local:
            local_config = load_provider_from_connections(settings.connections_config_path, provider)
            configs[provider] = local_config
            if local_config.get("accounts"):
                sources[provider] = "local_connections_config" if settings.connections_config_path.exists() else "local_connections_example"
            else:
                sources[provider] = "empty"
        else:
            configs[provider] = {"provider": provider, "accounts": []}
            sources[provider] = "empty"
    return configs, sources

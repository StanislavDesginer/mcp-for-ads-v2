from __future__ import annotations

import json
from pathlib import Path

from ad_mcp.core.connection_store import HostedConnectionStore, load_runtime_provider_configs
from ad_mcp.settings import Settings


def test_connection_store_saves_secrets_but_returns_safe_status(tmp_path: Path) -> None:
    store = HostedConnectionStore(tmp_path / "tokens" / "connections.json")

    status = store.save_provider_config(
        "meta_ads",
        {
            "provider": "meta_ads",
            "accounts": [
                {
                    "name": "Client Meta",
                    "account_id": "act_123",
                    "status": "connected",
                    "app_id": "app-id",
                    "app_secret": "app-secret",
                    "access_token": "access-token",
                }
            ],
        },
        source="dashboard_oauth",
    )
    runtime_config = store.provider_config("meta_ads")
    serialized_status = json.dumps(status)

    assert runtime_config["accounts"][0]["access_token"] == "access-token"
    assert runtime_config["accounts"][0]["app_secret"] == "app-secret"
    assert "access-token" not in serialized_status
    assert "app-secret" not in serialized_status
    assert status["accounts"][0]["credentials_present"] is True


def test_runtime_provider_configs_prefer_hosted_store_over_local_config(tmp_path: Path) -> None:
    local_config = tmp_path / "ads_config.yaml"
    local_config.write_text(
        """
providers:
  meta_ads:
    provider: meta_ads
    accounts:
      - name: Local Meta
        account_id: local_1
        status: configured
""",
        encoding="utf-8",
    )
    settings = Settings(project_root=tmp_path, connections_config="ads_config.yaml", connection_store_path="tokens/connections.json")
    store = HostedConnectionStore(settings.connection_store_file)
    store.save_provider_config(
        "meta_ads",
        {"provider": "meta_ads", "accounts": [{"name": "Hosted Meta", "account_id": "hosted_1", "status": "connected"}]},
    )

    configs, sources = load_runtime_provider_configs(settings)

    assert sources["meta_ads"] == "hosted_connection_store"
    assert configs["meta_ads"]["accounts"][0]["name"] == "Hosted Meta"


def test_runtime_provider_configs_can_disable_local_fallback(tmp_path: Path) -> None:
    local_config = tmp_path / "ads_config.yaml"
    local_config.write_text(
        """
providers:
  meta_ads:
    provider: meta_ads
    accounts:
      - name: Local Meta
        account_id: local_1
""",
        encoding="utf-8",
    )
    settings = Settings(project_root=tmp_path, connections_config="ads_config.yaml", connections_fallback_to_local=False)

    configs, sources = load_runtime_provider_configs(settings)

    assert sources["meta_ads"] == "empty"
    assert configs["meta_ads"]["accounts"] == []


def test_google_customer_id_becomes_account_id_for_oauth_store(tmp_path: Path) -> None:
    store = HostedConnectionStore(tmp_path / "tokens" / "connections.json")
    store.save_provider_config(
        "google_ads",
        {
            "provider": "google_ads",
            "accounts": [
                {
                    "name": "Google Client",
                    "customer_id": "123-456-7890",
                    "refresh_token": "refresh-token",
                }
            ],
        },
    )

    config = store.provider_config("google_ads")

    assert config["accounts"][0]["account_id"] == "123-456-7890"


def test_safe_account_summary_keeps_provider_metadata_without_secrets(tmp_path: Path) -> None:
    store = HostedConnectionStore(tmp_path / "tokens" / "connections.json")
    store.save_provider_config(
        "tiktok_ads",
        {
            "provider": "tiktok_ads",
            "accounts": [
                {
                    "name": "TikTok Advertiser",
                    "account_id": "744",
                    "advertiser_id": "744",
                    "app_name": "AdForge MCP",
                    "app_id": "app-id",
                    "verification_status": "Approved",
                    "requested_permissions": ["Reporting", "Ads Management"],
                    "secret": "tiktok-secret",
                }
            ],
        },
    )
    store.save_provider_config(
        "yandex_direct",
        {
            "provider": "yandex_direct",
            "accounts": [
                {
                    "name": "Yandex Client",
                    "account_id": "client-login",
                    "login": "agency-login",
                    "direct_client_login": "client-login",
                    "api_access_status": "opened",
                    "api_points": 32000,
                    "access_token": "yandex-token",
                }
            ],
        },
    )

    tiktok = store.safe_provider_status("tiktok_ads")["accounts"][0]
    yandex = store.safe_provider_status("yandex_direct")["accounts"][0]
    serialized = json.dumps({"tiktok": tiktok, "yandex": yandex})

    assert tiktok["app_name"] == "AdForge MCP"
    assert tiktok["verification_status"] == "Approved"
    assert tiktok["requested_permissions"] == ["Reporting", "Ads Management"]
    assert yandex["direct_client_login"] == "client-login"
    assert yandex["api_access_status"] == "opened"
    assert yandex["api_points"] == "32000"
    assert "tiktok-secret" not in serialized
    assert "yandex-token" not in serialized

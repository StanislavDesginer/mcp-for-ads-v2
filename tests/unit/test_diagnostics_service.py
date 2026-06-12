from __future__ import annotations

import json
from pathlib import Path

import pytest
from mcp.types import TextContent

from ad_mcp.core.connection_store import HostedConnectionStore
from ad_mcp.server import create_server
from ad_mcp.settings import Settings
from ad_mcp.web.diagnostics import DiagnosticsService


def test_diagnostics_reports_missing_env_and_redacts_secrets(tmp_path: Path) -> None:
    settings = Settings(
        project_root=tmp_path,
        public_base_url="https://mcp.adforge.dev",
        connection_store_path="tokens/connections.json",
        connections_fallback_to_local=False,
        google_oauth_client_id="client-id",
        google_oauth_client_secret="client-secret",
        google_ads_developer_token="developer-token",
    )
    HostedConnectionStore(settings.connection_store_file).save_provider_config(
        "google_ads",
        {
            "provider": "google_ads",
            "accounts": [
                {
                    "account_id": "1234567890",
                    "name": "Google Client",
                    "refresh_token": "refresh-secret",
                    "developer_token": "developer-token",
                    "oauth_client_secret": "client-secret",
                }
            ],
        },
    )

    payload = DiagnosticsService(settings).overview()
    text = str(payload)

    assert payload["backend"]["status"] == "ok"
    assert payload["connections"]["storage"]["valid_format"] is True
    assert "client-secret" not in text
    assert "developer-token" not in text
    assert "refresh-secret" not in text
    google = next(platform for platform in payload["platforms"] if platform["provider"] == "google_ads")
    assert google["status"] == "mcp_ready"
    assert google["account_count"] == 1


def test_diagnostics_marks_invalid_connection_store(tmp_path: Path) -> None:
    settings = Settings(project_root=tmp_path, connection_store_path="tokens/connections.json", connections_fallback_to_local=False)
    settings.connection_store_file.parent.mkdir(parents=True, exist_ok=True)
    settings.connection_store_file.write_text("{not valid json", encoding="utf-8")

    payload = DiagnosticsService(settings).connections()

    assert payload["status"] == "error"
    assert payload["storage"]["readable"] is False
    assert payload["storage"]["valid_format"] is False


def test_platform_live_diagnostics_return_not_available_without_fake_data(tmp_path: Path) -> None:
    settings = Settings(project_root=tmp_path, connection_store_path="tokens/connections.json", connections_fallback_to_local=False)
    HostedConnectionStore(settings.connection_store_file).save_provider_config(
        "tiktok_ads",
        {"provider": "tiktok_ads", "accounts": [{"account_id": "adv_1", "access_token": "sensitive-tiktok-value"}]},
    )

    payload = DiagnosticsService(settings).platform("tiktok_ads", live=True)
    check = payload["account_checks"][0]

    assert payload["account_count"] == 1
    assert check["campaigns"]["status"] == "not_available"
    assert check["metrics"]["status"] == "not_available"
    assert "sensitive-tiktok-value" not in str(payload)


@pytest.mark.asyncio
async def test_run_diagnostics_mcp_tool_is_registered_and_safe(tmp_path: Path) -> None:
    settings = Settings(project_root=tmp_path, connection_store_path="tokens/connections.json", connections_fallback_to_local=False)
    HostedConnectionStore(settings.connection_store_file).save_provider_config(
        "meta_ads",
        {"provider": "meta_ads", "accounts": [{"account_id": "act_123", "access_token": "sensitive-meta-value"}]},
    )
    mcp = create_server(settings)
    tool_names = {tool.name for tool in await mcp.list_tools()}

    result = await mcp.call_tool("run_diagnostics", {})
    assert "run_diagnostics" in tool_names
    assert result and isinstance(result[0], TextContent)
    payload = json.loads(result[0].text)
    assert payload["security"]["tokens_returned"] is False
    assert "sensitive-meta-value" not in result[0].text

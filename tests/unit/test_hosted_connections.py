from __future__ import annotations

from pathlib import Path

from ad_mcp.settings import Settings
from ad_mcp.web.hosted import HostedConnectionService


def test_mcp_connection_info_uses_public_url_and_route_path(tmp_path: Path) -> None:
    settings = Settings(
        project_root=tmp_path,
        public_base_url="https://mcp.adforge.dev/",
        mcp_endpoint_path="mcp",
        connections_config="missing.yaml",
    )
    service = HostedConnectionService(settings)

    info = service.mcp_connection_info()

    assert settings.mcp_route_path == "/mcp"
    assert info["url"] == "https://mcp.adforge.dev/mcp"
    assert info["transport"] == "streamable_http"
    assert info["auth"]["type"] == "bearer"


def test_connections_response_does_not_expose_provider_secrets(tmp_path: Path) -> None:
    config = tmp_path / "ads_config.yaml"
    config.write_text(
        """
providers:
  meta_ads:
    provider: meta_ads
    accounts:
      - name: Client Meta
        account_id: "act_123"
        status: configured
        app_secret: super-secret
        access_token: token-value
  google_ads:
    provider: google_ads
    accounts:
      - name: Client Google
        customer_id: "123-456-7890"
        refresh_token: refresh-secret
""",
        encoding="utf-8",
    )
    settings = Settings(project_root=tmp_path, connections_config="ads_config.yaml")
    service = HostedConnectionService(settings)

    payload = service.connections()
    text = str(payload)

    assert "super-secret" not in text
    assert "token-value" not in text
    assert "refresh-secret" not in text
    assert payload["platforms"][0]["status"] == "development_configured"
    assert payload["platforms"][0]["accounts"][0]["credentials_present"] is True


def test_oauth_start_preview_marks_beta_platform_as_not_configured(tmp_path: Path) -> None:
    settings = Settings(project_root=tmp_path, public_base_url="https://mcp.adforge.dev")
    service = HostedConnectionService(settings)

    payload = service.oauth_start_preview("meta_ads")

    assert payload["status"] == "oauth_not_configured"
    assert payload["redirect_url"] == "https://mcp.adforge.dev/oauth/meta/callback"

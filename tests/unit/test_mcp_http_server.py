from __future__ import annotations

import warnings

import pytest

from ad_mcp.http_server import create_http_app
from ad_mcp.mcp_auth import StaticBearerTokenVerifier, build_mcp_auth
from ad_mcp.settings import Settings


def _test_client(app):
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", message="Using `httpx` with `starlette.testclient` is deprecated.*")
        from starlette.testclient import TestClient

    return TestClient(app)


@pytest.mark.asyncio
async def test_static_bearer_token_verifier_accepts_only_expected_token() -> None:
    verifier = StaticBearerTokenVerifier("secret-token")

    accepted = await verifier.verify_token("secret-token")
    rejected = await verifier.verify_token("wrong-token")

    assert accepted is not None
    assert accepted.client_id == "adforge-beta-client"
    assert rejected is None


def test_hosted_mcp_auth_requires_token_in_production(tmp_path) -> None:
    settings = Settings(project_root=tmp_path, env="production", web_api_token="")

    with pytest.raises(RuntimeError, match="AD_MCP_WEB_API_TOKEN"):
        build_mcp_auth(settings)


def test_hosted_mcp_auth_requires_token_in_beta(tmp_path) -> None:
    settings = Settings(project_root=tmp_path, env="beta", web_api_token="", mcp_http_host="127.0.0.1")

    with pytest.raises(RuntimeError, match="beta"):
        build_mcp_auth(settings)


def test_hosted_mcp_auth_requires_token_for_network_exposed_development_host(tmp_path) -> None:
    settings = Settings(project_root=tmp_path, env="development", web_api_token="", mcp_http_host="0.0.0.0")

    with pytest.raises(RuntimeError, match="network-exposed"):
        build_mcp_auth(settings)


def test_hosted_mcp_app_protects_mcp_route_with_bearer_token(tmp_path) -> None:
    settings = Settings(
        project_root=tmp_path,
        env="production",
        web_api_token="secret-token",
        mcp_http_host="0.0.0.0",
        connections_config="missing.yaml",
    )
    app = create_http_app(settings)

    with _test_client(app) as client:
        response = client.post(settings.mcp_route_path, json={"jsonrpc": "2.0", "id": 1, "method": "tools/list"})

    assert response.status_code == 401


def test_hosted_mcp_app_allows_configured_public_host(tmp_path) -> None:
    settings = Settings(
        project_root=tmp_path,
        env="beta",
        web_api_token="secret-token",
        public_base_url="https://adforge.example",
        mcp_public_url="https://adforge.example/mcp",
        mcp_http_host="127.0.0.1",
        connections_config="missing.yaml",
    )
    app = create_http_app(settings)

    with _test_client(app) as client:
        response = client.post(
            settings.mcp_route_path,
            headers={
                "Host": "adforge.example",
                "Authorization": "Bearer secret-token",
                "Accept": "application/json, text/event-stream",
            },
            json={"jsonrpc": "2.0", "id": 1, "method": "tools/list"},
        )

    assert response.status_code != 421
    assert response.text != "Invalid Host header"


def test_hosted_mcp_app_exposes_configured_route(tmp_path) -> None:
    settings = Settings(
        project_root=tmp_path,
        env="development",
        web_api_token="",
        mcp_endpoint_path="custom-mcp",
        mcp_http_host="127.0.0.1",
        connections_config="missing.yaml",
    )
    app = create_http_app(settings)
    paths = {getattr(route, "path", "") for route in app.routes}

    assert "/custom-mcp" in paths


def test_public_mcp_url_can_be_overridden_for_reverse_proxy(tmp_path) -> None:
    settings = Settings(
        project_root=tmp_path,
        public_base_url="https://dashboard.example.com",
        mcp_public_url="https://mcp.example.com/custom-mcp",
        mcp_endpoint_path="/mcp",
    )

    assert settings.public_mcp_url == "https://mcp.example.com/custom-mcp"

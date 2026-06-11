from __future__ import annotations

from urllib.parse import parse_qs, urlparse

import pytest

from ad_mcp.settings import Settings
from ad_mcp.web.meta_oauth import MetaOAuthError, MetaOAuthService


class _FakeResponse:
    def __init__(self, payload: dict) -> None:
        self._payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict:
        return self._payload


class _FakeMetaHTTP:
    def __init__(self) -> None:
        self.calls: list[tuple[str, dict | None]] = []

    def get(self, url: str, params: dict | None = None) -> _FakeResponse:
        self.calls.append((url, params))
        if url.endswith("/oauth/access_token") and params and params.get("code") == "callback-code":
            return _FakeResponse({"access_token": "short-token"})
        if url.endswith("/oauth/access_token") and params and params.get("grant_type") == "fb_exchange_token":
            return _FakeResponse({"access_token": "long-token"})
        if url.endswith("/me/adaccounts"):
            return _FakeResponse(
                {
                    "data": [
                        {
                            "id": "act_111",
                            "account_id": "111",
                            "name": "Client Meta 1",
                            "account_status": 1,
                            "currency": "USD",
                            "timezone_name": "UTC",
                        },
                        {
                            "id": "act_222",
                            "account_id": "222",
                            "name": "Client Meta 2",
                        },
                    ]
                }
            )
        raise AssertionError(f"Unexpected Meta call: {url} {params}")


def _settings(tmp_path):
    return Settings(
        project_root=tmp_path,
        public_base_url="https://mcp.adforge.dev",
        web_api_token="state-secret",
        meta_oauth_app_id="meta-app-id",
        meta_oauth_app_secret="meta-app-secret",
        connection_store_path="tokens/connections.json",
    )


def test_meta_oauth_authorization_url_contains_signed_state(tmp_path) -> None:
    service = MetaOAuthService(_settings(tmp_path), _FakeMetaHTTP())

    url = service.authorization_url()
    query = parse_qs(urlparse(url).query)

    assert url.startswith("https://www.facebook.com/v20.0/dialog/oauth?")
    assert query["client_id"] == ["meta-app-id"]
    assert query["redirect_uri"] == ["https://mcp.adforge.dev/oauth/meta/callback"]
    assert query["scope"] == ["ads_read,business_management"]
    assert query["state"][0].count(".") == 1


def test_meta_oauth_callback_discovers_accounts_and_select_saves_credentials(tmp_path) -> None:
    http = _FakeMetaHTTP()
    service = MetaOAuthService(_settings(tmp_path), http)
    state = parse_qs(urlparse(service.authorization_url()).query)["state"][0]

    pending = service.handle_callback({"code": "callback-code", "state": state})
    selected = service.select_accounts(pending["pending_id"], ["act_111"])
    stored_config = service._store.provider_config("meta_ads")  # noqa: SLF001

    assert pending["status"] == "pending_account_selection"
    assert pending["account_count"] == 2
    assert pending["accounts"][0]["account_id"] == "act_111"
    assert "long-token" not in str(pending)
    assert selected["status"] == "connected"
    assert selected["accounts"] == [
        {"name": "Client Meta 1", "account_id": "act_111", "app_id": "meta-app-id", "status": "connected", "credentials_present": True}
    ]
    assert stored_config["accounts"][0]["access_token"] == "long-token"
    assert stored_config["accounts"][0]["app_secret"] == "meta-app-secret"


def test_meta_oauth_rejects_tampered_state(tmp_path) -> None:
    service = MetaOAuthService(_settings(tmp_path), _FakeMetaHTTP())
    state = parse_qs(urlparse(service.authorization_url()).query)["state"][0]

    with pytest.raises(MetaOAuthError, match="signature"):
        service.handle_callback({"code": "callback-code", "state": f"{state}tampered"})


def test_meta_oauth_requires_app_credentials(tmp_path) -> None:
    service = MetaOAuthService(Settings(project_root=tmp_path, public_base_url="https://mcp.adforge.dev"))

    with pytest.raises(MetaOAuthError, match="not configured"):
        service.authorization_url()

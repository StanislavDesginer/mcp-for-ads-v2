from __future__ import annotations

import base64
import binascii
import hashlib
import hmac
import json
import time
from abc import ABC, abstractmethod
from typing import Any
from urllib.parse import urlencode

import httpx

from ad_mcp.core.connection_store import HostedConnectionStore
from ad_mcp.settings import Settings


class PartnerOAuthError(RuntimeError):
    pass


def _b64_encode(payload: bytes) -> str:
    return base64.urlsafe_b64encode(payload).decode("ascii").rstrip("=")


def _b64_decode(payload: str) -> bytes:
    padding = "=" * (-len(payload) % 4)
    return base64.urlsafe_b64decode(f"{payload}{padding}".encode("ascii"))


def _split_scopes(value: str) -> str:
    return " ".join(part.strip() for part in value.replace(",", " ").split() if part.strip())


class BasePartnerOAuthService(ABC):
    provider: str
    state_ttl_seconds: int

    def __init__(self, settings: Settings | None = None, http_client: httpx.Client | None = None) -> None:
        self._settings = settings or Settings()
        self._store = HostedConnectionStore(self._settings.connection_store_file)
        self._http_client = http_client

    @abstractmethod
    def configured(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    def authorization_url(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def redirect_uri(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def handle_callback(self, query: dict[str, str]) -> dict[str, Any]:
        raise NotImplementedError

    def pending_selection(self, pending_id: str) -> dict[str, Any]:
        return self._store.pending_selection(self.provider, pending_id)

    def select_accounts(self, pending_id: str, account_ids: list[str]) -> dict[str, Any]:
        return self._store.select_pending_accounts(self.provider, pending_id, account_ids)

    def _ensure_configured(self, missing: str) -> None:
        if not self.configured():
            raise PartnerOAuthError(f"{self.provider} OAuth is not configured. Set {missing}.")

    def _signing_secret(self) -> bytes:
        provider_secret_fields = {
            "google_ads": "google_oauth_client_secret",
            "tiktok_ads": "tiktok_oauth_app_secret",
            "yandex_direct": "yandex_oauth_client_secret",
        }
        provider_secret = getattr(self._settings, provider_secret_fields.get(self.provider, ""), "")
        secret = self._settings.web_api_token.strip() or str(provider_secret).strip()
        if not secret:
            raise PartnerOAuthError("OAuth state signing secret is not configured.")
        return secret.encode("utf-8")

    def _sign_state(self, payload: dict[str, Any]) -> str:
        body = _b64_encode(json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8"))
        signature = hmac.new(self._signing_secret(), body.encode("ascii"), hashlib.sha256).digest()
        return f"{body}.{_b64_encode(signature)}"

    def _verify_state(self, state: str) -> dict[str, Any]:
        try:
            body, signature = state.split(".", 1)
        except ValueError as exc:
            raise PartnerOAuthError("Invalid OAuth state.") from exc
        expected = _b64_encode(hmac.new(self._signing_secret(), body.encode("ascii"), hashlib.sha256).digest())
        if not hmac.compare_digest(signature, expected):
            raise PartnerOAuthError("Invalid OAuth state signature.")
        try:
            payload = json.loads(_b64_decode(body).decode("utf-8"))
        except (ValueError, json.JSONDecodeError, UnicodeDecodeError, binascii.Error) as exc:
            raise PartnerOAuthError("Invalid OAuth state payload.") from exc
        if payload.get("provider") != self.provider:
            raise PartnerOAuthError("Invalid OAuth state provider.")
        try:
            issued_at = int(payload.get("iat") or 0)
        except (TypeError, ValueError) as exc:
            raise PartnerOAuthError("Invalid OAuth state timestamp.") from exc
        if int(time.time()) - issued_at > self.state_ttl_seconds:
            raise PartnerOAuthError("OAuth state expired.")
        return payload

    def _client(self) -> tuple[httpx.Client, bool]:
        if self._http_client is not None:
            return self._http_client, False
        return httpx.Client(timeout=20.0), True

    def _get_json(self, url: str, *, params: dict[str, Any] | None = None, headers: dict[str, str] | None = None) -> dict[str, Any]:
        client, close_client = self._client()
        try:
            response = client.get(url, params=params, headers=headers)
            response.raise_for_status()
            payload = response.json()
        except httpx.HTTPError as exc:
            raise PartnerOAuthError(f"{self.provider} OAuth GET failed: {exc}") from exc
        finally:
            if close_client:
                client.close()
        if not isinstance(payload, dict):
            raise PartnerOAuthError(f"{self.provider} returned a non-object payload.")
        return payload

    def _post_json(
        self,
        url: str,
        *,
        data: dict[str, Any] | None = None,
        json_body: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        client, close_client = self._client()
        try:
            response = client.post(url, data=data, json=json_body, headers=headers)
            response.raise_for_status()
            payload = response.json()
        except httpx.HTTPError as exc:
            raise PartnerOAuthError(f"{self.provider} OAuth POST failed: {exc}") from exc
        finally:
            if close_client:
                client.close()
        if not isinstance(payload, dict):
            raise PartnerOAuthError(f"{self.provider} returned a non-object payload.")
        return payload


class GoogleOAuthService(BasePartnerOAuthService):
    provider = "google_ads"

    @property
    def state_ttl_seconds(self) -> int:
        return self._settings.google_oauth_state_ttl_seconds

    def configured(self) -> bool:
        return bool(
            self._settings.google_oauth_client_id.strip()
            and self._settings.google_oauth_client_secret.strip()
            and self._settings.google_ads_developer_token.strip()
        )

    def redirect_uri(self) -> str:
        return f"{self._settings.public_base_or_local_web_url}{self._settings.google_oauth_redirect_path}"

    def authorization_url(self) -> str:
        self._ensure_configured(
            "AD_MCP_GOOGLE_OAUTH_CLIENT_ID, AD_MCP_GOOGLE_OAUTH_CLIENT_SECRET and AD_MCP_GOOGLE_ADS_DEVELOPER_TOKEN"
        )
        redirect_uri = self.redirect_uri()
        state = self._sign_state({"provider": self.provider, "iat": int(time.time()), "redirect_uri": redirect_uri})
        query = urlencode(
            {
                "client_id": self._settings.google_oauth_client_id.strip(),
                "redirect_uri": redirect_uri,
                "response_type": "code",
                "scope": _split_scopes(self._settings.google_oauth_scopes),
                "access_type": "offline",
                "prompt": "consent",
                "include_granted_scopes": "true",
                "state": state,
            }
        )
        return f"https://accounts.google.com/o/oauth2/v2/auth?{query}"

    def handle_callback(self, query: dict[str, str]) -> dict[str, Any]:
        self._ensure_configured(
            "AD_MCP_GOOGLE_OAUTH_CLIENT_ID, AD_MCP_GOOGLE_OAUTH_CLIENT_SECRET and AD_MCP_GOOGLE_ADS_DEVELOPER_TOKEN"
        )
        if query.get("error"):
            raise PartnerOAuthError(query.get("error_description") or query["error"])
        code = str(query.get("code", "") or "").strip()
        if not code:
            raise PartnerOAuthError("Google OAuth callback is missing code.")
        state_payload = self._verify_state(str(query.get("state", "") or "").strip())
        redirect_uri = str(state_payload.get("redirect_uri") or self.redirect_uri())
        token_payload = self._exchange_code_for_token(code, redirect_uri)
        access_token = str(token_payload.get("access_token", "") or "").strip()
        refresh_token = str(token_payload.get("refresh_token", "") or "").strip()
        if not access_token:
            raise PartnerOAuthError("Google OAuth token exchange did not return access_token.")
        if not refresh_token:
            raise PartnerOAuthError("Google OAuth token exchange did not return refresh_token. Reconnect with consent prompt.")
        accounts = self._fetch_accessible_customers(access_token)
        if not accounts:
            raise PartnerOAuthError("Google OAuth succeeded, but no accessible Google Ads accounts were returned.")
        pending = self._store.save_oauth_pending(
            self.provider,
            accounts,
            credentials={
                "developer_token": self._settings.google_ads_developer_token.strip(),
                "oauth_client_id": self._settings.google_oauth_client_id.strip(),
                "oauth_client_secret": self._settings.google_oauth_client_secret.strip(),
                "refresh_token": refresh_token,
                "access_token": access_token,
            },
            ttl_seconds=self.state_ttl_seconds,
            source="google_oauth",
        )
        return pending | {"status": "pending_account_selection", "account_count": len(pending["accounts"])}

    def _exchange_code_for_token(self, code: str, redirect_uri: str) -> dict[str, Any]:
        return self._post_json(
            "https://oauth2.googleapis.com/token",
            data={
                "code": code,
                "client_id": self._settings.google_oauth_client_id.strip(),
                "client_secret": self._settings.google_oauth_client_secret.strip(),
                "redirect_uri": redirect_uri,
                "grant_type": "authorization_code",
            },
        )

    def _fetch_accessible_customers(self, access_token: str) -> list[dict[str, Any]]:
        version = (self._settings.google_ads_api_version.strip() or "v20").lstrip("/")
        payload = self._get_json(
            f"https://googleads.googleapis.com/{version}/customers:listAccessibleCustomers",
            headers={
                "Authorization": f"Bearer {access_token}",
                "developer-token": self._settings.google_ads_developer_token.strip(),
            },
        )
        accounts: list[dict[str, Any]] = []
        for resource_name in payload.get("resourceNames", []) or []:
            customer_id = str(resource_name).split("/")[-1].strip()
            if customer_id:
                accounts.append(
                    {
                        "name": f"Google Ads {customer_id}",
                        "account_id": customer_id,
                        "customer_id": customer_id,
                        "status": "connected",
                    }
                )
        return accounts


class TikTokOAuthService(BasePartnerOAuthService):
    provider = "tiktok_ads"

    @property
    def state_ttl_seconds(self) -> int:
        return self._settings.tiktok_oauth_state_ttl_seconds

    def configured(self) -> bool:
        return bool(self._settings.tiktok_oauth_app_id.strip() and self._settings.tiktok_oauth_app_secret.strip())

    def redirect_uri(self) -> str:
        return f"{self._settings.public_base_or_local_web_url}{self._settings.tiktok_oauth_redirect_path}"

    def authorization_url(self) -> str:
        self._ensure_configured("AD_MCP_TIKTOK_OAUTH_APP_ID and AD_MCP_TIKTOK_OAUTH_APP_SECRET")
        redirect_uri = self.redirect_uri()
        state = self._sign_state({"provider": self.provider, "iat": int(time.time()), "redirect_uri": redirect_uri})
        params: dict[str, str] = {
            "app_id": self._settings.tiktok_oauth_app_id.strip(),
            "redirect_uri": redirect_uri,
            "state": state,
        }
        scopes = _split_scopes(self._settings.tiktok_oauth_scopes)
        if scopes:
            params["scope"] = scopes
        return f"{self._settings.tiktok_oauth_auth_url.strip()}?{urlencode(params)}"

    def handle_callback(self, query: dict[str, str]) -> dict[str, Any]:
        self._ensure_configured("AD_MCP_TIKTOK_OAUTH_APP_ID and AD_MCP_TIKTOK_OAUTH_APP_SECRET")
        if query.get("error"):
            raise PartnerOAuthError(query.get("error_description") or query["error"])
        auth_code = str(query.get("auth_code") or query.get("code") or "").strip()
        if not auth_code:
            raise PartnerOAuthError("TikTok OAuth callback is missing auth_code.")
        self._verify_state(str(query.get("state", "") or "").strip())
        token_payload = self._exchange_code_for_token(auth_code)
        token_data = token_payload.get("data") if isinstance(token_payload.get("data"), dict) else token_payload
        access_token = str(token_data.get("access_token", "") or "").strip()
        refresh_token = str(token_data.get("refresh_token", "") or "").strip()
        if not access_token:
            raise PartnerOAuthError("TikTok OAuth token exchange did not return access_token.")
        advertiser_ids = self._advertiser_ids_from_payload(token_data)
        if not advertiser_ids:
            advertiser_ids = self._fetch_advertiser_ids(access_token)
        if not advertiser_ids and self._settings.tiktok_oauth_advertiser_id.strip():
            advertiser_ids = [self._settings.tiktok_oauth_advertiser_id.strip()]
        if not advertiser_ids:
            raise PartnerOAuthError("TikTok OAuth succeeded, but no advertiser IDs were returned.")
        accounts = [
            {
                "name": f"TikTok Advertiser {advertiser_id}",
                "account_id": advertiser_id,
                "advertiser_id": advertiser_id,
                "app_id": self._settings.tiktok_oauth_app_id.strip(),
                "status": "connected",
            }
            for advertiser_id in advertiser_ids
        ]
        pending = self._store.save_oauth_pending(
            self.provider,
            accounts,
            credentials={
                "app_id": self._settings.tiktok_oauth_app_id.strip(),
                "app_secret": self._settings.tiktok_oauth_app_secret.strip(),
                "access_token": access_token,
                "refresh_token": refresh_token,
            },
            ttl_seconds=self.state_ttl_seconds,
            source="tiktok_oauth",
        )
        return pending | {"status": "pending_account_selection", "account_count": len(pending["accounts"])}

    def _exchange_code_for_token(self, auth_code: str) -> dict[str, Any]:
        return self._post_json(
            self._settings.tiktok_oauth_token_url.strip(),
            json_body={
                "app_id": self._settings.tiktok_oauth_app_id.strip(),
                "secret": self._settings.tiktok_oauth_app_secret.strip(),
                "auth_code": auth_code,
            },
        )

    def _fetch_advertiser_ids(self, access_token: str) -> list[str]:
        try:
            payload = self._get_json(
                self._settings.tiktok_oauth_advertiser_get_url.strip(),
                headers={"Access-Token": access_token},
            )
        except PartnerOAuthError:
            return []
        data = payload.get("data") if isinstance(payload.get("data"), dict) else payload
        return self._advertiser_ids_from_payload(data)

    def _advertiser_ids_from_payload(self, payload: dict[str, Any]) -> list[str]:
        candidates = (
            payload.get("advertiser_ids")
            or payload.get("advertiser_id_list")
            or payload.get("advertiser_id")
            or []
        )
        if isinstance(candidates, str):
            return [candidates]
        if isinstance(candidates, list):
            ids: list[str] = []
            for item in candidates:
                if isinstance(item, dict):
                    candidate = item.get("advertiser_id") or item.get("id")
                else:
                    candidate = item
                value = str(candidate or "").strip()
                if value:
                    ids.append(value)
            return ids
        return []


class YandexOAuthService(BasePartnerOAuthService):
    provider = "yandex_direct"

    @property
    def state_ttl_seconds(self) -> int:
        return self._settings.yandex_oauth_state_ttl_seconds

    def configured(self) -> bool:
        return bool(self._settings.yandex_oauth_client_id.strip() and self._settings.yandex_oauth_client_secret.strip())

    def redirect_uri(self) -> str:
        return f"{self._settings.public_base_or_local_web_url}{self._settings.yandex_oauth_redirect_path}"

    def authorization_url(self) -> str:
        self._ensure_configured("AD_MCP_YANDEX_OAUTH_CLIENT_ID and AD_MCP_YANDEX_OAUTH_CLIENT_SECRET")
        redirect_uri = self.redirect_uri()
        state = self._sign_state({"provider": self.provider, "iat": int(time.time()), "redirect_uri": redirect_uri})
        query = urlencode(
            {
                "response_type": "code",
                "client_id": self._settings.yandex_oauth_client_id.strip(),
                "redirect_uri": redirect_uri,
                "scope": self._settings.yandex_oauth_scope.strip(),
                "state": state,
            }
        )
        return f"{self._settings.yandex_oauth_authorize_url.strip()}?{query}"

    def handle_callback(self, query: dict[str, str]) -> dict[str, Any]:
        self._ensure_configured("AD_MCP_YANDEX_OAUTH_CLIENT_ID and AD_MCP_YANDEX_OAUTH_CLIENT_SECRET")
        if query.get("error"):
            raise PartnerOAuthError(query.get("error_description") or query["error"])
        code = str(query.get("code", "") or "").strip()
        if not code:
            raise PartnerOAuthError("Yandex OAuth callback is missing code.")
        state_payload = self._verify_state(str(query.get("state", "") or "").strip())
        redirect_uri = str(state_payload.get("redirect_uri") or self.redirect_uri())
        token_payload = self._exchange_code_for_token(code, redirect_uri)
        access_token = str(token_payload.get("access_token", "") or "").strip()
        refresh_token = str(token_payload.get("refresh_token", "") or "").strip()
        if not access_token:
            raise PartnerOAuthError("Yandex OAuth token exchange did not return access_token.")
        account_id = self._settings.yandex_direct_client_login.strip() or self._settings.yandex_direct_login.strip()
        if not account_id:
            raise PartnerOAuthError("Yandex Direct client login is not configured.")
        account = {
            "name": f"Yandex Direct {account_id}",
            "account_id": account_id,
            "login": self._settings.yandex_direct_login.strip(),
            "direct_client_login": self._settings.yandex_direct_client_login.strip() or account_id,
            "scope": self._settings.yandex_oauth_scope.strip(),
            "status": "connected",
        }
        pending = self._store.save_oauth_pending(
            self.provider,
            [account],
            credentials={
                "oauth_client_id": self._settings.yandex_oauth_client_id.strip(),
                "oauth_client_secret": self._settings.yandex_oauth_client_secret.strip(),
                "access_token": access_token,
                "refresh_token": refresh_token,
            },
            ttl_seconds=self.state_ttl_seconds,
            source="yandex_oauth",
        )
        return pending | {"status": "pending_account_selection", "account_count": len(pending["accounts"])}

    def _exchange_code_for_token(self, code: str, redirect_uri: str) -> dict[str, Any]:
        return self._post_json(
            self._settings.yandex_oauth_token_url.strip(),
            data={
                "grant_type": "authorization_code",
                "code": code,
                "client_id": self._settings.yandex_oauth_client_id.strip(),
                "client_secret": self._settings.yandex_oauth_client_secret.strip(),
                "redirect_uri": redirect_uri,
            },
        )

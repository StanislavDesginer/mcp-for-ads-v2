from __future__ import annotations

import secrets

from mcp.server.auth.provider import AccessToken
from mcp.server.auth.settings import AuthSettings

from ad_mcp.settings import Settings


MCP_SCOPE = "adforge:mcp"


class StaticBearerTokenVerifier:
    def __init__(self, token: str) -> None:
        self._token = token

    async def verify_token(self, token: str) -> AccessToken | None:
        if not self._token or not secrets.compare_digest(token, self._token):
            return None
        return AccessToken(token=token, client_id="adforge-beta-client", scopes=[MCP_SCOPE])


def mcp_token_required(settings: Settings) -> bool:
    return bool(settings.web_api_token.strip()) or settings.env.lower() == "production"


def build_mcp_auth(settings: Settings) -> tuple[AuthSettings | None, StaticBearerTokenVerifier | None]:
    if not mcp_token_required(settings):
        return None, None
    token = settings.web_api_token.strip()
    if not token:
        raise RuntimeError("AD_MCP_WEB_API_TOKEN is required for hosted MCP in production.")
    issuer_url = settings.public_base_or_local_mcp_url
    resource_server_url = settings.public_mcp_url
    return (
        AuthSettings(
            issuer_url=issuer_url,
            resource_server_url=resource_server_url,
            required_scopes=[MCP_SCOPE],
        ),
        StaticBearerTokenVerifier(token),
    )

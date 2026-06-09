from ad_mcp.settings import Settings
from ad_mcp.web.server import _api_token_required, _extract_request_token, _request_token_is_valid


class _Headers:
    def __init__(self, values: dict[str, str]) -> None:
        self._values = values

    def get(self, key: str, default: str = "") -> str:
        return self._values.get(key, default)


def test_api_token_not_required_for_development_without_token() -> None:
    settings = Settings(env="development", web_api_token="")

    assert _api_token_required(settings) is False
    assert _request_token_is_valid(_Headers({}), settings) is True


def test_api_token_required_for_production_even_when_missing() -> None:
    settings = Settings(env="production", web_api_token="")

    assert _api_token_required(settings) is True
    assert _request_token_is_valid(_Headers({}), settings) is False


def test_bearer_token_authorizes_request() -> None:
    settings = Settings(env="production", web_api_token="secret-token")

    assert _extract_request_token(_Headers({"Authorization": "Bearer secret-token"})) == "secret-token"
    assert _request_token_is_valid(_Headers({"Authorization": "Bearer secret-token"}), settings) is True
    assert _request_token_is_valid(_Headers({"Authorization": "Bearer wrong-token"}), settings) is False


def test_custom_beta_token_header_authorizes_request() -> None:
    settings = Settings(env="production", web_api_token="secret-token")

    assert _extract_request_token(_Headers({"X-AD-MCP-BETA-TOKEN": "secret-token"})) == "secret-token"
    assert _request_token_is_valid(_Headers({"X-AD-MCP-BETA-TOKEN": "secret-token"}), settings) is True

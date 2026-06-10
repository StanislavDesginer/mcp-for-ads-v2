import json

import pytest
from mcp.types import TextContent

from ad_mcp.core.connection_store import HostedConnectionStore
from ad_mcp.server import create_server
from ad_mcp.settings import Settings


def _json_tool_payload(result: list[TextContent]) -> dict:
    assert result
    assert isinstance(result[0], TextContent)
    return json.loads(result[0].text)


@pytest.mark.asyncio
async def test_beta_diagnostics_tool_is_registered_and_safe() -> None:
    mcp = create_server()
    tools = await mcp.list_tools()
    tool_names = {tool.name for tool in tools}

    assert "get_beta_diagnostics" in tool_names

    result = await mcp.call_tool("get_beta_diagnostics", {})
    payload = _json_tool_payload(result)

    assert payload["status"] == "ok"
    assert payload["smoke_checks"]["diagnostics_available"] is True
    assert payload["security"]["execution_mode"] == "simulated_no_write"

    meta_account = payload["providers"]["meta_ads"]["accounts"][0]
    assert set(meta_account) == {"name", "account_id", "status"}


@pytest.mark.asyncio
async def test_beta_diagnostics_reads_accounts_from_hosted_connection_store(tmp_path) -> None:
    settings = Settings(
        project_root=tmp_path,
        connection_store_path="tokens/connections.json",
        connections_fallback_to_local=False,
    )
    HostedConnectionStore(settings.connection_store_file).save_provider_config(
        "meta_ads",
        {
            "provider": "meta_ads",
            "accounts": [{"name": "Hosted Meta", "account_id": "hosted_123", "status": "connected", "access_token": "secret"}],
        },
    )
    mcp = create_server(settings)

    result = await mcp.call_tool("get_beta_diagnostics", {})
    payload = _json_tool_payload(result)

    assert payload["config"]["connection_store"]["provider_sources"]["meta_ads"] == "hosted_connection_store"
    assert payload["providers"]["meta_ads"]["accounts"] == [{"name": "Hosted Meta", "account_id": "hosted_123", "status": "connected"}]

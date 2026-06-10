from __future__ import annotations

import argparse
import asyncio
import json
import logging
import warnings
from typing import Any

from mcp.types import TextContent

from ad_mcp.http_server import create_http_app
from ad_mcp.server import create_server
from ad_mcp.settings import Settings


REQUIRED_TOOLS = {
    "list_providers",
    "get_provider_capabilities",
    "list_accounts",
    "describe_auth_strategy",
    "get_beta_diagnostics",
    "clone_campaign_preview",
    "update_campaign_budget_preview",
    "commit_preview",
}


def _extract_payload(result: Any) -> Any:
    if isinstance(result, tuple):
        for item in result:
            if isinstance(item, dict):
                return item.get("result", item)
        for item in result:
            if isinstance(item, list):
                parsed = _extract_payload(item)
                if parsed is not None:
                    return parsed
    if isinstance(result, list):
        text_values: list[str] = []
        for item in result:
            if isinstance(item, TextContent):
                try:
                    return json.loads(item.text)
                except json.JSONDecodeError:
                    text_values.append(item.text)
        if text_values:
            return text_values[0] if len(text_values) == 1 else text_values
    return result


def _first_account_id(diagnostics: dict[str, Any], provider: str) -> str | None:
    accounts = diagnostics.get("providers", {}).get(provider, {}).get("accounts", [])
    for account in accounts:
        account_id = account.get("account_id")
        if account_id:
            return str(account_id)
    return None


def _hosted_http_smoke() -> dict[str, Any]:
    settings = Settings(env="production", web_api_token="smoke-token", mcp_http_host="0.0.0.0")
    app = create_http_app(settings)
    route_paths = {getattr(route, "path", "") for route in app.routes}
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", message="Using `httpx` with `starlette.testclient` is deprecated.*")
        from starlette.testclient import TestClient

    previous_disable_level = logging.root.manager.disable
    logging.disable(logging.CRITICAL)
    try:
        with TestClient(app) as client:
            unauthorized = client.post(settings.mcp_route_path, json={"jsonrpc": "2.0", "id": 1, "method": "tools/list"})
    finally:
        logging.disable(previous_disable_level)
    return {
        "app_imports": True,
        "route": settings.mcp_route_path,
        "route_registered": settings.mcp_route_path in route_paths,
        "auth_required": unauthorized.status_code == 401,
        "unauthorized_status": unauthorized.status_code,
    }


async def run(provider: str, account_id: str | None, skip_preview: bool) -> dict[str, Any]:
    mcp = create_server()
    tools = await mcp.list_tools()
    tool_names = {tool.name for tool in tools}
    missing_tools = sorted(REQUIRED_TOOLS - tool_names)
    if missing_tools:
        raise RuntimeError(f"Missing required beta MCP tools: {', '.join(missing_tools)}")

    providers = _extract_payload(await mcp.call_tool("list_providers", {}))
    diagnostics = _extract_payload(await mcp.call_tool("get_beta_diagnostics", {}))
    if not isinstance(diagnostics, dict) or diagnostics.get("status") != "ok":
        raise RuntimeError("get_beta_diagnostics did not return an ok payload")
    if not diagnostics.get("smoke_checks", {}).get("diagnostics_available"):
        raise RuntimeError("Diagnostics are not marked as available")

    capabilities = _extract_payload(await mcp.call_tool("get_provider_capabilities", {"provider": provider}))
    auth_strategy = _extract_payload(await mcp.call_tool("describe_auth_strategy", {"provider": provider}))

    preview_result: dict[str, Any] | None = None
    commit_result: dict[str, Any] | None = None
    resolved_account_id = account_id or _first_account_id(diagnostics, provider)
    if not skip_preview:
        if not resolved_account_id:
            raise RuntimeError(f"No configured {provider} account found for preview smoke check")
        preview_result = _extract_payload(
            await mcp.call_tool(
                "clone_campaign_preview",
                {
                    "provider": provider,
                    "account_id": resolved_account_id,
                    "source_campaign_id": "smoke_source_campaign",
                    "new_name": "Smoke beta preview",
                },
            )
        )
        if not isinstance(preview_result, dict) or preview_result.get("status") != "preview":
            raise RuntimeError("Preview smoke check did not return status=preview")
        if preview_result.get("provider_response"):
            raise RuntimeError("Preview smoke check returned a provider_response; expected no live write")
        commit_result = _extract_payload(await mcp.call_tool("commit_preview", {"preview_token": preview_result.get("preview_token")}))
        if not isinstance(commit_result, dict) or commit_result.get("status") != "blocked":
            raise RuntimeError("Commit smoke check did not return status=blocked in beta preview-only mode")
        if commit_result.get("provider_response", {}).get("mode") != "preview_only":
            raise RuntimeError("Commit smoke check did not return provider_response.mode=preview_only")

    return {
        "status": "ok",
        "server_imports": True,
        "tool_count": len(tool_names),
        "required_tools": sorted(REQUIRED_TOOLS),
        "providers": providers,
        "provider_checked": provider,
        "account_checked": resolved_account_id,
        "diagnostics": {
            "status": diagnostics.get("status"),
            "environment": diagnostics.get("environment"),
            "execution_mode": diagnostics.get("security", {}).get("execution_mode"),
            "connections_config_exists": diagnostics.get("config", {}).get("connections_config", {}).get("exists"),
            "connection_store_exists": diagnostics.get("config", {}).get("connection_store", {}).get("exists"),
            "provider_sources": diagnostics.get("config", {}).get("connection_store", {}).get("provider_sources"),
            "policy_config_exists": diagnostics.get("config", {}).get("policy_config", {}).get("exists"),
        },
        "capability_counts": {
            "read_objects": len(capabilities.get("read_objects", [])) if isinstance(capabilities, dict) else None,
            "write_objects": len(capabilities.get("write_objects", [])) if isinstance(capabilities, dict) else None,
        },
        "auth_strategy_available": bool(auth_strategy),
        "hosted_http": _hosted_http_smoke(),
        "preview_checked": preview_result is not None,
        "preview_status": preview_result.get("status") if isinstance(preview_result, dict) else None,
        "commit_checked": commit_result is not None,
        "commit_status": commit_result.get("status") if isinstance(commit_result, dict) else None,
        "live_write_checked": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run beta MCP smoke checks without live writes.")
    parser.add_argument("--provider", default="meta_ads", help="Provider to check, default: meta_ads.")
    parser.add_argument("--account-id", default=None, help="Configured account_id to use for preview smoke.")
    parser.add_argument("--skip-preview", action="store_true", help="Skip preview mutation smoke check.")
    args = parser.parse_args()

    payload = asyncio.run(run(args.provider, args.account_id, args.skip_preview))
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

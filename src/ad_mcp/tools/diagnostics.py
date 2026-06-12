from __future__ import annotations

from ad_mcp.settings import Settings
from ad_mcp.web.diagnostics import DiagnosticsService


def build_diagnostics_tools(settings: Settings) -> dict[str, callable]:
    def run_diagnostics(live_check: bool = False) -> dict:
        return DiagnosticsService(settings).mcp_tool_summary(live=live_check)

    return {"run_diagnostics": run_diagnostics}

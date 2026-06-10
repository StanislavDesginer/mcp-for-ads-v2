from __future__ import annotations

from ad_mcp.core.audit_logger import AuditLogger
from ad_mcp.core.capability_registry import CapabilityRegistry
from ad_mcp.core.policy import PolicyManager, SafetyPolicy
from ad_mcp.core.preview_manager import PreviewManager
from ad_mcp.providers.google_ads.client import GoogleAdsProvider
from ad_mcp.tools.write_commit import build_write_commit_tools


def test_commit_preview_is_blocked_and_keeps_preview_token_in_beta(tmp_path) -> None:
    provider = GoogleAdsProvider(config={"accounts": [{"account_id": "123", "name": "Test"}]})
    registry = CapabilityRegistry({"google_ads": provider})
    preview_manager = PreviewManager()
    policy_manager = PolicyManager(SafetyPolicy(execution_mode="simulated_no_write"))
    audit_logger = AuditLogger(tmp_path / "audit.jsonl")
    preview = preview_manager.create(
        provider.preview_mutation(
            action="update",
            account_id="123",
            object_type="campaign",
            payload={"name": "Updated"},
        )
    )
    tools = build_write_commit_tools(registry, preview_manager, audit_logger, policy_manager)

    result = tools["commit_preview"](preview.token)

    assert result["status"] == "blocked"
    assert result["provider_response"]["mode"] == "preview_only"
    assert result["preview_token"] == preview.token
    assert preview_manager.get(preview.token).token == preview.token

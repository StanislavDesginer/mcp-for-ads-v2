from __future__ import annotations

from ad_mcp.core.capability_registry import CapabilityRegistry
from ad_mcp.core.audit_logger import AuditLogger
from ad_mcp.core.policy import PolicyManager
from ad_mcp.core.preview_manager import PreviewManager


def build_write_commit_tools(
    registry: CapabilityRegistry,
    preview_manager: PreviewManager,
    audit_logger: AuditLogger,
    policy_manager: PolicyManager,
) -> dict[str, callable]:
    def commit_preview(preview_token: str) -> dict:
        preview = preview_manager.get(preview_token)
        policy_manager.validate_account_access(bool(registry.get_provider(preview.provider).get_account_config(preview.account_id)))
        if policy_manager.preview_only_enabled:
            result = {
                "status": "blocked",
                "provider": preview.provider,
                "account_id": preview.account_id,
                "object_type": preview.object_type,
                "action": preview.action,
                "preview_token": preview.token,
                "diff": preview.diff,
                "risk_flags": preview.risk_flags,
                "provider_payload": preview.provider_payload,
                "provider_response": {
                    "mode": "preview_only",
                    "message": "Beta MVP is preview-only. No external mutation was executed.",
                },
            }
            audit_logger.log("commit_preview_blocked", result)
            return result
        policy_manager.ensure_preview_only()
        preview = preview_manager.consume(preview_token)
        response = registry.get_provider(preview.provider).commit_preview(preview)
        result = response.model_dump()
        audit_logger.log("commit_preview", result)
        return result

    return {"commit_preview": commit_preview}

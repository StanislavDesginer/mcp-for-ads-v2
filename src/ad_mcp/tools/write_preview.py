from __future__ import annotations

from ad_mcp.core.capability_registry import CapabilityRegistry
from ad_mcp.core.audit_logger import AuditLogger
from ad_mcp.core.models import ObjectMutationResponse
from ad_mcp.core.policy import PolicyManager
from ad_mcp.core.preview_manager import PreviewManager
from ad_mcp.tools._shared import validate_provider_account


PREVIEW_ONLY_REASON = "Beta MVP работает в preview-only mode. Реальные изменения отключены."
PREVIEW_ONLY_NOTE = "Реальное изменение не выполнено."


def build_write_preview_tools(
    registry: CapabilityRegistry,
    preview_manager: PreviewManager,
    audit_logger: AuditLogger,
    policy_manager: PolicyManager,
) -> dict[str, callable]:
    def _build_preview_response(provider: str, account_id: str, object_type: str, action: str, payload: dict) -> dict:
        policy_manager.ensure_simulated_no_write()
        validate_provider_account(registry, policy_manager, provider, account_id)
        policy_manager.validate_mutation_payload(payload)
        preview = registry.get_provider(provider).preview_mutation(
            action=action,
            account_id=account_id,
            object_type=object_type,
            payload=payload,
        )
        preview_manager.create(preview)
        response = ObjectMutationResponse(
            status="preview",
            provider=provider,
            account_id=account_id,
            object_type=object_type,
            action=action,  # type: ignore[arg-type]
            preview_token=preview.token,
            diff=preview.diff,
            risk_flags=preview.risk_flags,
            provider_payload=preview.provider_payload,
        ).model_dump()
        response.update(
            {
                "mode": "preview_only",
                "will_apply": False,
                "reason": PREVIEW_ONLY_REASON,
                "note": PREVIEW_ONLY_NOTE,
            }
        )
        audit_logger.log(f"preview_{action}", response)
        return response

    def preview_create_object(
        provider: str,
        account_id: str,
        object_type: str,
        payload: dict,
    ) -> dict:
        return _build_preview_response(provider, account_id, object_type, "create", payload)

    def preview_update_object(
        provider: str,
        account_id: str,
        object_type: str,
        payload: dict,
    ) -> dict:
        return _build_preview_response(provider, account_id, object_type, "update", payload)

    def preview_delete_or_archive_object(
        provider: str,
        account_id: str,
        object_type: str,
        payload: dict,
    ) -> dict:
        return _build_preview_response(provider, account_id, object_type, "delete_or_archive", payload)

    return {
        "preview_create_object": preview_create_object,
        "preview_update_object": preview_update_object,
        "preview_delete_or_archive_object": preview_delete_or_archive_object,
    }

from __future__ import annotations

from ad_mcp.core.capability_registry import CapabilityRegistry
from ad_mcp.core.models import ObjectMutationResponse
from ad_mcp.core.policy import PolicyManager
from ad_mcp.core.preview_manager import PreviewManager
from ad_mcp.intents.build_object_from_brief import (
    build_ad_group_payload_from_brief,
    build_ad_payload_from_brief,
    build_audience_payload_from_brief,
    build_keyword_payload_from_brief,
    build_schedule_payload_from_brief,
)
from ad_mcp.intents.create_campaign_from_brief import build_campaign_payload_from_brief
from ad_mcp.tools._shared import validate_provider_account


def build_intent_tools(
    registry: CapabilityRegistry,
    preview_manager: PreviewManager,
    policy_manager: PolicyManager,
) -> dict[str, callable]:
    def _preview(provider: str, account_id: str, object_type: str, payload: dict) -> dict:
        policy_manager.ensure_simulated_no_write()
        validate_provider_account(registry, policy_manager, provider, account_id)
        policy_manager.validate_mutation_payload(payload)
        preview = registry.get_provider(provider).preview_mutation(
            action="create",
            account_id=account_id,
            object_type=object_type,
            payload=payload,
        )
        preview_manager.create(preview)
        return ObjectMutationResponse(
            status="preview",
            provider=provider,
            account_id=account_id,
            object_type=object_type,
            action="create",
            preview_token=preview.token,
            diff=preview.diff,
            risk_flags=preview.risk_flags,
            provider_payload=preview.provider_payload,
        ).model_dump()

    def create_campaign_from_brief(provider: str, account_id: str, brief: dict) -> dict:
        return _preview(provider, account_id, "campaign", build_campaign_payload_from_brief(provider, brief))

    def create_ad_group_from_brief(provider: str, account_id: str, brief: dict) -> dict:
        object_type = "adset" if provider == "meta_ads" else ("adgroup" if provider == "tiktok_ads" else "ad_group")
        return _preview(provider, account_id, object_type, build_ad_group_payload_from_brief(provider, brief))

    def create_ad_from_brief(provider: str, account_id: str, brief: dict) -> dict:
        return _preview(provider, account_id, "ad", build_ad_payload_from_brief(provider, brief))

    def create_keyword_from_brief(provider: str, account_id: str, brief: dict) -> dict:
        return _preview(provider, account_id, "keyword", build_keyword_payload_from_brief(brief))

    def create_audience_from_brief(provider: str, account_id: str, brief: dict) -> dict:
        return _preview(provider, account_id, "audience", build_audience_payload_from_brief(provider, brief))

    def configure_schedule_from_brief(provider: str, account_id: str, brief: dict) -> dict:
        return _preview(provider, account_id, "schedule", build_schedule_payload_from_brief(brief))

    return {
        "create_campaign_from_brief": create_campaign_from_brief,
        "create_ad_group_from_brief": create_ad_group_from_brief,
        "create_ad_from_brief": create_ad_from_brief,
        "create_keyword_from_brief": create_keyword_from_brief,
        "create_audience_from_brief": create_audience_from_brief,
        "configure_schedule_from_brief": configure_schedule_from_brief,
    }

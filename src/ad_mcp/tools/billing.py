from __future__ import annotations

from ad_mcp.core.capability_registry import CapabilityRegistry
from ad_mcp.core.policy import PolicyManager
from ad_mcp.tools._shared import validate_provider_account


def build_billing_tools(
    registry: CapabilityRegistry,
    policy_manager: PolicyManager,
) -> dict[str, callable]:
    def get_billing_summary(provider: str, account_id: str) -> dict:
        validate_provider_account(registry, policy_manager, provider, account_id)
        return registry.get_provider(provider).get_billing_summary(account_id)

    return {"get_billing_summary": get_billing_summary}

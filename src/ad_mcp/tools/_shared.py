from __future__ import annotations

from typing import Any

from ad_mcp.core.capability_registry import CapabilityRegistry
from ad_mcp.core.policy import PolicyManager


def validate_provider_account(
    registry: CapabilityRegistry,
    policy_manager: PolicyManager,
    provider: str,
    account_id: str,
) -> dict[str, Any]:
    provider_client = registry.get_provider(provider)
    account_config = provider_client.get_account_config(account_id)
    policy_manager.validate_account_access(bool(account_config))
    return account_config

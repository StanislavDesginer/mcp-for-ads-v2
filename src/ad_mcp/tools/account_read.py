from __future__ import annotations

from datetime import date

from ad_mcp.core.capability_registry import CapabilityRegistry
from ad_mcp.core.policy import PolicyManager
from ad_mcp.tools._shared import validate_provider_account


def build_account_read_tools(
    registry: CapabilityRegistry,
    policy_manager: PolicyManager,
) -> dict[str, callable]:
    def get_account_summary(provider: str, account_id: str, fields: list[str] | None = None) -> dict:
        validate_provider_account(registry, policy_manager, provider, account_id)
        return registry.get_provider(provider).get_account_summary(account_id, fields)

    def list_account_objects(
        provider: str,
        account_id: str,
        object_type: str,
        fields: list[str] | None = None,
        params: dict | None = None,
        limit: int = 100,
    ) -> dict:
        validate_provider_account(registry, policy_manager, provider, account_id)
        return registry.get_provider(provider).list_account_objects(account_id, object_type, fields, params, limit)

    def get_account_object(
        provider: str,
        account_id: str,
        object_type: str,
        object_id: str,
        fields: list[str] | None = None,
    ) -> dict:
        validate_provider_account(registry, policy_manager, provider, account_id)
        return registry.get_provider(provider).get_account_object(account_id, object_type, object_id, fields)

    def get_flexible_insights(
        provider: str,
        account_id: str,
        level: str,
        start_date: str,
        end_date: str,
        fields: list[str] | None = None,
        breakdowns: list[str] | None = None,
        params: dict | None = None,
        limit: int = 500,
    ) -> dict:
        validate_provider_account(registry, policy_manager, provider, account_id)
        policy_manager.validate_report_range(start_date, end_date)
        date.fromisoformat(start_date)
        date.fromisoformat(end_date)
        return registry.get_provider(provider).get_flexible_insights(
            account_id=account_id,
            level=level,
            start_date=start_date,
            end_date=end_date,
            fields=fields,
            breakdowns=breakdowns,
            params=params,
            limit=limit,
        )

    def search_targeting(
        provider: str,
        account_id: str,
        query: str,
        targeting_type: str = "adinterest",
        limit: int = 25,
    ) -> dict:
        validate_provider_account(registry, policy_manager, provider, account_id)
        return registry.get_provider(provider).search_targeting(account_id, query, targeting_type, limit)

    return {
        "get_account_summary": get_account_summary,
        "list_account_objects": list_account_objects,
        "get_account_object": get_account_object,
        "get_flexible_insights": get_flexible_insights,
        "search_targeting": search_targeting,
    }


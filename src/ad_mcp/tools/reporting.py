from __future__ import annotations

from ad_mcp.core.capability_registry import CapabilityRegistry
from ad_mcp.core.models import DateRange, ReportRequest
from ad_mcp.core.policy import PolicyManager
from ad_mcp.tools._shared import validate_provider_account


def build_reporting_tools(
    registry: CapabilityRegistry,
    policy_manager: PolicyManager,
) -> dict[str, callable]:
    def get_performance_report(
        provider: str,
        account_id: str,
        entity_level: str,
        start_date: str,
        end_date: str,
        fields: list[str] | None = None,
        filters: dict | None = None,
        breakdowns: list[str] | None = None,
    ) -> dict:
        validate_provider_account(registry, policy_manager, provider, account_id)
        policy_manager.validate_report_range(start_date, end_date)
        request = ReportRequest(
            provider=provider,
            account_id=account_id,
            entity_level=entity_level,
            date_range=DateRange(start_date=start_date, end_date=end_date),
            fields=fields or [],
            filters=filters or {},
            breakdowns=breakdowns or [],
        )
        response = registry.get_provider(provider).get_report(request)
        return response.model_dump()

    return {"get_performance_report": get_performance_report}

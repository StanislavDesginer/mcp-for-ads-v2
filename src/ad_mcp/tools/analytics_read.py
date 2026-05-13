from __future__ import annotations

from datetime import date

from ad_mcp.core.capability_registry import CapabilityRegistry
from ad_mcp.core.policy import PolicyManager
from ad_mcp.tools._shared import validate_provider_account


def build_analytics_read_tools(
    registry: CapabilityRegistry,
    policy_manager: PolicyManager,
) -> dict[str, callable]:
    def get_spend_overview(provider: str, account_id: str, end_date: str) -> dict:
        validate_provider_account(registry, policy_manager, provider, account_id)
        date.fromisoformat(end_date)
        return registry.get_provider(provider).get_spend_overview(account_id, end_date)

    def estimate_budget_days_remaining(provider: str, account_id: str, end_date: str, lookback_days: int = 7) -> dict:
        validate_provider_account(registry, policy_manager, provider, account_id)
        date.fromisoformat(end_date)
        return registry.get_provider(provider).estimate_budget_days_remaining(account_id, end_date, lookback_days)

    def get_connected_assets(provider: str, account_id: str) -> dict:
        validate_provider_account(registry, policy_manager, provider, account_id)
        return registry.get_provider(provider).get_connected_assets(account_id)

    def get_delivery_issues(provider: str, account_id: str, limit: int = 100) -> dict:
        validate_provider_account(registry, policy_manager, provider, account_id)
        return registry.get_provider(provider).get_delivery_issues(account_id, limit)

    def rank_top_entities(
        provider: str,
        account_id: str,
        entity_level: str,
        start_date: str,
        end_date: str,
        metric: str,
        limit: int = 5,
    ) -> dict:
        validate_provider_account(registry, policy_manager, provider, account_id)
        policy_manager.validate_report_range(start_date, end_date)
        return registry.get_provider(provider).rank_top_entities(account_id, entity_level, start_date, end_date, metric, limit)

    def compare_periods(
        provider: str,
        account_id: str,
        entity_level: str,
        start_date_a: str,
        end_date_a: str,
        start_date_b: str,
        end_date_b: str,
    ) -> dict:
        validate_provider_account(registry, policy_manager, provider, account_id)
        policy_manager.validate_report_range(start_date_a, end_date_a)
        policy_manager.validate_report_range(start_date_b, end_date_b)
        return registry.get_provider(provider).compare_periods(account_id, entity_level, start_date_a, end_date_a, start_date_b, end_date_b)

    def detect_anomalies(provider: str, account_id: str, entity_level: str, end_date: str, lookback_days: int = 7) -> dict:
        validate_provider_account(registry, policy_manager, provider, account_id)
        date.fromisoformat(end_date)
        return registry.get_provider(provider).detect_anomalies(account_id, entity_level, end_date, lookback_days)

    def analyze_audiences(provider: str, account_id: str, start_date: str, end_date: str, limit: int = 20) -> dict:
        validate_provider_account(registry, policy_manager, provider, account_id)
        policy_manager.validate_report_range(start_date, end_date)
        return registry.get_provider(provider).analyze_audiences(account_id, start_date, end_date, limit)

    def find_burnout_ads(provider: str, account_id: str, start_date: str, end_date: str, limit: int = 20) -> dict:
        validate_provider_account(registry, policy_manager, provider, account_id)
        policy_manager.validate_report_range(start_date, end_date)
        return registry.get_provider(provider).find_burnout_ads(account_id, start_date, end_date, limit)

    def audit_account(provider: str, account_id: str, end_date: str) -> dict:
        validate_provider_account(registry, policy_manager, provider, account_id)
        date.fromisoformat(end_date)
        return registry.get_provider(provider).audit_account(account_id, end_date)

    def list_lead_forms(provider: str, account_id: str, page_id: str | None = None, limit: int = 50) -> dict:
        validate_provider_account(registry, policy_manager, provider, account_id)
        return registry.get_provider(provider).list_lead_forms(account_id, page_id, limit)

    def get_recommendations_read(provider: str, account_id: str, limit: int = 25, params: dict | None = None) -> dict:
        validate_provider_account(registry, policy_manager, provider, account_id)
        return registry.get_provider(provider).get_recommendations_read(account_id, limit, params)

    def list_automated_rules(provider: str, account_id: str, limit: int = 50) -> dict:
        validate_provider_account(registry, policy_manager, provider, account_id)
        return registry.get_provider(provider).list_automated_rules(account_id, limit)

    def get_rule_history(provider: str, account_id: str, limit: int = 50) -> dict:
        validate_provider_account(registry, policy_manager, provider, account_id)
        return registry.get_provider(provider).get_rule_history(account_id, limit)

    def get_minimum_budgets_read(provider: str, account_id: str, params: dict | None = None) -> dict:
        validate_provider_account(registry, policy_manager, provider, account_id)
        return registry.get_provider(provider).get_minimum_budgets_read(account_id, params)

    def get_reach_estimate_read(provider: str, account_id: str, params: dict) -> dict:
        validate_provider_account(registry, policy_manager, provider, account_id)
        return registry.get_provider(provider).get_reach_estimate_read(account_id, params)

    def get_tracking_specs(provider: str, account_id: str) -> dict:
        validate_provider_account(registry, policy_manager, provider, account_id)
        return registry.get_provider(provider).get_tracking_specs(account_id)

    def audit_links_and_utms(provider: str, account_id: str, limit: int = 100) -> dict:
        validate_provider_account(registry, policy_manager, provider, account_id)
        return registry.get_provider(provider).audit_links_and_utms(account_id, limit)

    return {
        "get_spend_overview": get_spend_overview,
        "estimate_budget_days_remaining": estimate_budget_days_remaining,
        "get_connected_assets": get_connected_assets,
        "get_delivery_issues": get_delivery_issues,
        "rank_top_entities": rank_top_entities,
        "compare_periods": compare_periods,
        "detect_anomalies": detect_anomalies,
        "analyze_audiences": analyze_audiences,
        "find_burnout_ads": find_burnout_ads,
        "audit_account": audit_account,
        "list_lead_forms": list_lead_forms,
        "get_recommendations_read": get_recommendations_read,
        "list_automated_rules": list_automated_rules,
        "get_rule_history": get_rule_history,
        "get_minimum_budgets_read": get_minimum_budgets_read,
        "get_reach_estimate_read": get_reach_estimate_read,
        "get_tracking_specs": get_tracking_specs,
        "audit_links_and_utms": audit_links_and_utms,
    }

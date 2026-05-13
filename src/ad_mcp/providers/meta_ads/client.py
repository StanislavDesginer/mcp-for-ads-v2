from __future__ import annotations

from ad_mcp.core.models import ReportRequest, ReportResponse
from ad_mcp.core.models import CapabilityMap
from ad_mcp.providers.base.client import BaseAdsProvider
from ad_mcp.providers.meta_ads.account_read import (
    fetch_meta_account_summary,
    fetch_meta_object,
    fetch_meta_objects,
    fetch_meta_flexible_insights,
    search_meta_targeting,
)
from ad_mcp.providers.meta_ads.analysis import (
    analyze_meta_audiences,
    audit_meta_account,
    audit_meta_links_and_utms,
    compare_meta_periods,
    detect_meta_anomalies,
    estimate_meta_budget_days_remaining,
    fetch_meta_connected_assets,
    fetch_meta_delivery_issues,
    fetch_meta_spend_overview,
    find_meta_burnout_ads,
    get_meta_minimum_budgets,
    get_meta_reach_estimate,
    get_meta_recommendations,
    get_meta_rule_history,
    get_meta_tracking_specs,
    list_meta_automated_rules,
    list_meta_lead_forms,
    rank_meta_entities,
)
from ad_mcp.providers.meta_ads.auth import credentials_from_config
from ad_mcp.providers.meta_ads.auth import normalize_meta_account_id
from ad_mcp.providers.meta_ads.billing import fetch_meta_billing_summary
from ad_mcp.providers.meta_ads.payloads import build_meta_ads_payload
from ad_mcp.providers.meta_ads.reporting import fetch_meta_report


class MetaAdsProvider(BaseAdsProvider):
    def __init__(self, config: dict | None = None) -> None:
        super().__init__(
            capabilities=CapabilityMap(
                provider="meta_ads",
                read_objects=[
                    "account",
                    "campaign",
                    "adset",
                    "ad",
                    "creative",
                    "audience",
                    "saved_audience",
                    "pixel",
                    "custom_conversion",
                    "ad_image",
                    "ad_video",
                    "instagram_account",
                    "page",
                    "activity",
                    "user",
                ],
                write_objects=["campaign", "adset", "ad", "creative", "audience", "schedule"],
                supported_metrics=[
                    "reach",
                    "impressions",
                    "interactions",
                    "clicks",
                    "spend",
                    "ctr",
                    "cr",
                    "conversions",
                ],
                supported_dimensions=["date", "campaign", "adset", "ad", "placement", "device_platform"],
                supported_campaign_types=["awareness", "traffic", "engagement", "leads", "sales", "app_promotion"],
                supported_audience_types=["saved", "custom", "lookalike"],
                notes=[
                    "Seeded from local reports-holymedia Meta scripts.",
                    "Real creative and audience creation still needs provider-native translators.",
                ],
            ),
            source_api="meta_marketing_api",
            config=config,
        )

    def get_account_config(self, account_id: str) -> dict:
        requested_id = str(account_id or "").strip()
        normalized_requested_id = normalize_meta_account_id(requested_id)
        for item in self.config.get("accounts", []):
            configured_id = str(item.get("account_id", "")).strip()
            if configured_id == requested_id:
                return item
            if normalize_meta_account_id(configured_id) == normalized_requested_id:
                return item
        return {}

    def get_report(self, request: ReportRequest) -> ReportResponse:
        account_config = self.get_account_config(request.account_id)
        if not account_config:
            return super().get_report(request)
        credentials = credentials_from_config(account_config)
        return fetch_meta_report(credentials, request, self.capabilities.supported_metrics)

    def get_billing_summary(self, account_id: str) -> dict:
        account_config = self.get_account_config(account_id)
        if not account_config:
            return super().get_billing_summary(account_id)
        credentials = credentials_from_config(account_config)
        return fetch_meta_billing_summary(credentials)

    def get_account_summary(self, account_id: str, fields: list[str] | None = None) -> dict:
        account_config = self.get_account_config(account_id)
        if not account_config:
            return super().get_account_summary(account_id, fields)
        credentials = credentials_from_config(account_config)
        return fetch_meta_account_summary(credentials, fields)

    def list_account_objects(
        self,
        account_id: str,
        object_type: str,
        fields: list[str] | None = None,
        params: dict | None = None,
        limit: int = 100,
    ) -> dict:
        account_config = self.get_account_config(account_id)
        if not account_config:
            return super().list_account_objects(account_id, object_type, fields, params, limit)
        credentials = credentials_from_config(account_config)
        return fetch_meta_objects(credentials, object_type, fields, params, limit)

    def get_account_object(
        self,
        account_id: str,
        object_type: str,
        object_id: str,
        fields: list[str] | None = None,
    ) -> dict:
        account_config = self.get_account_config(account_id)
        if not account_config:
            return super().get_account_object(account_id, object_type, object_id, fields)
        credentials = credentials_from_config(account_config)
        return fetch_meta_object(credentials, object_type, object_id, fields)

    def get_flexible_insights(
        self,
        account_id: str,
        level: str,
        start_date: str,
        end_date: str,
        fields: list[str] | None = None,
        breakdowns: list[str] | None = None,
        params: dict | None = None,
        limit: int = 500,
    ) -> dict:
        account_config = self.get_account_config(account_id)
        if not account_config:
            return super().get_flexible_insights(account_id, level, start_date, end_date, fields, breakdowns, params, limit)
        credentials = credentials_from_config(account_config)
        return fetch_meta_flexible_insights(credentials, level, start_date, end_date, fields, breakdowns, params, limit)

    def search_targeting(
        self,
        account_id: str,
        query: str,
        targeting_type: str,
        limit: int = 25,
    ) -> dict:
        account_config = self.get_account_config(account_id)
        if not account_config:
            return super().search_targeting(account_id, query, targeting_type, limit)
        credentials = credentials_from_config(account_config)
        return search_meta_targeting(credentials, query, targeting_type, limit)

    def get_spend_overview(self, account_id: str, end_date: str) -> dict:
        account_config = self.get_account_config(account_id)
        if not account_config:
            return super().get_spend_overview(account_id, end_date)
        credentials = credentials_from_config(account_config)
        return fetch_meta_spend_overview(credentials, end_date)

    def estimate_budget_days_remaining(self, account_id: str, end_date: str, lookback_days: int = 7) -> dict:
        account_config = self.get_account_config(account_id)
        if not account_config:
            return super().estimate_budget_days_remaining(account_id, end_date, lookback_days)
        credentials = credentials_from_config(account_config)
        return estimate_meta_budget_days_remaining(credentials, end_date, lookback_days)

    def get_connected_assets(self, account_id: str) -> dict:
        account_config = self.get_account_config(account_id)
        if not account_config:
            return super().get_connected_assets(account_id)
        credentials = credentials_from_config(account_config)
        return fetch_meta_connected_assets(credentials)

    def get_delivery_issues(self, account_id: str, limit: int = 100) -> dict:
        account_config = self.get_account_config(account_id)
        if not account_config:
            return super().get_delivery_issues(account_id, limit)
        credentials = credentials_from_config(account_config)
        return fetch_meta_delivery_issues(credentials, limit)

    def rank_top_entities(
        self,
        account_id: str,
        entity_level: str,
        start_date: str,
        end_date: str,
        metric: str,
        limit: int = 5,
    ) -> dict:
        account_config = self.get_account_config(account_id)
        if not account_config:
            return super().rank_top_entities(account_id, entity_level, start_date, end_date, metric, limit)
        credentials = credentials_from_config(account_config)
        return rank_meta_entities(credentials, entity_level, start_date, end_date, metric, limit)

    def compare_periods(
        self,
        account_id: str,
        entity_level: str,
        start_date_a: str,
        end_date_a: str,
        start_date_b: str,
        end_date_b: str,
    ) -> dict:
        account_config = self.get_account_config(account_id)
        if not account_config:
            return super().compare_periods(account_id, entity_level, start_date_a, end_date_a, start_date_b, end_date_b)
        credentials = credentials_from_config(account_config)
        return compare_meta_periods(credentials, entity_level, start_date_a, end_date_a, start_date_b, end_date_b)

    def detect_anomalies(self, account_id: str, entity_level: str, end_date: str, lookback_days: int = 7) -> dict:
        account_config = self.get_account_config(account_id)
        if not account_config:
            return super().detect_anomalies(account_id, entity_level, end_date, lookback_days)
        credentials = credentials_from_config(account_config)
        return detect_meta_anomalies(credentials, entity_level, end_date, lookback_days)

    def analyze_audiences(self, account_id: str, start_date: str, end_date: str, limit: int = 20) -> dict:
        account_config = self.get_account_config(account_id)
        if not account_config:
            return super().analyze_audiences(account_id, start_date, end_date, limit)
        credentials = credentials_from_config(account_config)
        return analyze_meta_audiences(credentials, start_date, end_date, limit)

    def find_burnout_ads(self, account_id: str, start_date: str, end_date: str, limit: int = 20) -> dict:
        account_config = self.get_account_config(account_id)
        if not account_config:
            return super().find_burnout_ads(account_id, start_date, end_date, limit)
        credentials = credentials_from_config(account_config)
        return find_meta_burnout_ads(credentials, start_date, end_date, limit)

    def audit_account(self, account_id: str, end_date: str) -> dict:
        account_config = self.get_account_config(account_id)
        if not account_config:
            return super().audit_account(account_id, end_date)
        credentials = credentials_from_config(account_config)
        return audit_meta_account(credentials, end_date)

    def list_lead_forms(self, account_id: str, page_id: str | None = None, limit: int = 50) -> dict:
        account_config = self.get_account_config(account_id)
        if not account_config:
            return super().list_lead_forms(account_id, page_id, limit)
        credentials = credentials_from_config(account_config)
        return list_meta_lead_forms(credentials, page_id, limit)

    def get_recommendations_read(self, account_id: str, limit: int = 25, params: dict | None = None) -> dict:
        account_config = self.get_account_config(account_id)
        if not account_config:
            return super().get_recommendations_read(account_id, limit, params)
        credentials = credentials_from_config(account_config)
        return get_meta_recommendations(credentials, limit, params)

    def list_automated_rules(self, account_id: str, limit: int = 50) -> dict:
        account_config = self.get_account_config(account_id)
        if not account_config:
            return super().list_automated_rules(account_id, limit)
        credentials = credentials_from_config(account_config)
        return list_meta_automated_rules(credentials, limit)

    def get_rule_history(self, account_id: str, limit: int = 50) -> dict:
        account_config = self.get_account_config(account_id)
        if not account_config:
            return super().get_rule_history(account_id, limit)
        credentials = credentials_from_config(account_config)
        return get_meta_rule_history(credentials, limit)

    def get_minimum_budgets_read(self, account_id: str, params: dict | None = None) -> dict:
        account_config = self.get_account_config(account_id)
        if not account_config:
            return super().get_minimum_budgets_read(account_id, params)
        credentials = credentials_from_config(account_config)
        return get_meta_minimum_budgets(credentials, params)

    def get_reach_estimate_read(self, account_id: str, params: dict) -> dict:
        account_config = self.get_account_config(account_id)
        if not account_config:
            return super().get_reach_estimate_read(account_id, params)
        credentials = credentials_from_config(account_config)
        return get_meta_reach_estimate(credentials, params)

    def get_tracking_specs(self, account_id: str) -> dict:
        account_config = self.get_account_config(account_id)
        if not account_config:
            return super().get_tracking_specs(account_id)
        credentials = credentials_from_config(account_config)
        return get_meta_tracking_specs(credentials)

    def audit_links_and_utms(self, account_id: str, limit: int = 100) -> dict:
        account_config = self.get_account_config(account_id)
        if not account_config:
            return super().audit_links_and_utms(account_id, limit)
        credentials = credentials_from_config(account_config)
        return audit_meta_links_and_utms(credentials, limit)

    def build_provider_payload(self, action: str, account_id: str, object_type: str, payload: dict) -> dict:
        provider_payload = build_meta_ads_payload(action, object_type, payload)
        provider_payload["account_id"] = account_id
        return provider_payload

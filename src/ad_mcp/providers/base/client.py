from __future__ import annotations

from abc import ABC
from typing import Any

from ad_mcp.core.errors import ValidationError
from ad_mcp.core.models import (
    AccountRef,
    CapabilityMap,
    ObjectMutationResponse,
    PreviewRecord,
    ReportRequest,
    ReportResponse,
)
from ad_mcp.core.normalization import split_requested_fields


class BaseAdsProvider(ABC):
    _ALIAS_GROUPS = (
        ("ad_group", "adgroup", "adset"),
        ("asset", "extension"),
    )

    def __init__(
        self,
        capabilities: CapabilityMap,
        source_api: str,
        config: dict[str, Any] | None = None,
    ) -> None:
        self.capabilities = capabilities
        self.source_api = source_api
        self.config = config or {}

    def list_accounts(self) -> list[AccountRef]:
        accounts: list[AccountRef] = []
        for item in self.config.get("accounts", []):
            accounts.append(
                AccountRef(
                    provider=self.capabilities.provider,
                    account_id=str(item.get("account_id", "")),
                    name=item.get("name"),
                    status=item.get("status", "configured"),
                )
            )
        return accounts

    def get_account_config(self, account_id: str) -> dict[str, Any]:
        for item in self.config.get("accounts", []):
            if str(item.get("account_id")) == str(account_id):
                return item
        return {}

    def _canonicalize_name(self, value: str, supported: list[str]) -> str:
        if value in supported:
            return value
        for alias_group in self._ALIAS_GROUPS:
            if value in alias_group:
                for candidate in alias_group:
                    if candidate in supported:
                        return candidate
        return value

    def ensure_valid_entity_level(self, entity_level: str) -> str:
        canonical = self._canonicalize_name(entity_level, self.capabilities.read_objects)
        if canonical not in self.capabilities.read_objects:
            raise ValidationError(
                f"Entity level '{entity_level}' is not supported by provider '{self.capabilities.provider}'."
            )
        return canonical

    def ensure_valid_object_type(self, object_type: str) -> str:
        supported = set(self.capabilities.read_objects) | set(self.capabilities.write_objects)
        canonical = self._canonicalize_name(object_type, list(supported))
        if canonical not in supported:
            raise ValidationError(
                f"Object type '{object_type}' is not supported by provider '{self.capabilities.provider}'."
            )
        return canonical

    def build_provider_payload(
        self,
        action: str,
        account_id: str,
        object_type: str,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        return {
            "provider": self.capabilities.provider,
            "action": action,
            "account_id": account_id,
            "object_type": object_type,
            "payload": payload,
        }

    def get_report(self, request: ReportRequest) -> ReportResponse:
        request.entity_level = self.ensure_valid_entity_level(request.entity_level)
        matched, unsupported = split_requested_fields(
            request.fields or self.capabilities.supported_metrics,
            self.capabilities.supported_metrics,
        )
        return ReportResponse(
            provider=self.capabilities.provider,
            entity_level=request.entity_level,
            date_range=request.date_range,
            rows=[],
            normalized_metrics=matched,
            native_metrics=[],
            unsupported_requested_fields=unsupported,
            source_api=self.source_api,
            preview=True,
        )

    def get_billing_summary(self, account_id: str) -> dict[str, Any]:
        return {
            "provider": self.capabilities.provider,
            "account_id": account_id,
            "status": "unsupported",
            "message": "Billing summary is not implemented for this provider yet.",
        }

    def get_account_summary(self, account_id: str, fields: list[str] | None = None) -> dict[str, Any]:
        return {
            "provider": self.capabilities.provider,
            "account_id": account_id,
            "status": "unsupported",
            "message": "Account summary is not implemented for this provider yet.",
        }

    def list_account_objects(
        self,
        account_id: str,
        object_type: str,
        fields: list[str] | None = None,
        params: dict[str, Any] | None = None,
        limit: int = 100,
    ) -> dict[str, Any]:
        return {
            "provider": self.capabilities.provider,
            "account_id": account_id,
            "object_type": object_type,
            "status": "unsupported",
            "message": "Object listing is not implemented for this provider yet.",
        }

    def get_account_object(
        self,
        account_id: str,
        object_type: str,
        object_id: str,
        fields: list[str] | None = None,
    ) -> dict[str, Any]:
        return {
            "provider": self.capabilities.provider,
            "account_id": account_id,
            "object_type": object_type,
            "object_id": object_id,
            "status": "unsupported",
            "message": "Object retrieval is not implemented for this provider yet.",
        }

    def get_flexible_insights(
        self,
        account_id: str,
        level: str,
        start_date: str,
        end_date: str,
        fields: list[str] | None = None,
        breakdowns: list[str] | None = None,
        params: dict[str, Any] | None = None,
        limit: int = 500,
    ) -> dict[str, Any]:
        return {
            "provider": self.capabilities.provider,
            "account_id": account_id,
            "level": level,
            "status": "unsupported",
            "message": "Flexible insights are not implemented for this provider yet.",
        }

    def search_targeting(
        self,
        account_id: str,
        query: str,
        targeting_type: str,
        limit: int = 25,
    ) -> dict[str, Any]:
        return {
            "provider": self.capabilities.provider,
            "account_id": account_id,
            "targeting_type": targeting_type,
            "query": query,
            "status": "unsupported",
            "message": "Targeting search is not implemented for this provider yet.",
        }

    def get_spend_overview(self, account_id: str, end_date: str) -> dict[str, Any]:
        return {
            "provider": self.capabilities.provider,
            "account_id": account_id,
            "status": "unsupported",
            "message": "Spend overview is not implemented for this provider yet.",
        }

    def estimate_budget_days_remaining(self, account_id: str, end_date: str, lookback_days: int = 7) -> dict[str, Any]:
        return {
            "provider": self.capabilities.provider,
            "account_id": account_id,
            "status": "unsupported",
            "message": "Budget runway estimation is not implemented for this provider yet.",
        }

    def get_connected_assets(self, account_id: str) -> dict[str, Any]:
        return {
            "provider": self.capabilities.provider,
            "account_id": account_id,
            "status": "unsupported",
            "message": "Connected assets inspection is not implemented for this provider yet.",
        }

    def get_delivery_issues(self, account_id: str, limit: int = 100) -> dict[str, Any]:
        return {
            "provider": self.capabilities.provider,
            "account_id": account_id,
            "status": "unsupported",
            "message": "Delivery issue detection is not implemented for this provider yet.",
        }

    def rank_top_entities(
        self,
        account_id: str,
        entity_level: str,
        start_date: str,
        end_date: str,
        metric: str,
        limit: int = 5,
    ) -> dict[str, Any]:
        return {
            "provider": self.capabilities.provider,
            "account_id": account_id,
            "status": "unsupported",
            "message": "Top entity ranking is not implemented for this provider yet.",
        }

    def compare_periods(
        self,
        account_id: str,
        entity_level: str,
        start_date_a: str,
        end_date_a: str,
        start_date_b: str,
        end_date_b: str,
    ) -> dict[str, Any]:
        return {
            "provider": self.capabilities.provider,
            "account_id": account_id,
            "status": "unsupported",
            "message": "Period comparison is not implemented for this provider yet.",
        }

    def detect_anomalies(self, account_id: str, entity_level: str, end_date: str, lookback_days: int = 7) -> dict[str, Any]:
        return {
            "provider": self.capabilities.provider,
            "account_id": account_id,
            "status": "unsupported",
            "message": "Anomaly detection is not implemented for this provider yet.",
        }

    def analyze_audiences(self, account_id: str, start_date: str, end_date: str, limit: int = 20) -> dict[str, Any]:
        return {
            "provider": self.capabilities.provider,
            "account_id": account_id,
            "status": "unsupported",
            "message": "Audience analysis is not implemented for this provider yet.",
        }

    def find_burnout_ads(self, account_id: str, start_date: str, end_date: str, limit: int = 20) -> dict[str, Any]:
        return {
            "provider": self.capabilities.provider,
            "account_id": account_id,
            "status": "unsupported",
            "message": "Creative burnout analysis is not implemented for this provider yet.",
        }

    def audit_account(self, account_id: str, end_date: str) -> dict[str, Any]:
        return {
            "provider": self.capabilities.provider,
            "account_id": account_id,
            "status": "unsupported",
            "message": "Account audit is not implemented for this provider yet.",
        }

    def list_lead_forms(self, account_id: str, page_id: str | None = None, limit: int = 50) -> dict[str, Any]:
        return {
            "provider": self.capabilities.provider,
            "account_id": account_id,
            "status": "unsupported",
            "message": "Lead forms listing is not implemented for this provider yet.",
        }

    def get_recommendations_read(self, account_id: str, limit: int = 25, params: dict[str, Any] | None = None) -> dict[str, Any]:
        return {
            "provider": self.capabilities.provider,
            "account_id": account_id,
            "status": "unsupported",
            "message": "Recommendations listing is not implemented for this provider yet.",
        }

    def list_automated_rules(self, account_id: str, limit: int = 50) -> dict[str, Any]:
        return {
            "provider": self.capabilities.provider,
            "account_id": account_id,
            "status": "unsupported",
            "message": "Automated rules listing is not implemented for this provider yet.",
        }

    def get_rule_history(self, account_id: str, limit: int = 50) -> dict[str, Any]:
        return {
            "provider": self.capabilities.provider,
            "account_id": account_id,
            "status": "unsupported",
            "message": "Rule history is not implemented for this provider yet.",
        }

    def get_minimum_budgets_read(self, account_id: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        return {
            "provider": self.capabilities.provider,
            "account_id": account_id,
            "status": "unsupported",
            "message": "Minimum budget lookup is not implemented for this provider yet.",
        }

    def get_reach_estimate_read(self, account_id: str, params: dict[str, Any]) -> dict[str, Any]:
        return {
            "provider": self.capabilities.provider,
            "account_id": account_id,
            "status": "unsupported",
            "message": "Reach estimate is not implemented for this provider yet.",
        }

    def get_tracking_specs(self, account_id: str) -> dict[str, Any]:
        return {
            "provider": self.capabilities.provider,
            "account_id": account_id,
            "status": "unsupported",
            "message": "Tracking inspection is not implemented for this provider yet.",
        }

    def audit_links_and_utms(self, account_id: str, limit: int = 100) -> dict[str, Any]:
        return {
            "provider": self.capabilities.provider,
            "account_id": account_id,
            "status": "unsupported",
            "message": "Link and UTM audit is not implemented for this provider yet.",
        }

    def preview_mutation(
        self,
        action: str,
        account_id: str,
        object_type: str,
        payload: dict[str, Any],
    ) -> PreviewRecord:
        object_type = self.ensure_valid_object_type(object_type)
        provider_payload = self.build_provider_payload(action, account_id, object_type, payload)
        diff = {"requested_payload": payload, "provider_payload_summary": provider_payload}
        risk_flags: list[str] = []
        if payload.get("budget_delta_percent", 0) and payload["budget_delta_percent"] > 30:
            risk_flags.append("large_budget_change")
        if payload.get("bulk_count", 0) and payload["bulk_count"] > 50:
            risk_flags.append("large_bulk_operation")
        if action in {"delete_or_archive"}:
            risk_flags.append("destructive_operation")
        return PreviewRecord(
            action=action,  # type: ignore[arg-type]
            provider=self.capabilities.provider,
            account_id=account_id,
            object_type=object_type,
            payload=payload,
            provider_payload=provider_payload,
            diff=diff,
            risk_flags=risk_flags,
        )

    def commit_preview(self, preview: PreviewRecord) -> ObjectMutationResponse:
        return ObjectMutationResponse(
            status="blocked",
            provider=preview.provider,
            account_id=preview.account_id,
            object_type=preview.object_type,
            action=preview.action,
            diff=preview.diff,
            risk_flags=preview.risk_flags,
            provider_payload=preview.provider_payload,
            provider_response={
                "mode": "preview_only",
                "message": "Beta MVP is preview-only. No external mutation was executed.",
                "source_api": self.source_api,
            },
        )

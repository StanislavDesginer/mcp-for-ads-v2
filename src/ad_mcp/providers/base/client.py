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
            status="committed",
            provider=preview.provider,
            account_id=preview.account_id,
            object_type=preview.object_type,
            action=preview.action,
            diff=preview.diff,
            risk_flags=preview.risk_flags,
            provider_payload=preview.provider_payload,
            provider_response={
                "mode": "simulated_no_write",
                "message": "Provider write path is intentionally simulated. No external mutation was executed.",
                "source_api": self.source_api,
                "would_send": preview.provider_payload,
            },
        )

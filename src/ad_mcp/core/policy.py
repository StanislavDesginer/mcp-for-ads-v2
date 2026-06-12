from __future__ import annotations

from datetime import date

from pydantic import BaseModel, Field

from ad_mcp.core.errors import PolicyViolationError


class SafetyPolicy(BaseModel):
    preview_only: bool = True
    write_mode: str = "preview_confirm"
    execution_mode: str = "simulated_no_write"
    allow_unknown_accounts: bool = False
    max_budget_delta_percent: int = 30
    max_bulk_object_count: int = 50
    max_report_days: int = 93
    require_confirm_for: list[str] = Field(default_factory=lambda: ["create", "update", "delete_or_archive"])


class PolicyManager:
    def __init__(self, policy: SafetyPolicy) -> None:
        self.policy = policy

    @property
    def preview_only_enabled(self) -> bool:
        return self.policy.preview_only or self.policy.execution_mode == "simulated_no_write"

    def validate_account_access(self, configured: bool) -> None:
        if not configured and not self.policy.allow_unknown_accounts:
            raise PolicyViolationError("Account is not configured in the provider allowlist.")

    def validate_mutation_payload(self, payload: dict) -> None:
        budget_delta = payload.get("budget_delta_percent", 0) or 0
        bulk_count = payload.get("bulk_count", 0) or 0
        if abs(budget_delta) > self.policy.max_budget_delta_percent:
            raise PolicyViolationError(
                f"budget_delta_percent={budget_delta} exceeds max_budget_delta_percent={self.policy.max_budget_delta_percent}"
            )
        if bulk_count > self.policy.max_bulk_object_count:
            raise PolicyViolationError(
                f"bulk_count={bulk_count} exceeds max_bulk_object_count={self.policy.max_bulk_object_count}"
            )

    def validate_report_range(self, start_date: str, end_date: str) -> None:
        start = date.fromisoformat(start_date)
        end = date.fromisoformat(end_date)
        if end < start:
            raise PolicyViolationError("end_date must be greater than or equal to start_date.")
        if (end - start).days > self.policy.max_report_days:
            raise PolicyViolationError(
                f"Requested report window exceeds max_report_days={self.policy.max_report_days}."
            )

    def ensure_simulated_no_write(self) -> None:
        if not self.preview_only_enabled:
            raise PolicyViolationError(
                f"Unsupported execution_mode='{self.policy.execution_mode}'. Only simulated_no_write is allowed in this build."
            )

    def ensure_preview_only(self) -> None:
        if not self.preview_only_enabled:
            raise PolicyViolationError("PREVIEW_ONLY is disabled. Beta MVP requires preview-only mode for write actions.")

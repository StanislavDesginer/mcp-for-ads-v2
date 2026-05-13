from __future__ import annotations

from typing import Any

from ad_mcp.providers.meta_ads.auth import MetaAccountCredentials

try:
    from facebook_business.adobjects.adaccount import AdAccount
    from facebook_business.api import FacebookAdsApi
except ImportError:  # pragma: no cover
    AdAccount = None
    FacebookAdsApi = None


ACCOUNT_BILLING_FIELDS = [
    "id",
    "name",
    "account_status",
    "currency",
    "timezone_name",
    "balance",
    "amount_spent",
    "spend_cap",
    "funding_source",
    "funding_source_details",
    "is_prepay_account",
    "disable_reason",
    "min_daily_budget",
]


def _export_value(value: Any) -> Any:
    if hasattr(value, "export_all_data"):
        return value.export_all_data()
    if isinstance(value, dict):
        return {key: _export_value(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_export_value(item) for item in value]
    return value


def _money_from_minor_units(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        return round(float(value) / 100, 2)
    except (TypeError, ValueError):
        return None


def fetch_meta_billing_summary(credentials: MetaAccountCredentials) -> dict[str, Any]:
    if FacebookAdsApi is None or AdAccount is None:
        return {
            "provider": "meta_ads",
            "account_id": credentials.account_id,
            "status": "preview",
            "message": "facebook-business SDK is not installed; returning billing field shape only.",
            "available_fields": ACCOUNT_BILLING_FIELDS,
        }

    FacebookAdsApi.init(
        credentials.app_id,
        credentials.app_secret,
        credentials.access_token,
        api_version=credentials.api_version,
    )
    account = AdAccount(f"act_{credentials.account_id}").api_get(fields=ACCOUNT_BILLING_FIELDS)
    raw = _export_value(dict(account))
    funding_details = _export_value(raw.get("funding_source_details") or {})

    return {
        "provider": "meta_ads",
        "account_id": raw.get("id") or f"act_{credentials.account_id}",
        "account_name": raw.get("name") or credentials.name,
        "account_status": raw.get("account_status"),
        "currency": raw.get("currency"),
        "timezone_name": raw.get("timezone_name"),
        "billing": {
            "balance_due": _money_from_minor_units(raw.get("balance")),
            "amount_spent_lifetime": _money_from_minor_units(raw.get("amount_spent")),
            "spend_cap": _money_from_minor_units(raw.get("spend_cap")),
            "has_spend_cap": str(raw.get("spend_cap") or "0") != "0",
            "is_prepay_account": raw.get("is_prepay_account"),
            "min_daily_budget": _money_from_minor_units(raw.get("min_daily_budget")),
        },
        "payment_method": {
            "funding_source_id": raw.get("funding_source"),
            "display_string": funding_details.get("display_string"),
            "type": funding_details.get("type"),
            "coupons": funding_details.get("coupons", []),
        },
        "unsupported_fields": [
            "payment_threshold",
            "next_charge_date",
        ],
        "notes": [
            "Meta returns monetary ad account fields in minor currency units; values here are normalized by dividing by 100.",
            "Exact payment threshold and next charge date are not exposed by this tool/API response.",
        ],
        "source_api": "meta_marketing_api",
        "preview": False,
    }

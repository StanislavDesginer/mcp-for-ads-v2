from __future__ import annotations

from datetime import date, timedelta
from typing import Any

from ad_mcp.core.config_loader import load_provider_from_connections, load_safety_policy
from ad_mcp.core.models import ObjectMutationResponse
from ad_mcp.core.policy import PolicyManager
from ad_mcp.core.preview_manager import PreviewManager
from ad_mcp.providers.meta_ads.client import MetaAdsProvider
from ad_mcp.settings import Settings


class MetaDashboardService:
    def __init__(self) -> None:
        settings = Settings()
        self._policy_manager = PolicyManager(load_safety_policy(settings.policy_config_path))
        provider_config = load_provider_from_connections(settings.connections_config_path, "meta_ads")
        self._provider = MetaAdsProvider(config=provider_config)
        self._preview_manager = PreviewManager()

    def _default_account_id(self) -> str:
        accounts = self._provider.config.get("accounts", [])
        if not accounts:
            raise ValueError("No configured Meta Ads accounts found.")
        return str(accounts[0].get("account_id", "")).strip()

    def _resolve_account_id(self, account_id: str | None) -> str:
        return str(account_id or self._default_account_id()).strip()

    def _date_window(self, end_date: str | None = None, lookback_days: int = 7) -> tuple[str, str, str]:
        resolved_end = date.fromisoformat(end_date) if end_date else date.today()
        resolved_start = resolved_end - timedelta(days=max(lookback_days - 1, 0))
        start_date = resolved_start.isoformat()
        end_date_iso = resolved_end.isoformat()
        self._policy_manager.validate_report_range(start_date, end_date_iso)
        return start_date, start_date, end_date_iso

    def _count_statuses(self, rows: list[dict[str, Any]]) -> dict[str, int]:
        result: dict[str, int] = {}
        for row in rows:
            status = str(row.get("effective_status") or row.get("status") or "UNKNOWN")
            result[status] = result.get(status, 0) + 1
        return result

    def dashboard(self, account_id: str | None = None, end_date: str | None = None) -> dict[str, Any]:
        resolved_account_id = self._resolve_account_id(account_id)
        provider = self._provider
        account = provider.get_account_summary(resolved_account_id)
        spend = provider.get_spend_overview(resolved_account_id, end_date or date.today().isoformat())
        billing = provider.get_billing_summary(resolved_account_id)
        campaigns = provider.list_account_objects(resolved_account_id, "campaign", limit=200).get("rows", [])
        adsets = provider.list_account_objects(resolved_account_id, "adset", limit=500).get("rows", [])
        ads = provider.list_account_objects(resolved_account_id, "ad", limit=1000).get("rows", [])
        issues = provider.get_delivery_issues(resolved_account_id, 20)
        return {
            "provider": "meta_ads",
            "account_id": resolved_account_id,
            "account": account,
            "billing": billing,
            "spend": spend,
            "issues": issues,
            "totals": {
                "campaigns": len(campaigns),
                "adsets": len(adsets),
                "ads": len(ads),
            },
            "statuses": {
                "campaigns": self._count_statuses(campaigns),
                "adsets": self._count_statuses(adsets),
                "ads": self._count_statuses(ads),
            },
        }

    def campaign_structure(self, account_id: str | None = None) -> dict[str, Any]:
        resolved_account_id = self._resolve_account_id(account_id)
        campaigns = self._provider.list_account_objects(resolved_account_id, "campaign", limit=20).get("rows", [])
        adsets = self._provider.list_account_objects(resolved_account_id, "adset", limit=500).get("rows", [])
        ads = self._provider.list_account_objects(resolved_account_id, "ad", limit=1000).get("rows", [])
        adsets_by_campaign: dict[str, list[dict[str, Any]]] = {}
        ads_by_adset: dict[str, list[dict[str, Any]]] = {}
        for adset in adsets:
            adsets_by_campaign.setdefault(str(adset.get("campaign_id")), []).append(adset)
        for ad in ads:
            ads_by_adset.setdefault(str(ad.get("adset_id")), []).append(ad)
        rows: list[dict[str, Any]] = []
        for campaign in campaigns:
            campaign_adsets = adsets_by_campaign.get(str(campaign.get("id")), [])
            rows.append(
                {
                    "campaign_id": campaign.get("id"),
                    "campaign_name": campaign.get("name"),
                    "campaign_status": campaign.get("effective_status") or campaign.get("status"),
                    "adsets": [
                        {
                            "adset_id": adset.get("id"),
                            "adset_name": adset.get("name"),
                            "adset_status": adset.get("effective_status") or adset.get("status"),
                            "ads": [
                                {
                                    "ad_id": ad.get("id"),
                                    "ad_name": ad.get("name"),
                                    "ad_status": ad.get("effective_status") or ad.get("status"),
                                }
                                for ad in ads_by_adset.get(str(adset.get("id")), [])[:20]
                            ],
                        }
                        for adset in campaign_adsets[:20]
                    ],
                }
            )
        return {"provider": "meta_ads", "account_id": resolved_account_id, "rows": rows}

    def delivery_issues(self, account_id: str | None = None, limit: int = 20) -> dict[str, Any]:
        resolved_account_id = self._resolve_account_id(account_id)
        return self._provider.get_delivery_issues(resolved_account_id, limit)

    def connected_assets(self, account_id: str | None = None) -> dict[str, Any]:
        resolved_account_id = self._resolve_account_id(account_id)
        return self._provider.get_connected_assets(resolved_account_id)

    def top_performers(
        self,
        account_id: str | None = None,
        end_date: str | None = None,
        lookback_days: int = 7,
        entity_level: str = "campaign",
        metric: str = "cost_per_result",
        limit: int = 5,
    ) -> dict[str, Any]:
        resolved_account_id = self._resolve_account_id(account_id)
        start_date, _, end_date_iso = self._date_window(end_date=end_date, lookback_days=lookback_days)
        return self._provider.rank_top_entities(
            resolved_account_id,
            entity_level,
            start_date,
            end_date_iso,
            metric,
            limit,
        )

    def no_result_entities(
        self,
        account_id: str | None = None,
        end_date: str | None = None,
        lookback_days: int = 7,
        entity_level: str = "ad",
        min_spend: float = 20.0,
        limit: int = 10,
    ) -> dict[str, Any]:
        resolved_account_id = self._resolve_account_id(account_id)
        start_date, _, end_date_iso = self._date_window(end_date=end_date, lookback_days=lookback_days)
        ranked = self._provider.rank_top_entities(
            resolved_account_id,
            entity_level,
            start_date,
            end_date_iso,
            "spend",
            300,
        )
        rows = [
            row
            for row in ranked.get("rows", [])
            if float(row.get("spend", 0) or 0) >= min_spend and float(row.get("conversions", 0) or 0) == 0
        ]
        rows.sort(key=lambda row: float(row.get("spend", 0) or 0), reverse=True)
        return {
            "provider": "meta_ads",
            "account_id": resolved_account_id,
            "entity_level": entity_level,
            "rows": rows[:limit],
        }

    def _build_preview_response(self, action: str, account_id: str, object_type: str, payload: dict[str, Any]) -> dict[str, Any]:
        self._policy_manager.ensure_simulated_no_write()
        self._policy_manager.validate_mutation_payload(payload)
        preview = self._provider.preview_mutation(action, account_id, object_type, payload)
        self._preview_manager.create(preview)
        return ObjectMutationResponse(
            status="preview",
            provider="meta_ads",
            account_id=account_id,
            object_type=object_type,
            action=action,  # type: ignore[arg-type]
            preview_token=preview.token,
            diff=preview.diff,
            risk_flags=preview.risk_flags,
            provider_payload=preview.provider_payload,
        ).model_dump()

    def preview_clone_campaign(
        self,
        source_campaign_id: str,
        new_name: str | None = None,
        daily_budget: float | None = None,
        lifetime_budget: float | None = None,
        status: str = "PAUSED",
        account_id: str | None = None,
    ) -> dict[str, Any]:
        resolved_account_id = self._resolve_account_id(account_id)
        payload = {
            "name": new_name,
            "status": status,
            "daily_budget": daily_budget,
            "lifetime_budget": lifetime_budget,
            "source_campaign_id": source_campaign_id,
            "clone_options": {"include_adsets": True, "include_ads": True},
        }
        return self._build_preview_response("create", resolved_account_id, "campaign", payload)

    def preview_update_campaign_budget(
        self,
        campaign_id: str,
        daily_budget: float | None = None,
        lifetime_budget: float | None = None,
        spend_cap: float | None = None,
        budget_delta_percent: float | None = None,
        account_id: str | None = None,
    ) -> dict[str, Any]:
        resolved_account_id = self._resolve_account_id(account_id)
        payload = {
            "id": campaign_id,
            "daily_budget": daily_budget,
            "lifetime_budget": lifetime_budget,
            "spend_cap": spend_cap,
            "budget_delta_percent": budget_delta_percent,
        }
        return self._build_preview_response("update", resolved_account_id, "campaign", payload)

    def preview_pause_ads(self, ids: list[str], account_id: str | None = None) -> dict[str, Any]:
        resolved_account_id = self._resolve_account_id(account_id)
        payload = {
            "ids": ids,
            "status": "PAUSED",
            "bulk_count": len(ids),
            "extra_fields": {"operation": "bulk_pause"},
        }
        return self._build_preview_response("update", resolved_account_id, "ad", payload)

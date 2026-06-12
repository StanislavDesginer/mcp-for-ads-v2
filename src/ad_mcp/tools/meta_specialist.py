from __future__ import annotations

from calendar import monthrange
from datetime import date

from ad_mcp.core.capability_registry import CapabilityRegistry
from ad_mcp.core.models import ObjectMutationResponse
from ad_mcp.core.policy import PolicyManager
from ad_mcp.core.preview_manager import PreviewManager
from ad_mcp.tools._shared import validate_provider_account


PREVIEW_ONLY_REASON = "Beta MVP работает в preview-only mode. Реальные изменения отключены."
PREVIEW_ONLY_NOTE = "Реальное изменение не выполнено."


def build_meta_specialist_tools(
    registry: CapabilityRegistry,
    preview_manager: PreviewManager,
    policy_manager: PolicyManager,
) -> dict[str, callable]:
    def _meta_only(provider: str) -> None:
        if provider != "meta_ads":
            raise ValueError("This tool is currently implemented only for provider='meta_ads'.")

    def _preview(action: str, provider: str, account_id: str, object_type: str, payload: dict) -> dict:
        _meta_only(provider)
        policy_manager.ensure_simulated_no_write()
        validate_provider_account(registry, policy_manager, provider, account_id)
        policy_manager.validate_mutation_payload(payload)
        preview = registry.get_provider(provider).preview_mutation(
            action=action,
            account_id=account_id,
            object_type=object_type,
            payload=payload,
        )
        preview_manager.create(preview)
        response = ObjectMutationResponse(
            status="preview",
            provider=provider,
            account_id=account_id,
            object_type=object_type,
            action=action,  # type: ignore[arg-type]
            preview_token=preview.token,
            diff=preview.diff,
            risk_flags=preview.risk_flags,
            provider_payload=preview.provider_payload,
        ).model_dump()
        response.update(
            {
                "mode": "preview_only",
                "will_apply": False,
                "reason": PREVIEW_ONLY_REASON,
                "note": PREVIEW_ONLY_NOTE,
            }
        )
        return response

    def get_status_summary(provider: str, account_id: str) -> dict:
        _meta_only(provider)
        validate_provider_account(registry, policy_manager, provider, account_id)
        provider_client = registry.get_provider(provider)
        campaigns = provider_client.list_account_objects(account_id, "campaign", limit=200)["rows"]
        adsets = provider_client.list_account_objects(account_id, "adset", limit=200)["rows"]
        ads = provider_client.list_account_objects(account_id, "ad", limit=200)["rows"]

        def _count(rows: list[dict], key: str = "effective_status") -> dict:
            result: dict[str, int] = {}
            for row in rows:
                status = row.get(key) or row.get("status") or "UNKNOWN"
                result[status] = result.get(status, 0) + 1
            return result

        return {
            "provider": provider,
            "account_id": account_id,
            "campaign_statuses": _count(campaigns),
            "adset_statuses": _count(adsets),
            "ad_statuses": _count(ads),
            "totals": {
                "campaigns": len(campaigns),
                "adsets": len(adsets),
                "ads": len(ads),
            },
            "preview": False,
        }

    def get_breakdown_preset(
        provider: str,
        account_id: str,
        preset: str,
        start_date: str,
        end_date: str,
        level: str = "campaign",
        limit: int = 200,
    ) -> dict:
        _meta_only(provider)
        validate_provider_account(registry, policy_manager, provider, account_id)
        policy_manager.validate_report_range(start_date, end_date)
        preset_map = {
            "placement": ["publisher_platform", "platform_position"],
            "publisher_platform": ["publisher_platform"],
            "device": ["device_platform"],
            "age_gender": ["age", "gender"],
            "region": ["country", "region"],
        }
        breakdowns = preset_map.get(preset)
        if not breakdowns:
            raise ValueError(f"Unsupported preset='{preset}'. Supported: {sorted(preset_map.keys())}")
        return registry.get_provider(provider).get_flexible_insights(
            account_id=account_id,
            level=level,
            start_date=start_date,
            end_date=end_date,
            fields=[
                "date_start",
                "campaign_name",
                "adset_name",
                "ad_name",
                "spend",
                "impressions",
                "reach",
                "inline_link_clicks",
                "ctr",
                "cpm",
                "actions",
            ],
            breakdowns=breakdowns,
            params={"time_increment": "all_days"},
            limit=limit,
        )

    def find_wasting_spend(
        provider: str,
        account_id: str,
        start_date: str,
        end_date: str,
        entity_level: str = "ad",
        min_spend: float = 20.0,
        limit: int = 20,
    ) -> dict:
        _meta_only(provider)
        validate_provider_account(registry, policy_manager, provider, account_id)
        policy_manager.validate_report_range(start_date, end_date)
        result = registry.get_provider(provider).rank_top_entities(
            account_id=account_id,
            entity_level=entity_level,
            start_date=start_date,
            end_date=end_date,
            metric="spend",
            limit=200,
        )
        rows = [row for row in result["rows"] if row.get("spend", 0) >= min_spend and row.get("conversions", 0) == 0]
        rows.sort(key=lambda row: row.get("spend", 0), reverse=True)
        return {
            "provider": provider,
            "account_id": account_id,
            "entity_level": entity_level,
            "min_spend": min_spend,
            "rows": rows[:limit],
            "preview": False,
        }

    def compare_creatives(
        provider: str,
        account_id: str,
        start_date: str,
        end_date: str,
        adset_id: str | None = None,
        limit: int = 20,
    ) -> dict:
        _meta_only(provider)
        validate_provider_account(registry, policy_manager, provider, account_id)
        policy_manager.validate_report_range(start_date, end_date)
        params = {"time_increment": "all_days"}
        fields = ["ad_id", "ad_name", "adset_id", "adset_name", "spend", "impressions", "inline_link_clicks", "ctr", "cpm", "actions"]
        rows = registry.get_provider(provider).get_flexible_insights(
            account_id=account_id,
            level="ad",
            start_date=start_date,
            end_date=end_date,
            fields=fields,
            breakdowns=[],
            params=params,
            limit=500,
        )["rows"]
        filtered = [row for row in rows if not adset_id or str(row.get("adset_id")) == str(adset_id)]
        grouped: dict[str, dict] = {}
        for row in filtered:
            key = row.get("ad_id") or row.get("ad_name")
            item = grouped.setdefault(
                key,
                {
                    "ad_id": row.get("ad_id"),
                    "ad_name": row.get("ad_name"),
                    "adset_id": row.get("adset_id"),
                    "adset_name": row.get("adset_name"),
                    "spend": 0.0,
                    "impressions": 0.0,
                    "clicks": 0.0,
                    "conversions": 0.0,
                },
            )
            item["spend"] += float(row.get("spend") or 0)
            item["impressions"] += float(row.get("impressions") or 0)
            item["clicks"] += float(row.get("inline_link_clicks") or 0)
            for action in row.get("actions") or []:
                try:
                    item["conversions"] += float(action.get("value") or 0)
                except (TypeError, ValueError):
                    pass
        result_rows = []
        for item in grouped.values():
            impressions = item["impressions"]
            clicks = item["clicks"]
            spend = item["spend"]
            conversions = item["conversions"]
            result_rows.append(
                {
                    **item,
                    "ctr": round((clicks / impressions * 100) if impressions else 0.0, 4),
                    "cpc": round((spend / clicks) if clicks else 0.0, 2),
                    "cost_per_result": round((spend / conversions) if conversions else 0.0, 2),
                }
            )
        result_rows.sort(key=lambda row: (row["cost_per_result"] if row["conversions"] else 999999, -row["ctr"]))
        return {
            "provider": provider,
            "account_id": account_id,
            "adset_id": adset_id,
            "rows": result_rows[:limit],
            "preview": False,
        }

    def get_executive_summary(provider: str, account_id: str, end_date: str) -> dict:
        _meta_only(provider)
        validate_provider_account(registry, policy_manager, provider, account_id)
        spend = registry.get_provider(provider).get_spend_overview(account_id, end_date)
        issues = registry.get_provider(provider).get_delivery_issues(account_id, 20)
        audit = registry.get_provider(provider).audit_account(account_id, end_date)
        return {
            "provider": provider,
            "account_id": account_id,
            "summary": {
                "today": next((x for x in spend["periods"] if x["period"] == "today"), None),
                "last_7_days": next((x for x in spend["periods"] if x["period"] == "last_7_days"), None),
                "last_30_days": next((x for x in spend["periods"] if x["period"] == "last_30_days"), None),
                "issue_count": issues.get("issue_count"),
                "asset_counts": audit.get("summary", {}).get("asset_counts"),
            },
            "highlights": {
                "issues": issues.get("issues", [])[:5],
                "anomalies": audit.get("details", {}).get("anomalies", [])[:5],
            },
            "preview": False,
        }

    def get_campaign_structure(provider: str, account_id: str, limit_campaigns: int = 20, limit_adsets_per_campaign: int = 20, limit_ads_per_adset: int = 20) -> dict:
        _meta_only(provider)
        validate_provider_account(registry, policy_manager, provider, account_id)
        provider_client = registry.get_provider(provider)
        campaigns = provider_client.list_account_objects(account_id, "campaign", limit=limit_campaigns)["rows"]
        adsets = provider_client.list_account_objects(account_id, "adset", limit=500)["rows"]
        ads = provider_client.list_account_objects(account_id, "ad", limit=1000)["rows"]
        adsets_by_campaign: dict[str, list[dict]] = {}
        for adset in adsets:
            adsets_by_campaign.setdefault(str(adset.get("campaign_id")), []).append(adset)
        ads_by_adset: dict[str, list[dict]] = {}
        for ad in ads:
            ads_by_adset.setdefault(str(ad.get("adset_id")), []).append(ad)
        rows = []
        for campaign in campaigns:
            campaign_adsets = adsets_by_campaign.get(str(campaign.get("id")), [])[:limit_adsets_per_campaign]
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
                                for ad in ads_by_adset.get(str(adset.get("id")), [])[:limit_ads_per_adset]
                            ],
                        }
                        for adset in campaign_adsets
                    ],
                }
            )
        return {"provider": provider, "account_id": account_id, "rows": rows, "preview": False}

    def get_policy_issues(provider: str, account_id: str, limit: int = 50) -> dict:
        _meta_only(provider)
        validate_provider_account(registry, policy_manager, provider, account_id)
        issues = registry.get_provider(provider).get_delivery_issues(account_id, limit * 3)
        rows = [
            issue
            for issue in issues.get("issues", [])
            if issue.get("review_feedback") or issue.get("issues_info") or str(issue.get("status", "")).upper() in {"DISAPPROVED", "WITH_ISSUES"}
        ][:limit]
        return {
            "provider": provider,
            "account_id": account_id,
            "rows": rows,
            "row_count": len(rows),
            "preview": False,
        }

    def get_conversion_health(provider: str, account_id: str) -> dict:
        _meta_only(provider)
        validate_provider_account(registry, policy_manager, provider, account_id)
        provider_client = registry.get_provider(provider)
        assets = provider_client.get_connected_assets(account_id)
        pixels = assets.get("assets", {}).get("pixels", [])
        conversions = assets.get("assets", {}).get("custom_conversions", [])
        pixel_rows = [
            {
                "pixel_id": row.get("id"),
                "pixel_name": row.get("name"),
                "creation_time": row.get("creation_time"),
                "last_fired_time": row.get("last_fired_time"),
            }
            for row in pixels
        ]
        conversion_rows = [
            {
                "conversion_id": row.get("id"),
                "conversion_name": row.get("name"),
                "event_source_type": row.get("event_source_type"),
                "event_source_id": row.get("event_source_id"),
                "first_fired_time": row.get("first_fired_time"),
                "last_fired_time": row.get("last_fired_time"),
                "is_archived": row.get("is_archived"),
                "is_unavailable": row.get("is_unavailable"),
            }
            for row in conversions
        ]
        return {
            "provider": provider,
            "account_id": account_id,
            "pixels": pixel_rows,
            "custom_conversions": conversion_rows,
            "summary": {
                "pixel_count": len(pixel_rows),
                "custom_conversion_count": len(conversion_rows),
                "pixels_with_recent_fire_time": sum(1 for row in pixel_rows if row.get("last_fired_time")),
                "custom_conversions_with_recent_fire_time": sum(1 for row in conversion_rows if row.get("last_fired_time")),
            },
            "preview": False,
        }

    def get_asset_health(provider: str, account_id: str) -> dict:
        _meta_only(provider)
        validate_provider_account(registry, policy_manager, provider, account_id)
        provider_client = registry.get_provider(provider)
        assets = provider_client.get_connected_assets(account_id)
        lead_forms = provider_client.list_lead_forms(account_id, None, 50)
        pages = assets.get("assets", {}).get("pages", [])
        page_rows = [
            {
                "id": page.get("id"),
                "name": page.get("name"),
                "link": page.get("link"),
                "category": page.get("category"),
            }
            for page in pages
        ]
        return {
            "provider": provider,
            "account_id": account_id,
            "summary": {
                **assets.get("summary", {}),
                "lead_forms": lead_forms.get("row_count", 0),
            },
            "pages": page_rows,
            "instagram_accounts": assets.get("assets", {}).get("instagram_accounts", []),
            "pixels": assets.get("assets", {}).get("pixels", []),
            "custom_conversions": assets.get("assets", {}).get("custom_conversions", []),
            "lead_forms": lead_forms.get("rows", []),
            "preview": False,
        }

    def list_creative_assets(provider: str, account_id: str, limit: int = 50) -> dict:
        _meta_only(provider)
        validate_provider_account(registry, policy_manager, provider, account_id)
        provider_client = registry.get_provider(provider)
        creatives = provider_client.list_account_objects(account_id, "creative", limit=limit)
        images = provider_client.list_account_objects(account_id, "ad_image", limit=limit)
        videos = provider_client.list_account_objects(account_id, "ad_video", limit=limit)
        return {
            "provider": provider,
            "account_id": account_id,
            "creatives": creatives.get("rows", []),
            "images": images.get("rows", []),
            "videos": videos.get("rows", []),
            "summary": {
                "creatives": creatives.get("row_count", 0),
                "images": images.get("row_count", 0),
                "videos": videos.get("row_count", 0),
            },
            "preview": False,
        }

    def get_top_performers(
        provider: str,
        account_id: str,
        start_date: str,
        end_date: str,
        entity_level: str = "campaign",
        metric: str = "cost_per_result",
        limit: int = 5,
    ) -> dict:
        _meta_only(provider)
        validate_provider_account(registry, policy_manager, provider, account_id)
        policy_manager.validate_report_range(start_date, end_date)
        return registry.get_provider(provider).rank_top_entities(account_id, entity_level, start_date, end_date, metric, limit)

    def get_no_result_entities(
        provider: str,
        account_id: str,
        start_date: str,
        end_date: str,
        entity_level: str = "ad",
        min_spend: float = 20.0,
        limit: int = 20,
    ) -> dict:
        _meta_only(provider)
        validate_provider_account(registry, policy_manager, provider, account_id)
        policy_manager.validate_report_range(start_date, end_date)
        ranked = registry.get_provider(provider).rank_top_entities(account_id, entity_level, start_date, end_date, "spend", 300)
        rows = [row for row in ranked["rows"] if row.get("conversions", 0) == 0 and row.get("spend", 0) >= min_spend]
        rows.sort(key=lambda row: row.get("spend", 0), reverse=True)
        return {
            "provider": provider,
            "account_id": account_id,
            "entity_level": entity_level,
            "rows": rows[:limit],
            "preview": False,
        }

    def get_launch_checklist(provider: str, account_id: str, end_date: str) -> dict:
        _meta_only(provider)
        validate_provider_account(registry, policy_manager, provider, account_id)
        assets = registry.get_provider(provider).get_connected_assets(account_id)
        billing = registry.get_provider(provider).get_billing_summary(account_id)
        issues = registry.get_provider(provider).get_delivery_issues(account_id, 20)
        checklist = [
            {"item": "pages_connected", "ok": assets.get("summary", {}).get("pages", 0) > 0},
            {"item": "instagram_connected", "ok": assets.get("summary", {}).get("instagram_accounts", 0) > 0},
            {"item": "pixel_connected", "ok": assets.get("summary", {}).get("pixels", 0) > 0},
            {"item": "custom_conversions_present", "ok": assets.get("summary", {}).get("custom_conversions", 0) > 0},
            {"item": "billing_has_no_balance_due", "ok": (billing.get("billing", {}).get("balance_due") or 0) == 0},
            {"item": "no_delivery_issues", "ok": issues.get("issue_count", 0) == 0},
        ]
        return {
            "provider": provider,
            "account_id": account_id,
            "checklist": checklist,
            "issues": issues.get("issues", [])[:10],
            "preview": False,
        }

    def clone_campaign_preview(provider: str, account_id: str, source_campaign_id: str, new_name: str | None = None, daily_budget: float | None = None, lifetime_budget: float | None = None, status: str = "PAUSED") -> dict:
        payload = {
            "name": new_name,
            "status": status,
            "daily_budget": daily_budget,
            "lifetime_budget": lifetime_budget,
            "source_campaign_id": source_campaign_id,
            "clone_options": {"include_adsets": True, "include_ads": True},
        }
        return _preview("create", provider, account_id, "campaign", payload)

    def clone_adset_preview(provider: str, account_id: str, source_adset_id: str, campaign_id: str | None = None, new_name: str | None = None, daily_budget: float | None = None, status: str = "PAUSED") -> dict:
        payload = {
            "name": new_name,
            "campaign_id": campaign_id,
            "status": status,
            "daily_budget": daily_budget,
            "source_adset_id": source_adset_id,
            "clone_options": {"include_ads": True},
        }
        return _preview("create", provider, account_id, "adset", payload)

    def clone_ad_preview(provider: str, account_id: str, source_ad_id: str, adset_id: str | None = None, new_name: str | None = None, status: str = "PAUSED") -> dict:
        payload = {
            "name": new_name,
            "adset_id": adset_id,
            "status": status,
            "source_ad_id": source_ad_id,
            "clone_options": {"reuse_creative": True},
        }
        return _preview("create", provider, account_id, "ad", payload)

    def update_campaign_budget_preview(provider: str, account_id: str, campaign_id: str, daily_budget: float | None = None, lifetime_budget: float | None = None, spend_cap: float | None = None, budget_delta_percent: float | None = None) -> dict:
        payload = {
            "id": campaign_id,
            "daily_budget": daily_budget,
            "lifetime_budget": lifetime_budget,
            "spend_cap": spend_cap,
            "budget_delta_percent": budget_delta_percent,
        }
        return _preview("update", provider, account_id, "campaign", payload)

    def update_adset_budget_preview(provider: str, account_id: str, adset_id: str, daily_budget: float | None = None, lifetime_budget: float | None = None, budget_delta_percent: float | None = None) -> dict:
        payload = {
            "id": adset_id,
            "daily_budget": daily_budget,
            "lifetime_budget": lifetime_budget,
            "budget_delta_percent": budget_delta_percent,
        }
        return _preview("update", provider, account_id, "adset", payload)

    def scale_best_campaigns_preview(provider: str, account_id: str, campaign_ids: list[str], increase_percent: float = 20.0) -> dict:
        payload = {
            "campaign_ids": campaign_ids,
            "budget_delta_percent": increase_percent,
            "bulk_count": len(campaign_ids),
            "extra_fields": {"operation": "scale_best_campaigns"},
        }
        return _preview("update", provider, account_id, "campaign", payload)

    def pause_entities_preview(provider: str, account_id: str, object_type: str, ids: list[str]) -> dict:
        payload = {
            "ids": ids,
            "status": "PAUSED",
            "bulk_count": len(ids),
            "extra_fields": {"operation": "bulk_pause"},
        }
        return _preview("update", provider, account_id, object_type, payload)

    def enable_entities_preview(provider: str, account_id: str, object_type: str, ids: list[str]) -> dict:
        payload = {
            "ids": ids,
            "status": "ACTIVE",
            "bulk_count": len(ids),
            "extra_fields": {"operation": "bulk_enable"},
        }
        return _preview("update", provider, account_id, object_type, payload)

    def update_placements_preview(provider: str, account_id: str, adset_id: str, publisher_platforms: list[str], platform_positions: dict | None = None) -> dict:
        payload = {
            "id": adset_id,
            "placements": {
                "publisher_platforms": publisher_platforms,
                "platform_positions": platform_positions or {},
            },
        }
        return _preview("update", provider, account_id, "adset", payload)

    def update_targeting_preview(provider: str, account_id: str, adset_id: str, targeting: dict) -> dict:
        payload = {"id": adset_id, "targeting": targeting}
        return _preview("update", provider, account_id, "adset", payload)

    def replace_ad_creative_preview(provider: str, account_id: str, ad_id: str, creative_id: str | None = None, creative: dict | None = None, url_tags: str | None = None) -> dict:
        payload = {
            "id": ad_id,
            "creative_id": creative_id,
            "creative": creative or {},
            "url_tags": url_tags,
        }
        return _preview("update", provider, account_id, "ad", payload)

    def create_whatsapp_traffic_campaign_preview(provider: str, account_id: str, name: str, page_id: str, whatsapp_number: str, daily_budget: float, targeting: dict, placements: dict | None = None, creative: dict | None = None) -> dict:
        payload = {
            "name": name,
            "objective": "OUTCOME_TRAFFIC",
            "status": "PAUSED",
            "daily_budget": daily_budget,
            "targeting": targeting,
            "promoted_object": {"page_id": page_id, "whatsapp_number": whatsapp_number},
            "extra_fields": {
                "destination_type": "WHATSAPP",
                "placements": placements or {},
                "creative": creative or {},
            },
        }
        return _preview("create", provider, account_id, "campaign", payload)

    def create_engagement_campaign_preview(provider: str, account_id: str, name: str, daily_budget: float | None = None, targeting: dict | None = None, promoted_object: dict | None = None) -> dict:
        payload = {
            "name": name,
            "objective": "OUTCOME_ENGAGEMENT",
            "status": "PAUSED",
            "daily_budget": daily_budget,
            "targeting": targeting or {},
            "promoted_object": promoted_object or {},
        }
        return _preview("create", provider, account_id, "campaign", payload)

    def create_lead_campaign_preview(provider: str, account_id: str, name: str, daily_budget: float | None = None, targeting: dict | None = None, promoted_object: dict | None = None) -> dict:
        payload = {
            "name": name,
            "objective": "OUTCOME_LEADS",
            "status": "PAUSED",
            "daily_budget": daily_budget,
            "targeting": targeting or {},
            "promoted_object": promoted_object or {},
        }
        return _preview("create", provider, account_id, "campaign", payload)

    def create_ab_test_ads_preview(provider: str, account_id: str, adset_id: str, ad_variants: list[dict]) -> dict:
        payload = {
            "adset_id": adset_id,
            "variants": ad_variants,
            "bulk_count": len(ad_variants),
            "extra_fields": {"operation": "ab_test_ads"},
        }
        return _preview("create", provider, account_id, "ad", payload)

    def update_entity_status_preview(provider: str, account_id: str, object_type: str, entity_id: str, status: str) -> dict:
        payload = {"id": entity_id, "status": status}
        return _preview("update", provider, account_id, object_type, payload)

    def create_ad_in_existing_adset_preview(provider: str, account_id: str, adset_id: str, name: str, creative: dict, status: str = "PAUSED", tracking_specs: list | None = None) -> dict:
        payload = {
            "name": name,
            "adset_id": adset_id,
            "creative": creative,
            "status": status,
            "tracking_specs": tracking_specs or [],
        }
        return _preview("create", provider, account_id, "ad", payload)

    def create_adset_in_campaign_preview(
        provider: str,
        account_id: str,
        campaign_id: str,
        name: str,
        daily_budget: float | None = None,
        lifetime_budget: float | None = None,
        billing_event: str | None = None,
        optimization_goal: str | None = None,
        bid_strategy: str | None = None,
        targeting: dict | None = None,
        promoted_object: dict | None = None,
        status: str = "PAUSED",
    ) -> dict:
        payload = {
            "campaign_id": campaign_id,
            "name": name,
            "daily_budget": daily_budget,
            "lifetime_budget": lifetime_budget,
            "billing_event": billing_event,
            "optimization_goal": optimization_goal,
            "bid_strategy": bid_strategy,
            "targeting": targeting or {},
            "promoted_object": promoted_object or {},
            "status": status,
        }
        return _preview("create", provider, account_id, "adset", payload)

    def create_creative_preview(provider: str, account_id: str, name: str, creative_payload: dict) -> dict:
        payload = {"name": name, "extra_fields": creative_payload}
        return _preview("create", provider, account_id, "creative", payload)

    def create_audience_variant_preview(provider: str, account_id: str, name: str, subtype: str, base_rule: dict | None = None, lookalike_spec: dict | None = None, retention_days: int | None = None) -> dict:
        payload = {
            "name": name,
            "subtype": subtype,
            "rule": base_rule or {},
            "lookalike_spec": lookalike_spec or {},
            "retention_days": retention_days,
        }
        return _preview("create", provider, account_id, "audience", payload)

    def duplicate_campaign_with_geo_preview(provider: str, account_id: str, source_campaign_id: str, countries: list[str], regions: list[str] | None = None, new_name: str | None = None) -> dict:
        payload = {
            "name": new_name,
            "source_campaign_id": source_campaign_id,
            "clone_options": {
                "include_adsets": True,
                "include_ads": True,
                "targeting_override": {
                    "geo_locations": {
                        "countries": countries,
                        "regions": regions or [],
                    }
                },
            },
        }
        return _preview("create", provider, account_id, "campaign", payload)

    def duplicate_campaign_with_audience_preview(provider: str, account_id: str, source_campaign_id: str, targeting: dict, new_name: str | None = None) -> dict:
        payload = {
            "name": new_name,
            "source_campaign_id": source_campaign_id,
            "clone_options": {
                "include_adsets": True,
                "include_ads": True,
                "targeting_override": targeting,
            },
        }
        return _preview("create", provider, account_id, "campaign", payload)

    def rebalance_budget_to_end_of_month_preview(provider: str, account_id: str, entity_id: str, object_type: str, remaining_budget: float, reference_date: str | None = None) -> dict:
        ref = date.fromisoformat(reference_date) if reference_date else date.today()
        days_left = max(monthrange(ref.year, ref.month)[1] - ref.day + 1, 1)
        new_daily_budget = round(remaining_budget / days_left, 2)
        payload = {
            "id": entity_id,
            "daily_budget": new_daily_budget,
            "extra_fields": {
                "remaining_budget": remaining_budget,
                "days_left_in_month": days_left,
                "operation": "rebalance_to_month_end",
            },
        }
        return _preview("update", provider, account_id, object_type, payload)

    def pause_underperformers_preview(
        provider: str,
        account_id: str,
        start_date: str,
        end_date: str,
        entity_level: str = "ad",
        min_spend: float = 20.0,
        max_ctr: float = 0.8,
        limit: int = 25,
    ) -> dict:
        _meta_only(provider)
        validate_provider_account(registry, policy_manager, provider, account_id)
        policy_manager.validate_report_range(start_date, end_date)
        ranked = registry.get_provider(provider).rank_top_entities(account_id, entity_level, start_date, end_date, "spend", 300)
        candidates = [row["entity_id"] for row in ranked["rows"] if row.get("spend", 0) >= min_spend and row.get("conversions", 0) == 0 and row.get("ctr", 0) <= max_ctr][:limit]
        payload = {
            "ids": candidates,
            "status": "PAUSED",
            "bulk_count": len(candidates),
            "extra_fields": {
                "selection_rule": {
                    "min_spend": min_spend,
                    "max_ctr": max_ctr,
                    "requires_zero_conversions": True,
                }
            },
        }
        return _preview("update", provider, account_id, entity_level, payload)

    def archive_entities_preview(provider: str, account_id: str, object_type: str, ids: list[str]) -> dict:
        payload = {
            "ids": ids,
            "bulk_count": len(ids),
            "extra_fields": {"operation": "bulk_archive"},
        }
        return _preview("delete_or_archive", provider, account_id, object_type, payload)

    def scale_winners_by_rule_preview(
        provider: str,
        account_id: str,
        start_date: str,
        end_date: str,
        entity_level: str = "campaign",
        increase_percent: float = 20.0,
        max_cost_per_result: float = 20.0,
        limit: int = 10,
    ) -> dict:
        _meta_only(provider)
        validate_provider_account(registry, policy_manager, provider, account_id)
        policy_manager.validate_report_range(start_date, end_date)
        ranked = registry.get_provider(provider).rank_top_entities(account_id, entity_level, start_date, end_date, "cost_per_result", 300)
        candidates = [
            row["entity_id"]
            for row in ranked["rows"]
            if row.get("conversions", 0) > 0 and 0 < row.get("cost_per_result", 0) <= max_cost_per_result
        ][:limit]
        payload = {
            "ids": candidates,
            "budget_delta_percent": increase_percent,
            "bulk_count": len(candidates),
            "extra_fields": {
                "selection_rule": {
                    "max_cost_per_result": max_cost_per_result,
                    "requires_conversions": True,
                }
            },
        }
        return _preview("update", provider, account_id, entity_level, payload)

    return {
        "get_status_summary": get_status_summary,
        "get_breakdown_preset": get_breakdown_preset,
        "find_wasting_spend": find_wasting_spend,
        "compare_creatives": compare_creatives,
        "get_executive_summary": get_executive_summary,
        "get_campaign_structure": get_campaign_structure,
        "get_policy_issues": get_policy_issues,
        "get_conversion_health": get_conversion_health,
        "get_asset_health": get_asset_health,
        "list_creative_assets": list_creative_assets,
        "get_top_performers": get_top_performers,
        "get_no_result_entities": get_no_result_entities,
        "get_launch_checklist": get_launch_checklist,
        "clone_campaign_preview": clone_campaign_preview,
        "clone_adset_preview": clone_adset_preview,
        "clone_ad_preview": clone_ad_preview,
        "update_campaign_budget_preview": update_campaign_budget_preview,
        "update_adset_budget_preview": update_adset_budget_preview,
        "scale_best_campaigns_preview": scale_best_campaigns_preview,
        "pause_entities_preview": pause_entities_preview,
        "enable_entities_preview": enable_entities_preview,
        "update_placements_preview": update_placements_preview,
        "update_targeting_preview": update_targeting_preview,
        "replace_ad_creative_preview": replace_ad_creative_preview,
        "create_whatsapp_traffic_campaign_preview": create_whatsapp_traffic_campaign_preview,
        "create_engagement_campaign_preview": create_engagement_campaign_preview,
        "create_lead_campaign_preview": create_lead_campaign_preview,
        "create_ab_test_ads_preview": create_ab_test_ads_preview,
        "update_entity_status_preview": update_entity_status_preview,
        "create_ad_in_existing_adset_preview": create_ad_in_existing_adset_preview,
        "create_adset_in_campaign_preview": create_adset_in_campaign_preview,
        "create_creative_preview": create_creative_preview,
        "create_audience_variant_preview": create_audience_variant_preview,
        "duplicate_campaign_with_geo_preview": duplicate_campaign_with_geo_preview,
        "duplicate_campaign_with_audience_preview": duplicate_campaign_with_audience_preview,
        "rebalance_budget_to_end_of_month_preview": rebalance_budget_to_end_of_month_preview,
        "pause_underperformers_preview": pause_underperformers_preview,
        "scale_winners_by_rule_preview": scale_winners_by_rule_preview,
        "archive_entities_preview": archive_entities_preview,
    }

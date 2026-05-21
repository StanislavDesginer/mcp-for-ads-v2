from __future__ import annotations

import os
import re
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import yaml

from ad_mcp.core.config_loader import (
    load_provider_config,
    load_provider_from_connections,
    load_safety_policy,
)
from ad_mcp.core.models import ObjectMutationResponse
from ad_mcp.core.policy import PolicyManager
from ad_mcp.core.preview_manager import PreviewManager
from ad_mcp.providers.meta_ads.client import MetaAdsProvider
from ad_mcp.settings import Settings


_ENV_REF_RE = re.compile(r"\$\{([A-Z0-9_]+)(?::-([^}]*))?\}")


class MetaDashboardService:
    def __init__(self) -> None:
        settings = Settings()
        self._settings = settings
        self._policy_manager = PolicyManager(load_safety_policy(settings.policy_config_path))
        provider_config = load_provider_from_connections(settings.connections_config_path, "meta_ads")
        if not provider_config.get("accounts"):
            provider_config = load_provider_config(settings.project_root / "config/providers", "meta_ads")
        self._provider_config = provider_config
        self._provider = MetaAdsProvider(config=provider_config)
        self._preview_manager = PreviewManager()

    def _has_placeholder_credentials(self, account: dict[str, Any]) -> bool:
        markers = ("YOUR_", "<", "EXAMPLE", "CHANGE_ME", "PLACEHOLDER")
        token = str(account.get("access_token", "") or "").strip()
        app_id = str(account.get("app_id", "") or "").strip()
        app_secret = str(account.get("app_secret", "") or "").strip()
        if not token or not app_secret:
            return True
        values = [token, app_secret]
        if app_id:
            values.append(app_id)
        joined = " ".join(values).upper()
        return any(marker in joined for marker in markers)

    def _ensure_account_is_usable(self, account_id: str) -> None:
        account = self._provider.get_account_config(account_id)
        if not account:
            raise ValueError(
                "Аккаунт не найден в конфиге Meta. Проверьте account_id в ads_config.yaml "
                "или config/providers/meta_ads.yaml."
            )
        if self._has_placeholder_credentials(account):
            raise ValueError(
                "Найдены шаблонные креды Meta (placeholder-значения). "
                "Проверьте app_secret и access_token в локальных конфигурациях."
            )

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
        self._ensure_account_is_usable(resolved_account_id)
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
        self._ensure_account_is_usable(resolved_account_id)
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
        self._ensure_account_is_usable(resolved_account_id)
        return self._provider.get_delivery_issues(resolved_account_id, limit)

    def connected_assets(self, account_id: str | None = None) -> dict[str, Any]:
        resolved_account_id = self._resolve_account_id(account_id)
        self._ensure_account_is_usable(resolved_account_id)
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
        self._ensure_account_is_usable(resolved_account_id)
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
        self._ensure_account_is_usable(resolved_account_id)
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
        self._ensure_account_is_usable(resolved_account_id)
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
        self._ensure_account_is_usable(resolved_account_id)
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
        self._ensure_account_is_usable(resolved_account_id)
        payload = {
            "ids": ids,
            "status": "PAUSED",
            "bulk_count": len(ids),
            "extra_fields": {"operation": "bulk_pause"},
        }
        return self._build_preview_response("update", resolved_account_id, "ad", payload)

    def _mask_secret(self, value: Any, head: int = 6, tail: int = 4) -> str:
        text = str(value or "")
        if not text:
            return "(пусто)"
        if len(text) <= head + tail:
            return "*" * len(text)
        return f"{text[:head]}...{text[-tail:]}"

    def _read_yaml_without_expansion(self, path: Path) -> dict[str, Any]:
        if not path.exists():
            return {}
        try:
            with path.open("r", encoding="utf-8") as handle:
                return yaml.safe_load(handle) or {}
        except Exception:
            return {}

    def _connections_paths(self) -> tuple[Path, Path]:
        primary = self._settings.connections_config_path
        example = primary.with_name(f"{primary.stem}.example{primary.suffix}")
        return primary, example

    def _load_runtime_meta_config(self) -> dict[str, Any]:
        provider_config = load_provider_from_connections(self._settings.connections_config_path, "meta_ads")
        if provider_config.get("accounts"):
            return provider_config
        return load_provider_config(self._settings.project_root / "config/providers", "meta_ads")

    def _load_raw_meta_config(self) -> tuple[dict[str, Any], str, Path]:
        connections_primary, connections_example = self._connections_paths()
        source_kind = "connections_primary"
        source_path = connections_primary

        raw_connections = self._read_yaml_without_expansion(connections_primary)
        if not raw_connections:
            raw_connections = self._read_yaml_without_expansion(connections_example)
            source_kind = "connections_example"
            source_path = connections_example

        provider = (raw_connections.get("providers") or {}).get("meta_ads") or {}
        if provider.get("accounts"):
            return provider, source_kind, source_path

        provider_primary = self._settings.project_root / "config/providers/meta_ads.yaml"
        provider_example = self._settings.project_root / "config/providers/meta_ads.example.yaml"
        raw_provider = self._read_yaml_without_expansion(provider_primary)
        source_kind = "provider_primary"
        source_path = provider_primary

        if not raw_provider:
            raw_provider = self._read_yaml_without_expansion(provider_example)
            source_kind = "provider_example"
            source_path = provider_example

        return raw_provider, source_kind, source_path

    def _env_reference_status(self, raw_value: Any) -> dict[str, Any]:
        if not isinstance(raw_value, str):
            return {"has_env_ref": False, "resolved": True, "vars": []}

        refs = [match.group(1) for match in _ENV_REF_RE.finditer(raw_value)]
        if not refs:
            return {"has_env_ref": False, "resolved": True, "vars": []}

        missing = [item for item in refs if os.getenv(item) in (None, "")]
        return {
            "has_env_ref": True,
            "resolved": not missing,
            "vars": refs,
            "missing_vars": missing,
        }

    def config_diagnostics(self) -> dict[str, Any]:
        env_path = self._settings.project_root / ".env"
        connections_primary, connections_example = self._connections_paths()

        runtime_provider = self._load_runtime_meta_config()
        raw_provider, raw_source_kind, raw_source_path = self._load_raw_meta_config()
        runtime_accounts = runtime_provider.get("accounts") or []
        raw_accounts = raw_provider.get("accounts") or []

        accounts: list[dict[str, Any]] = []
        for index, runtime_account in enumerate(runtime_accounts):
            raw_account = raw_accounts[index] if index < len(raw_accounts) else {}
            access_token = str(runtime_account.get("access_token", "") or "")
            app_secret = str(runtime_account.get("app_secret", "") or "")
            account_id = str(runtime_account.get("account_id", "") or "")
            access_ref = self._env_reference_status(raw_account.get("access_token"))
            secret_ref = self._env_reference_status(raw_account.get("app_secret"))

            accounts.append(
                {
                    "name": runtime_account.get("name") or f"Account #{index + 1}",
                    "account_id": account_id,
                    "status": runtime_account.get("status") or "unknown",
                    "app_id": str(runtime_account.get("app_id", "") or ""),
                    "api_version": str(runtime_account.get("api_version", "") or ""),
                    "access_token": {
                        "present": bool(access_token),
                        "masked": self._mask_secret(access_token),
                        "looks_placeholder": self._has_placeholder_credentials({"access_token": access_token, "app_secret": "x"}),
                        "env_ref": access_ref,
                    },
                    "app_secret": {
                        "present": bool(app_secret),
                        "masked": self._mask_secret(app_secret),
                        "looks_placeholder": self._has_placeholder_credentials({"access_token": "x", "app_secret": app_secret}),
                        "env_ref": secret_ref,
                    },
                }
            )

        runtime_account_ids = [str(item.get("account_id", "") or "") for item in runtime_accounts]
        unresolved_env_vars = sorted(
            {
                missing_var
                for account in accounts
                for secret_key in ("access_token", "app_secret")
                for missing_var in account[secret_key]["env_ref"].get("missing_vars", [])
            }
        )

        provider_loaded = bool(runtime_accounts)
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "provider": "meta_ads",
            "provider_loaded": provider_loaded,
            "project_root": str(self._settings.project_root),
            "env": {
                "path": str(env_path),
                "exists": env_path.exists(),
                "loaded_hint": env_path.exists(),
            },
            "connections": {
                "primary_path": str(connections_primary),
                "primary_exists": connections_primary.exists(),
                "example_path": str(connections_example),
                "example_exists": connections_example.exists(),
                "runtime_source": str(self._settings.connections_config_path if connections_primary.exists() else connections_example),
                "raw_source_kind": raw_source_kind,
                "raw_source_path": str(raw_source_path),
            },
            "runtime": {
                "accounts_total": len(runtime_accounts),
                "runtime_account_ids": runtime_account_ids,
                "accounts": accounts,
            },
            "env_substitution": {
                "all_resolved": not unresolved_env_vars,
                "missing_vars": unresolved_env_vars,
            },
        }

    def auth_diagnostics(self) -> dict[str, Any]:
        runtime_provider = self._load_runtime_meta_config()
        self._provider_config = runtime_provider
        self._provider = MetaAdsProvider(config=runtime_provider)

        accounts = runtime_provider.get("accounts") or []
        checks: list[dict[str, Any]] = []

        for account in accounts:
            account_id = str(account.get("account_id", "") or "")
            name = str(account.get("name", "") or account_id or "Unknown account")
            token = str(account.get("access_token", "") or "")
            secret = str(account.get("app_secret", "") or "")

            check: dict[str, Any] = {
                "name": name,
                "account_id": account_id,
                "access_token_masked": self._mask_secret(token),
                "app_secret_masked": self._mask_secret(secret),
                "token_present": bool(token),
                "app_secret_present": bool(secret),
                "app_id": str(account.get("app_id", "") or ""),
                "auth_ok": False,
                "error": None,
                "account_name_from_meta": None,
                "meta_account_status": None,
            }

            if not token or not secret:
                check["error"] = "Пустой access_token или app_secret в runtime-конфиге"
                checks.append(check)
                continue

            if self._has_placeholder_credentials(account):
                check["error"] = "Обнаружены placeholder-значения в credentials"
                checks.append(check)
                continue

            try:
                summary = self._provider.get_account_summary(account_id, fields=["id", "name", "account_status", "currency"])
                meta = summary.get("data") if isinstance(summary, dict) else {}
                check["auth_ok"] = True
                check["account_name_from_meta"] = meta.get("name") if isinstance(meta, dict) else None
                check["meta_account_status"] = meta.get("account_status") if isinstance(meta, dict) else None
            except Exception as exc:  # noqa: BLE001
                check["error"] = str(exc)

            checks.append(check)

        ok_count = sum(1 for item in checks if item.get("auth_ok"))
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "provider": "meta_ads",
            "accounts_checked": len(checks),
            "auth_ok_count": ok_count,
            "auth_failed_count": len(checks) - ok_count,
            "checks": checks,
        }

    def diagnostics_health(self) -> dict[str, Any]:
        config = self.config_diagnostics()
        auth = self.auth_diagnostics()
        status = "ok" if auth.get("auth_failed_count", 0) == 0 and config.get("provider_loaded") else "degraded"
        return {
            "status": status,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "config": {
                "provider_loaded": config.get("provider_loaded"),
                "accounts_total": config.get("runtime", {}).get("accounts_total", 0),
                "env_exists": config.get("env", {}).get("exists"),
                "connections_primary_exists": config.get("connections", {}).get("primary_exists"),
                "env_substitution_ok": config.get("env_substitution", {}).get("all_resolved"),
                "missing_env_vars": config.get("env_substitution", {}).get("missing_vars", []),
            },
            "auth": {
                "accounts_checked": auth.get("accounts_checked", 0),
                "auth_ok_count": auth.get("auth_ok_count", 0),
                "auth_failed_count": auth.get("auth_failed_count", 0),
            },
        }

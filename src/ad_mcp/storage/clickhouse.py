from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

import httpx

from ad_mcp.settings import Settings


class ClickHousePersistence:
    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or Settings()
        self._schema_ready = False

    @property
    def enabled(self) -> bool:
        return self._settings.clickhouse_enabled

    @property
    def configured(self) -> bool:
        return bool(
            self._settings.clickhouse_host
            and self._settings.clickhouse_port
            and self._settings.clickhouse_database
        )

    @property
    def base_url(self) -> str:
        scheme = "https" if self._settings.clickhouse_secure else "http"
        return f"{scheme}://{self._settings.clickhouse_host}:{self._settings.clickhouse_port}"

    def diagnostics(self) -> dict[str, Any]:
        diagnostics = {
            "enabled": self.enabled,
            "configured": self.configured,
            "host": self._settings.clickhouse_host,
            "port": self._settings.clickhouse_port,
            "database": self._settings.clickhouse_database,
            "user": self._settings.clickhouse_user,
            "secure": self._settings.clickhouse_secure,
            "timeout_seconds": self._settings.clickhouse_timeout_seconds,
            "reachable": False,
            "schema_ready": False,
            "existing_tables": [],
            "last_error": None,
        }
        if not self.enabled:
            diagnostics["last_error"] = "ClickHouse persistence выключен в настройках."
            return diagnostics
        if not self.configured:
            diagnostics["last_error"] = "ClickHouse persistence включен, но параметры подключения не заполнены."
            return diagnostics

        try:
            self._execute_json("SELECT 1 AS ok FORMAT JSON")
            diagnostics["reachable"] = True
            diagnostics["existing_tables"] = self._existing_tables()
            diagnostics["schema_ready"] = all(
                table in diagnostics["existing_tables"]
                for table in (
                    "meta_account_daily_fact",
                    "meta_entity_daily_fact",
                    "meta_delivery_issue_log",
                    "meta_preview_action_log",
                )
            )
        except Exception as exc:  # noqa: BLE001
            diagnostics["last_error"] = str(exc)
        return diagnostics

    def ensure_schema(self) -> dict[str, Any]:
        if not self.enabled:
            return {"status": "skipped", "reason": "disabled"}
        if not self.configured:
            return {"status": "failed", "reason": "not_configured"}
        if self._schema_ready:
            return {"status": "ok", "created": False}

        self._execute(
            f"CREATE DATABASE IF NOT EXISTS {self._settings.clickhouse_database}"
        )
        for statement in self._schema_statements():
            self._execute(statement)
        self._schema_ready = True
        return {"status": "ok", "created": True}

    def sync_workspace(self, workspace: dict[str, Any]) -> dict[str, Any]:
        if not self.enabled:
            return {
                "status": "skipped",
                "reason": "disabled",
                "tables": {},
            }
        if not self.configured:
            return {
                "status": "failed",
                "reason": "not_configured",
                "tables": {},
            }

        try:
            self.ensure_schema()
            account_rows = self._build_account_rows(workspace)
            entity_rows = self._build_entity_rows(workspace)
            issue_rows = self._build_issue_rows(workspace)

            account_inserted = self._insert_json_rows("meta_account_daily_fact", account_rows)
            entity_inserted = self._insert_json_rows("meta_entity_daily_fact", entity_rows)
            issue_inserted = self._insert_json_rows("meta_delivery_issue_log", issue_rows)

            return {
                "status": "ok",
                "synced_at": datetime.now(timezone.utc).isoformat(),
                "tables": {
                    "meta_account_daily_fact": account_inserted,
                    "meta_entity_daily_fact": entity_inserted,
                    "meta_delivery_issue_log": issue_inserted,
                },
            }
        except Exception as exc:  # noqa: BLE001
            return {
                "status": "failed",
                "synced_at": datetime.now(timezone.utc).isoformat(),
                "reason": str(exc),
                "tables": {},
            }

    def log_preview_action(self, preview: dict[str, Any]) -> dict[str, Any]:
        if not self.enabled:
            return {"status": "skipped", "reason": "disabled"}
        if not self.configured:
            return {"status": "failed", "reason": "not_configured"}

        try:
            self.ensure_schema()
            row = {
                "created_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
                "account_id": str(preview.get("account_id", "") or ""),
                "object_type": str(preview.get("object_type", "") or ""),
                "action": str(preview.get("action", "") or ""),
                "preview_token": str(preview.get("preview_token", "") or ""),
                "risk_flags": [str(item) for item in preview.get("risk_flags", []) or []],
                "diff_json": json.dumps(preview.get("diff", {}), ensure_ascii=False),
                "provider_payload_json": json.dumps(preview.get("provider_payload", {}), ensure_ascii=False),
            }
            inserted = self._insert_json_rows("meta_preview_action_log", [row])
            return {"status": "ok", "inserted": inserted}
        except Exception as exc:  # noqa: BLE001
            return {"status": "failed", "reason": str(exc)}

    def _execute(self, query: str) -> str:
        response = httpx.post(
            f"{self.base_url}/",
            params={"database": self._settings.clickhouse_database, "query": query},
            auth=(self._settings.clickhouse_user, self._settings.clickhouse_password),
            timeout=self._settings.clickhouse_timeout_seconds,
        )
        response.raise_for_status()
        return response.text

    def _execute_json(self, query: str) -> dict[str, Any]:
        payload = self._execute(query)
        return json.loads(payload or "{}")

    def _insert_json_rows(self, table: str, rows: list[dict[str, Any]]) -> int:
        if not rows:
            return 0
        body = "\n".join(json.dumps(row, ensure_ascii=False) for row in rows).encode("utf-8")
        response = httpx.post(
            f"{self.base_url}/",
            params={
                "database": self._settings.clickhouse_database,
                "query": f"INSERT INTO {table} FORMAT JSONEachRow",
            },
            content=body,
            auth=(self._settings.clickhouse_user, self._settings.clickhouse_password),
            timeout=self._settings.clickhouse_timeout_seconds,
            headers={"Content-Type": "application/x-ndjson; charset=utf-8"},
        )
        response.raise_for_status()
        return len(rows)

    def _existing_tables(self) -> list[str]:
        query = (
            "SELECT name FROM system.tables "
            f"WHERE database = '{self._settings.clickhouse_database}' "
            "ORDER BY name FORMAT JSON"
        )
        payload = self._execute_json(query)
        return [str(item.get("name")) for item in payload.get("data", [])]

    def _schema_statements(self) -> list[str]:
        db = self._settings.clickhouse_database
        return [
            f"""
            CREATE TABLE IF NOT EXISTS {db}.meta_account_daily_fact (
                event_date Date,
                provider LowCardinality(String),
                account_id String,
                account_name String,
                currency LowCardinality(String),
                spend Float64,
                impressions UInt64,
                clicks UInt64,
                conversions Float64,
                ctr Float64,
                cpm Float64,
                balance_due Float64,
                issue_count UInt32,
                synced_at DateTime
            ) ENGINE = MergeTree
            ORDER BY (event_date, provider, account_id)
            """,
            f"""
            CREATE TABLE IF NOT EXISTS {db}.meta_entity_daily_fact (
                event_date Date,
                account_id String,
                entity_level LowCardinality(String),
                entity_id String,
                entity_name String,
                effective_status LowCardinality(String),
                objective LowCardinality(String),
                spend Float64,
                impressions UInt64,
                reach UInt64,
                clicks UInt64,
                conversions Float64,
                ctr Float64,
                cpc Float64,
                cpm Float64,
                cost_per_result Float64,
                frequency_avg Float64,
                synced_at DateTime
            ) ENGINE = MergeTree
            ORDER BY (event_date, account_id, entity_level, entity_id)
            """,
            f"""
            CREATE TABLE IF NOT EXISTS {db}.meta_delivery_issue_log (
                captured_at DateTime,
                account_id String,
                object_type LowCardinality(String),
                entity_id String,
                entity_name String,
                status LowCardinality(String),
                issue_summary String,
                raw_payload String
            ) ENGINE = MergeTree
            ORDER BY (captured_at, account_id, object_type, entity_id)
            """,
            f"""
            CREATE TABLE IF NOT EXISTS {db}.meta_preview_action_log (
                created_at DateTime,
                account_id String,
                object_type LowCardinality(String),
                action LowCardinality(String),
                preview_token String,
                risk_flags Array(String),
                diff_json String,
                provider_payload_json String
            ) ENGINE = MergeTree
            ORDER BY (created_at, account_id, object_type, action)
            """,
        ]

    def _build_account_rows(self, workspace: dict[str, Any]) -> list[dict[str, Any]]:
        header = workspace.get("header", {})
        sections = workspace.get("sections", {})
        overview = sections.get("overview", {})
        spend_periods = (overview.get("spend") or {}).get("periods", [])
        month = next((item for item in spend_periods if item.get("period") == "last_30_days"), {})
        billing = (overview.get("billing") or {}).get("billing", {})
        issues = sections.get("issues", {})
        event_date = str(header.get("end_date") or workspace.get("generated_at") or "")
        synced_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

        return [
            {
                "event_date": event_date,
                "provider": "meta_ads",
                "account_id": str(workspace.get("account_id", "") or ""),
                "account_name": str(header.get("account_name", "") or ""),
                "currency": str(header.get("currency", "") or "USD"),
                "spend": float(month.get("spend", 0) or 0.0),
                "impressions": int(float(month.get("impressions", 0) or 0)),
                "clicks": int(float(month.get("clicks", 0) or 0)),
                "conversions": float(month.get("conversions", 0) or 0.0),
                "ctr": float(month.get("ctr", 0) or 0.0),
                "cpm": 0.0,
                "balance_due": float(billing.get("balance_due", 0) or 0.0),
                "issue_count": int(issues.get("issue_count", 0) or 0),
                "synced_at": synced_at,
            }
        ]

    def _build_entity_rows(self, workspace: dict[str, Any]) -> list[dict[str, Any]]:
        event_date = str(workspace.get("header", {}).get("end_date") or workspace.get("generated_at") or "")
        synced_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        account_id = str(workspace.get("account_id", "") or "")
        rows: list[dict[str, Any]] = []
        seen: set[tuple[str, str]] = set()

        for source_key, payload in (
            ("campaign", (workspace.get("sections", {}).get("performers") or {}).get("rows", [])),
            ("ad", (workspace.get("sections", {}).get("no_result") or {}).get("rows", [])),
        ):
            for row in payload:
                entity_id = str(row.get("entity_id") or "")
                if not entity_id:
                    continue
                dedupe_key = (source_key, entity_id)
                if dedupe_key in seen:
                    continue
                seen.add(dedupe_key)
                rows.append(
                    {
                        "event_date": event_date,
                        "account_id": account_id,
                        "entity_level": source_key,
                        "entity_id": entity_id,
                        "entity_name": str(row.get("entity_name", "") or ""),
                        "effective_status": str(row.get("effective_status", "") or row.get("status", "") or "UNKNOWN"),
                        "objective": str(row.get("objective", "") or ""),
                        "spend": float(row.get("spend", 0) or 0.0),
                        "impressions": int(float(row.get("impressions", 0) or 0)),
                        "reach": int(float(row.get("reach", 0) or 0)),
                        "clicks": int(float(row.get("clicks", 0) or 0)),
                        "conversions": float(row.get("conversions", 0) or 0.0),
                        "ctr": float(row.get("ctr", 0) or 0.0),
                        "cpc": float(row.get("cpc", 0) or 0.0),
                        "cpm": float(row.get("cpm", 0) or 0.0),
                        "cost_per_result": float(row.get("cost_per_result", 0) or 0.0),
                        "frequency_avg": float(row.get("frequency_avg", 0) or 0.0),
                        "synced_at": synced_at,
                    }
                )
        return rows

    def _build_issue_rows(self, workspace: dict[str, Any]) -> list[dict[str, Any]]:
        account_id = str(workspace.get("account_id", "") or "")
        captured_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        rows: list[dict[str, Any]] = []
        for issue in (workspace.get("sections", {}).get("issues") or {}).get("issues", []):
            rows.append(
                {
                    "captured_at": captured_at,
                    "account_id": account_id,
                    "object_type": str(issue.get("object_type", "") or "entity"),
                    "entity_id": str(issue.get("id", "") or ""),
                    "entity_name": str(issue.get("name", "") or ""),
                    "status": str(issue.get("status", "") or "UNKNOWN"),
                    "issue_summary": str(issue.get("review_feedback") or issue.get("issues_info") or ""),
                    "raw_payload": json.dumps(issue, ensure_ascii=False),
                }
            )
        return rows

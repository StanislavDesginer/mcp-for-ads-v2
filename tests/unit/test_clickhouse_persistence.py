from __future__ import annotations

from ad_mcp.settings import Settings
from ad_mcp.storage.clickhouse import ClickHousePersistence


def test_diagnostics_reports_disabled_persistence() -> None:
    persistence = ClickHousePersistence(
        Settings(
            clickhouse_enabled=False,
            clickhouse_host="clickhouse.internal",
            clickhouse_database="ads_ai",
        )
    )

    payload = persistence.diagnostics()

    assert payload["enabled"] is False
    assert payload["configured"] is True
    assert payload["reachable"] is False
    assert payload["last_error"] == "ClickHouse persistence выключен в настройках."


def test_diagnostics_reports_missing_connection_settings() -> None:
    persistence = ClickHousePersistence(
        Settings(
            clickhouse_enabled=True,
            clickhouse_host="",
            clickhouse_database="",
        )
    )

    payload = persistence.diagnostics()

    assert payload["enabled"] is True
    assert payload["configured"] is False
    assert payload["last_error"] == "ClickHouse persistence включен, но параметры подключения не заполнены."


def test_diagnostics_marks_schema_ready_when_all_tables_exist(monkeypatch) -> None:
    persistence = ClickHousePersistence(
        Settings(
            clickhouse_enabled=True,
            clickhouse_host="clickhouse.internal",
            clickhouse_database="ads_ai",
        )
    )

    monkeypatch.setattr(
        persistence,
        "_execute_json",
        lambda query: {"data": [{"ok": 1}]},
    )
    monkeypatch.setattr(
        persistence,
        "_existing_tables",
        lambda: [
            "meta_account_daily_fact",
            "meta_entity_daily_fact",
            "meta_delivery_issue_log",
            "meta_preview_action_log",
        ],
    )

    payload = persistence.diagnostics()

    assert payload["reachable"] is True
    assert payload["schema_ready"] is True
    assert payload["existing_tables"] == [
        "meta_account_daily_fact",
        "meta_entity_daily_fact",
        "meta_delivery_issue_log",
        "meta_preview_action_log",
    ]


def test_ensure_schema_executes_create_database_and_tables(monkeypatch) -> None:
    persistence = ClickHousePersistence(
        Settings(
            clickhouse_enabled=True,
            clickhouse_host="clickhouse.internal",
            clickhouse_database="ads_ai",
        )
    )
    executed: list[str] = []

    monkeypatch.setattr(
        persistence,
        "_execute",
        lambda query: executed.append(query) or "",
    )

    payload = persistence.ensure_schema()

    assert payload == {"status": "ok", "created": True}
    assert executed[0] == "CREATE DATABASE IF NOT EXISTS ads_ai"
    assert len(executed) == 5


def test_sync_workspace_returns_insert_counts(monkeypatch) -> None:
    persistence = ClickHousePersistence(
        Settings(
            clickhouse_enabled=True,
            clickhouse_host="clickhouse.internal",
            clickhouse_database="ads_ai",
        )
    )
    inserted_rows: list[tuple[str, list[dict[str, object]]]] = []

    monkeypatch.setattr(persistence, "ensure_schema", lambda: {"status": "ok", "created": False})
    monkeypatch.setattr(persistence, "_build_account_rows", lambda workspace: [{"row": "account"}])
    monkeypatch.setattr(persistence, "_build_entity_rows", lambda workspace: [{"row": "entity_a"}, {"row": "entity_b"}])
    monkeypatch.setattr(persistence, "_build_issue_rows", lambda workspace: [{"row": "issue"}])

    def _capture_insert(table: str, rows: list[dict[str, object]]) -> int:
        inserted_rows.append((table, rows))
        return len(rows)

    monkeypatch.setattr(persistence, "_insert_json_rows", _capture_insert)

    payload = persistence.sync_workspace({"account_id": "act_123"})

    assert payload["status"] == "ok"
    assert payload["tables"] == {
        "meta_account_daily_fact": 1,
        "meta_entity_daily_fact": 2,
        "meta_delivery_issue_log": 1,
    }
    assert [table for table, _rows in inserted_rows] == [
        "meta_account_daily_fact",
        "meta_entity_daily_fact",
        "meta_delivery_issue_log",
    ]


def test_log_preview_action_serializes_payload(monkeypatch) -> None:
    persistence = ClickHousePersistence(
        Settings(
            clickhouse_enabled=True,
            clickhouse_host="clickhouse.internal",
            clickhouse_database="ads_ai",
        )
    )
    inserted_rows: list[dict[str, object]] = []

    monkeypatch.setattr(persistence, "ensure_schema", lambda: {"status": "ok", "created": False})
    monkeypatch.setattr(
        persistence,
        "_insert_json_rows",
        lambda table, rows: inserted_rows.extend(rows) or len(rows),
    )

    payload = persistence.log_preview_action(
        {
            "account_id": "act_123",
            "object_type": "campaign",
            "action": "update",
            "preview_token": "preview-1",
            "risk_flags": ["budget_change"],
            "diff": {"before": {"daily_budget": 10}, "after": {"daily_budget": 12}},
            "provider_payload": {"body": {"daily_budget": 12}},
        }
    )

    assert payload == {"status": "ok", "inserted": 1}
    assert inserted_rows[0]["account_id"] == "act_123"
    assert inserted_rows[0]["preview_token"] == "preview-1"
    assert inserted_rows[0]["risk_flags"] == ["budget_change"]
    assert '"daily_budget": 12' in str(inserted_rows[0]["provider_payload_json"])

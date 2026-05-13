from ad_mcp.providers.meta_ads.payloads import build_meta_ads_payload
from ad_mcp.providers.meta_ads.analysis import rank_meta_entities
from ad_mcp.providers.meta_ads.auth import MetaAccountCredentials


def test_rank_meta_entities_cost_per_result_pushes_zero_conversion_rows_to_end(monkeypatch) -> None:
    rows = [
        {
            "campaign_id": "1",
            "campaign_name": "zero-conv",
            "objective": "OUTCOME_LEADS",
            "spend": "100",
            "impressions": "1000",
            "reach": "900",
            "clicks": "50",
            "inline_link_clicks": "50",
            "ctr": "5",
            "cpm": "100",
            "actions": [],
        },
        {
            "campaign_id": "2",
            "campaign_name": "has-conv",
            "objective": "OUTCOME_LEADS",
            "spend": "120",
            "impressions": "1000",
            "reach": "900",
            "clicks": "60",
            "inline_link_clicks": "60",
            "ctr": "6",
            "cpm": "120",
            "actions": [{"action_type": "lead", "value": "4"}],
        },
    ]

    monkeypatch.setattr(
        "ad_mcp.providers.meta_ads.analysis._get_rows",
        lambda *args, **kwargs: rows,
    )

    result = rank_meta_entities(
        MetaAccountCredentials(
            account_id="123",
            app_id="app-id",
            app_secret="secret",
            access_token="token",
            action_metrics=["lead"],
        ),
        "campaign",
        "2026-04-29",
        "2026-05-05",
        "cost_per_result",
        5,
    )

    assert result["rows"][0]["entity_id"] == "2"


def test_update_campaign_payload_keeps_budget_delta_without_create_defaults() -> None:
    payload = build_meta_ads_payload(
        "update",
        "campaign",
        {
            "id": "123",
            "budget_delta_percent": 20.0,
        },
    )

    body = payload["body"]
    assert body["id"] == "123"
    assert body["budget_delta_percent"] == 20.0
    assert body["status"] is None
    assert body["objective"] is None


def test_bulk_ad_update_payload_keeps_ids() -> None:
    payload = build_meta_ads_payload(
        "update",
        "ad",
        {
            "ids": ["1", "2"],
            "status": "PAUSED",
            "extra_fields": {"operation": "bulk_pause"},
        },
    )

    body = payload["body"]
    assert body["ids"] == ["1", "2"]
    assert body["status"] == "PAUSED"
    assert body["operation"] == "bulk_pause"

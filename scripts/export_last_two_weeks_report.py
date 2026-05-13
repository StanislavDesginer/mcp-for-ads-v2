from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, "src")

from ad_mcp.web.service import MetaDashboardService


START_DATE = "2026-04-22"
END_DATE = "2026-05-05"


def _num(value: Any) -> float:
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0


def _sum_actions(row: dict[str, Any]) -> float:
    return round(sum(_num(action.get("value")) for action in row.get("actions") or []), 2)


def _totals(rows: list[dict[str, Any]]) -> dict[str, Any]:
    spend = sum(_num(row.get("spend")) for row in rows)
    impressions = sum(_num(row.get("impressions")) for row in rows)
    clicks = sum(_num(row.get("inline_link_clicks") or row.get("clicks")) for row in rows)
    reach = sum(_num(row.get("reach")) for row in rows)
    actions = sum(_sum_actions(row) for row in rows)
    return {
        "spend": round(spend, 2),
        "impressions": int(round(impressions)),
        "reach": int(round(reach)),
        "clicks": int(round(clicks)),
        "ctr": round(clicks / impressions * 100, 4) if impressions else 0.0,
        "cpc": round(spend / clicks, 2) if clicks else 0.0,
        "cpm": round(spend / impressions * 1000, 2) if impressions else 0.0,
        "raw_actions_total": round(actions, 2),
    }


def _clean_ranked_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    cleaned = []
    for row in rows:
        cleaned.append(
            {
                "id": row.get("entity_id"),
                "name": row.get("entity_name"),
                "objective": row.get("objective"),
                "spend": row.get("spend"),
                "impressions": row.get("impressions"),
                "reach": row.get("reach"),
                "clicks": row.get("clicks"),
                "conversions": row.get("conversions"),
                "ctr": row.get("ctr"),
                "cpc": row.get("cpc"),
                "cpm": row.get("cpm"),
                "cost_per_result": row.get("cost_per_result"),
            }
        )
    return cleaned


ERRORS: list[dict[str, str]] = []


def _safe_call(label: str, func, fallback):
    try:
        return func()
    except Exception as exc:  # Meta can rate-limit individual diagnostic calls.
        ERRORS.append(
            {
                "section": label,
                "error_type": type(exc).__name__,
                "message": str(exc).split("access_token=")[0][:800],
            }
        )
        return fallback


def main() -> None:
    output_path = Path("outputs/meta_last_two_weeks_report_data.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    service = MetaDashboardService()
    account_id = service._default_account_id()
    provider = service._provider
    account = provider.get_account_summary(account_id)

    fields = [
        "campaign_id",
        "campaign_name",
        "adset_id",
        "adset_name",
        "ad_id",
        "ad_name",
        "objective",
        "spend",
        "impressions",
        "reach",
        "clicks",
        "inline_link_clicks",
        "ctr",
        "cpm",
        "actions",
    ]
    campaign_raw = provider.get_flexible_insights(
        account_id,
        "campaign",
        START_DATE,
        END_DATE,
        fields=fields,
        params={"time_increment": "all_days"},
        limit=500,
    )["rows"]

    report = {
        "period": {
            "start_date": START_DATE,
            "end_date": END_DATE,
            "definition": "14 full days before 2026-05-06",
        },
        "account": {
            "account_id": account_id,
            "name": account.get("account", {}).get("name") or account.get("name"),
            "currency": account.get("account", {}).get("currency") or account.get("currency"),
            "timezone": account.get("account", {}).get("timezone_name") or account.get("timezone_name"),
        },
        "summary": _totals(campaign_raw),
        "campaigns": _clean_ranked_rows(
            _safe_call(
                "campaign ranking",
                lambda: provider.rank_top_entities(account_id, "campaign", START_DATE, END_DATE, "spend", 50)["rows"],
                [],
            )
        ),
        "adsets": _clean_ranked_rows(
            _safe_call(
                "adset ranking",
                lambda: provider.rank_top_entities(account_id, "adset", START_DATE, END_DATE, "spend", 80)["rows"],
                [],
            )
        ),
        "ads": _clean_ranked_rows(
            _safe_call(
                "ad ranking",
                lambda: provider.rank_top_entities(account_id, "ad", START_DATE, END_DATE, "spend", 120)["rows"],
                [],
            )
        ),
        "no_result_ads": _clean_ranked_rows(
            _safe_call(
                "no-result ads",
                lambda: service.no_result_entities(account_id, END_DATE, 14, "ad", 20, 50)["rows"],
                [],
            )
        ),
        "burnout_ads": _safe_call(
            "burnout ads",
            lambda: provider.find_burnout_ads(account_id, START_DATE, END_DATE, 50).get("rows", []),
            [],
        ),
        "delivery_issues": _safe_call(
            "delivery issues",
            lambda: provider.get_delivery_issues(account_id, 50),
            {"issues": [], "issue_count": None},
        ),
        "errors": ERRORS,
    }
    output_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(str(output_path.resolve()))


if __name__ == "__main__":
    main()

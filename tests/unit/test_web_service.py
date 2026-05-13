from ad_mcp.web.service import MetaDashboardService


def test_date_window_defaults_to_requested_lookback() -> None:
    service = MetaDashboardService()
    start_date, _, end_date = service._date_window(end_date="2026-05-05", lookback_days=7)
    assert start_date == "2026-04-29"
    assert end_date == "2026-05-05"


def test_count_statuses_falls_back_to_status_field() -> None:
    service = MetaDashboardService()
    result = service._count_statuses(
        [
            {"effective_status": "ACTIVE"},
            {"status": "PAUSED"},
            {},
        ]
    )
    assert result == {"ACTIVE": 1, "PAUSED": 1, "UNKNOWN": 1}

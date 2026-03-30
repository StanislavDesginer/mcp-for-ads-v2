from __future__ import annotations

from ad_mcp.core.models import ReportRequest, ReportResponse
from ad_mcp.core.normalization import split_requested_fields


def build_tiktok_report_preview(request: ReportRequest, supported_metrics: list[str]) -> ReportResponse:
    matched, unsupported = split_requested_fields(
        request.fields or supported_metrics,
        supported_metrics,
    )
    return ReportResponse(
        provider="tiktok_ads",
        entity_level=request.entity_level,
        date_range=request.date_range,
        rows=[],
        normalized_metrics=matched,
        native_metrics=[],
        unsupported_requested_fields=unsupported,
        source_api="tiktok_marketing_api",
        preview=True,
    )

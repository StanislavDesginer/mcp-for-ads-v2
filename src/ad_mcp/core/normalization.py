from __future__ import annotations


COMMON_METRICS = [
    "reach",
    "impressions",
    "interactions",
    "clicks",
    "spend",
    "ctr",
    "cr",
    "conversions",
    "impression_share",
    "lost_impression_share",
    "quality_score",
    "expected_ctr",
    "landing_page_quality",
    "ad_quality",
]


def split_requested_fields(requested: list[str], supported: list[str]) -> tuple[list[str], list[str]]:
    supported_set = set(supported)
    matched = [field for field in requested if field in supported_set]
    unsupported = [field for field in requested if field not in supported_set]
    return matched, unsupported

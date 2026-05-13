from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class MetaAccountCredentials:
    account_id: str
    app_id: str
    app_secret: str
    access_token: str
    api_version: str = "v20.0"
    name: str | None = None
    action_metrics: list[str] | None = None
    video_metrics: list[str] | None = None


def normalize_meta_account_id(value: Any) -> str:
    account_id = str(value or "").strip()
    if account_id.startswith("act_"):
        return account_id[4:]
    return account_id


def credentials_from_config(config: dict[str, Any]) -> MetaAccountCredentials:
    return MetaAccountCredentials(
        account_id=normalize_meta_account_id(config["account_id"]),
        app_id=config["app_id"],
        app_secret=config["app_secret"],
        access_token=config["access_token"],
        api_version=config.get("api_version", "v20.0"),
        name=config.get("name"),
        action_metrics=config.get("action_metrics"),
        video_metrics=config.get("video_metrics"),
    )

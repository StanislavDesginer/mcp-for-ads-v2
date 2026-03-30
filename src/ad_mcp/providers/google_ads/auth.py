from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class GoogleAdsCredentials:
    account_id: str
    customer_id: str
    developer_token: str
    oauth_client_id: str
    oauth_client_secret: str
    refresh_token: str
    login_customer_id: str | None = None
    name: str | None = None


def credentials_from_config(config: dict[str, Any]) -> GoogleAdsCredentials:
    return GoogleAdsCredentials(
        account_id=str(config["account_id"]),
        customer_id=str(config.get("customer_id", config["account_id"])),
        developer_token=config["developer_token"],
        oauth_client_id=config["oauth_client_id"],
        oauth_client_secret=config["oauth_client_secret"],
        refresh_token=config["refresh_token"],
        login_customer_id=config.get("login_customer_id"),
        name=config.get("name"),
    )

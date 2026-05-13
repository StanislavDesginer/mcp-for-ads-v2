from ad_mcp.providers.meta_ads.auth import credentials_from_config
from ad_mcp.providers.meta_ads.client import MetaAdsProvider


def test_credentials_from_config_strips_act_prefix_from_account_id() -> None:
    credentials = credentials_from_config(
        {
            "account_id": "act_951047354096689",
            "app_id": "app-id",
            "app_secret": "secret",
            "access_token": "token",
        }
    )

    assert credentials.account_id == "951047354096689"


def test_credentials_from_config_keeps_numeric_account_id() -> None:
    credentials = credentials_from_config(
        {
            "account_id": "951047354096689",
            "app_id": "app-id",
            "app_secret": "secret",
            "access_token": "token",
        }
    )

    assert credentials.account_id == "951047354096689"


def test_meta_provider_get_account_config_accepts_numeric_id_for_act_prefixed_config() -> None:
    provider = MetaAdsProvider(
        config={
            "accounts": [
                {
                    "account_id": "act_951047354096689",
                    "app_id": "app-id",
                    "app_secret": "secret",
                    "access_token": "token",
                }
            ]
        }
    )

    account_config = provider.get_account_config("951047354096689")

    assert account_config["account_id"] == "act_951047354096689"


def test_meta_provider_get_account_config_accepts_act_prefixed_id_for_numeric_config() -> None:
    provider = MetaAdsProvider(
        config={
            "accounts": [
                {
                    "account_id": "951047354096689",
                    "app_id": "app-id",
                    "app_secret": "secret",
                    "access_token": "token",
                }
            ]
        }
    )

    account_config = provider.get_account_config("act_951047354096689")

    assert account_config["account_id"] == "951047354096689"

from ad_mcp.core.preview_manager import PreviewManager
from ad_mcp.providers.google_ads.client import GoogleAdsProvider


def test_preview_contains_provider_payload() -> None:
    provider = GoogleAdsProvider()
    preview = provider.preview_mutation(
        action="create",
        account_id="123",
        object_type="campaign",
        payload={"name": "Search Campaign", "campaign_type": "search"},
    )

    assert preview.provider_payload["resource"] == "campaign"
    assert preview.provider_payload["account_id"] == "123"
    assert preview.provider_payload["name"] == "Search Campaign"


def test_preview_manager_consume_removes_token() -> None:
    provider = GoogleAdsProvider()
    manager = PreviewManager()
    preview = manager.create(
        provider.preview_mutation(
            action="update",
            account_id="123",
            object_type="campaign",
            payload={"name": "Updated"},
        )
    )

    consumed = manager.consume(preview.token)

    assert consumed.token == preview.token

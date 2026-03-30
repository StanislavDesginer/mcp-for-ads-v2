from __future__ import annotations

from pathlib import Path
from typing import Any


class AuthManager:
    """Central place for future token loading and refresh flows."""

    def __init__(self, secrets_dir: Path, tokens_dir: Path) -> None:
        self.secrets_dir = secrets_dir
        self.tokens_dir = tokens_dir

    def describe_auth_strategy(self, provider: str) -> dict[str, Any]:
        strategies = {
            "google_ads": {
                "auth_type": "oauth_or_service_account",
                "secret_location": str(self.secrets_dir / "google_ads"),
                "token_cache": str(self.tokens_dir / "google_ads"),
            },
            "meta_ads": {
                "auth_type": "app_credentials_plus_access_token",
                "secret_location": str(self.secrets_dir / "meta_ads"),
                "token_cache": str(self.tokens_dir / "meta_ads"),
            },
            "tiktok_ads": {
                "auth_type": "oauth_or_access_token",
                "secret_location": str(self.secrets_dir / "tiktok_ads"),
                "token_cache": str(self.tokens_dir / "tiktok_ads"),
            },
            "yandex_direct": {
                "auth_type": "oauth_token",
                "secret_location": str(self.secrets_dir / "yandex_direct"),
                "token_cache": str(self.tokens_dir / "yandex_direct"),
            },
        }
        return strategies.get(provider, {"auth_type": "unknown"})

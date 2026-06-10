from __future__ import annotations

from pathlib import Path

from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


ROOT_DIR = Path(__file__).resolve().parents[2]
load_dotenv(ROOT_DIR / ".env")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="AD_MCP_", extra="ignore")

    env: str = "development"
    log_level: str = "INFO"
    audit_log_path: str = "logs/audit.jsonl"
    connections_config: str = "ads_config.yaml"
    policy_config: str = "config/policies/safety.example.yaml"
    web_host: str = "127.0.0.1"
    web_port: int = 8765
    web_api_token: str = ""
    web_max_body_bytes: int = 65536
    public_base_url: str = ""
    mcp_endpoint_path: str = "/mcp"
    meta_oauth_redirect_path: str = "/oauth/meta/callback"
    google_oauth_redirect_path: str = "/oauth/google/callback"
    connection_store_path: str = "tokens/connections.json"
    clickhouse_enabled: bool = False
    clickhouse_host: str = "127.0.0.1"
    clickhouse_port: int = 8123
    clickhouse_database: str = "ad_mcp_ai"
    clickhouse_user: str = "default"
    clickhouse_password: str = ""
    clickhouse_secure: bool = False
    clickhouse_timeout_seconds: float = 5.0
    clickhouse_auto_sync_workspace: bool = True
    project_root: Path = Field(default=ROOT_DIR)

    @property
    def audit_log_file(self) -> Path:
        return self.project_root / self.audit_log_path

    @property
    def connections_config_path(self) -> Path:
        return self.project_root / self.connections_config

    @property
    def policy_config_path(self) -> Path:
        return self.project_root / self.policy_config

    @property
    def connection_store_file(self) -> Path:
        return self.project_root / self.connection_store_path

    @property
    def mcp_route_path(self) -> str:
        clean = (self.mcp_endpoint_path or "/mcp").strip()
        if not clean.startswith("/"):
            clean = f"/{clean}"
        return clean

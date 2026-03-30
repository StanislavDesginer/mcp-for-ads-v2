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

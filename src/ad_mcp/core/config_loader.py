from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv

from ad_mcp.core.policy import SafetyPolicy


ROOT_DIR = Path(__file__).resolve().parents[3]
load_dotenv(ROOT_DIR / ".env")


_ENV_VAR_PATTERN = re.compile(r"\$\{([A-Z0-9_]+)(?::-([^}]*))?\}")


def _expand_env_string(value: str) -> str:
    def _replace(match: re.Match[str]) -> str:
        var_name = match.group(1)
        default_value = match.group(2)
        return os.getenv(var_name, default_value if default_value is not None else match.group(0))

    return _ENV_VAR_PATTERN.sub(_replace, value)


def _expand_env_values(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _expand_env_values(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_expand_env_values(item) for item in value]
    if isinstance(value, str):
        return _expand_env_string(value)
    return value


def load_yaml_file(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    return _expand_env_values(data)


def load_provider_config(config_dir: Path, provider: str) -> dict[str, Any]:
    primary = config_dir / f"{provider}.yaml"
    example = config_dir / f"{provider}.example.yaml"
    if primary.exists():
        return load_yaml_file(primary)
    return load_yaml_file(example)


def load_connections_config(path: Path | str) -> dict[str, Any]:
    primary = Path(path)
    example = primary.with_name(f"{primary.stem}.example{primary.suffix}")
    if primary.exists():
        return load_yaml_file(primary)
    return load_yaml_file(example)


def load_provider_from_connections(path: Path | str, provider: str) -> dict[str, Any]:
    config = load_connections_config(path)
    providers = config.get("providers", {})
    return providers.get(provider, {"provider": provider, "accounts": []})


def load_safety_policy(path: Path) -> SafetyPolicy:
    return SafetyPolicy.model_validate(load_yaml_file(path))

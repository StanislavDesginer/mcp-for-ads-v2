from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from ad_mcp.core.policy import SafetyPolicy


def load_yaml_file(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    return data


def load_provider_config(config_dir: Path, provider: str) -> dict[str, Any]:
    primary = config_dir / f"{provider}.yaml"
    example = config_dir / f"{provider}.example.yaml"
    if primary.exists():
        return load_yaml_file(primary)
    return load_yaml_file(example)


def load_connections_config(path: Path) -> dict[str, Any]:
    primary = path
    example = path.with_name(f"{path.stem}.example{path.suffix}")
    if primary.exists():
        return load_yaml_file(primary)
    return load_yaml_file(example)


def load_provider_from_connections(path: Path, provider: str) -> dict[str, Any]:
    config = load_connections_config(path)
    providers = config.get("providers", {})
    return providers.get(provider, {"provider": provider, "accounts": []})


def load_safety_policy(path: Path) -> SafetyPolicy:
    return SafetyPolicy.model_validate(load_yaml_file(path))

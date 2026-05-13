from pathlib import Path

from ad_mcp.core.config_loader import load_yaml_file


def test_load_yaml_file_expands_environment_variables(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("TEST_SECRET", "resolved-value")
    config_file = tmp_path / "config.yaml"
    config_file.write_text("token: ${TEST_SECRET}\nname: ${MISSING_VAR:-fallback}\n", encoding="utf-8")

    data = load_yaml_file(config_file)

    assert data["token"] == "resolved-value"
    assert data["name"] == "fallback"

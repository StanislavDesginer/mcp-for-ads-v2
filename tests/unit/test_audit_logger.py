from __future__ import annotations

import json

from ad_mcp.core.audit_logger import AuditLogger


def test_audit_logger_redacts_secret_keys_and_secret_string_values(tmp_path) -> None:
    log_file = tmp_path / "audit.jsonl"
    logger = AuditLogger(log_file)

    logger.log(
        "test",
        {
            "access_token": "direct-secret",
            "url": "https://example.test/callback?access_token=url-secret&state=ok",
            "header": "Authorization: Bearer bearer-secret",
        },
    )

    payload = json.loads(log_file.read_text(encoding="utf-8").strip())["payload"]
    serialized = json.dumps(payload)

    assert "direct-secret" not in serialized
    assert "url-secret" not in serialized
    assert "bearer-secret" not in serialized
    assert payload["access_token"] == "***REDACTED***"
    assert "access_token=***REDACTED***" in payload["url"]
    assert "Bearer ***REDACTED***" in payload["header"]

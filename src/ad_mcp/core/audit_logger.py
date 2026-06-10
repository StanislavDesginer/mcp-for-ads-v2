from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


_SECRET_VALUE_RE = re.compile(
    r"(?i)\b(access_token|refresh_token|client_secret|app_secret|api_key|authorization|password|secret|token)=([^&\s]+)"
)
_BEARER_RE = re.compile(r"(?i)\bBearer\s+[A-Za-z0-9._~+/=-]+")


class AuditLogger:
    def __init__(self, path: Path) -> None:
        self.path = path

    def log(self, event_type: str, payload: dict[str, Any]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        event = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_type": event_type,
            "payload": self._redact(payload),
        }
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event, ensure_ascii=True) + "\n")

    def _redact(self, value: Any) -> Any:
        sensitive_markers = ("token", "secret", "password", "key", "authorization")
        if isinstance(value, dict):
            redacted: dict[str, Any] = {}
            for key, item in value.items():
                lowered = key.lower()
                if any(marker in lowered for marker in sensitive_markers):
                    redacted[key] = "***REDACTED***"
                else:
                    redacted[key] = self._redact(item)
            return redacted
        if isinstance(value, list):
            return [self._redact(item) for item in value]
        if isinstance(value, str):
            value = _SECRET_VALUE_RE.sub(lambda match: f"{match.group(1)}=***REDACTED***", value)
            return _BEARER_RE.sub("Bearer ***REDACTED***", value)
        return value

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from ad_mcp.core.errors import PreviewNotFoundError
from ad_mcp.core.models import PreviewRecord


class PreviewManager:
    def __init__(self) -> None:
        self._records: dict[str, PreviewRecord] = {}

    def create(self, record: PreviewRecord) -> PreviewRecord:
        self._records[record.token] = record
        return record

    def get(self, token: str) -> PreviewRecord:
        record = self._records.get(token)
        if record is None:
            raise PreviewNotFoundError(f"Preview token not found: {token}")
        if datetime.now(timezone.utc) > record.created_at + timedelta(seconds=record.expires_in_seconds):
            self._records.pop(token, None)
            raise PreviewNotFoundError(f"Preview token expired: {token}")
        return record

    def consume(self, token: str) -> PreviewRecord:
        record = self.get(token)
        self._records.pop(token, None)
        return record

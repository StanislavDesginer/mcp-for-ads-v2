from __future__ import annotations

import json
import logging
import secrets
import uuid
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from ad_mcp.core.errors import AdMCPError
from ad_mcp.settings import Settings, is_network_exposed_host
from ad_mcp.web.hosted import HostedConnectionService
from ad_mcp.web.service import MetaDashboardService


WEB_ROOT = Path(__file__).resolve().parent
STATIC_ROOT = WEB_ROOT / "static"
LOGGER = logging.getLogger(__name__)
AUTH_HEADER = "Authorization"
TOKEN_HEADER = "X-AD-MCP-BETA-TOKEN"


def _api_token_required(settings: Settings) -> bool:
    return bool(settings.web_api_token.strip()) or settings.env.lower() == "production" or is_network_exposed_host(settings.web_host)


def _extract_request_token(headers) -> str:
    header_value = str(headers.get(AUTH_HEADER, "") or "").strip()
    if header_value.lower().startswith("bearer "):
        return header_value[7:].strip()
    return str(headers.get(TOKEN_HEADER, "") or "").strip()


def _request_token_is_valid(headers, settings: Settings) -> bool:
    expected = settings.web_api_token.strip()
    if not _api_token_required(settings):
        return True
    if not expected:
        return False
    candidate = _extract_request_token(headers)
    return bool(candidate) and secrets.compare_digest(candidate, expected)


class AdsWebHandler(BaseHTTPRequestHandler):
    settings = Settings()
    hosted = HostedConnectionService()
    service = MetaDashboardService()

    def _set_default_headers(self) -> None:
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Cache-Control", "no-store")

    def _send_json(self, payload: dict, status: HTTPStatus = HTTPStatus.OK, headers: dict[str, str] | None = None) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self._set_default_headers()
        self.send_header("Content-Type", "application/json; charset=utf-8")
        for key, value in (headers or {}).items():
            self.send_header(key, value)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_file(self, path: Path, content_type: str) -> None:
        body = path.read_bytes()
        self.send_response(HTTPStatus.OK)
        self._set_default_headers()
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _redirect(self, location: str) -> None:
        self.send_response(HTTPStatus.FOUND)
        self._set_default_headers()
        self.send_header("Location", location)
        self.send_header("Content-Length", "0")
        self.end_headers()

    def _error(self, message: str, status: HTTPStatus = HTTPStatus.BAD_REQUEST, code: str = "bad_request") -> None:
        self._send_json({"error": message, "code": code}, status)

    def _ensure_api_authorized(self, route: str) -> bool:
        protected_route = route.startswith("/api/") or route == self.settings.mcp_route_path
        if not protected_route or not _api_token_required(self.settings):
            return True
        if not self.settings.web_api_token.strip():
            self._error(
                "Web API закрыт: AD_MCP_WEB_API_TOKEN не настроен на сервере.",
                HTTPStatus.SERVICE_UNAVAILABLE,
                "api_auth_not_configured",
            )
            return False
        if not _request_token_is_valid(self.headers, self.settings):
            self._send_json(
                {"error": "Нужен beta token для доступа к MCP web API.", "code": "api_auth_required"},
                HTTPStatus.UNAUTHORIZED,
                {"WWW-Authenticate": 'Bearer realm="AdForge MCP"'},
            )
            return False
        return True

    def _client_error_message(self, exc: Exception) -> str:
        if isinstance(exc, json.JSONDecodeError):
            return "Некорректный JSON в теле запроса."
        if isinstance(exc, KeyError):
            return f"Не хватает обязательного поля: {exc.args[0]}"
        text = str(exc).strip()
        if not text:
            return "Запрос не может быть выполнен."
        if len(text) > 320:
            return f"{text[:317]}..."
        return text

    def _unexpected_error(self, operation: str, exc: Exception) -> None:
        request_id = uuid.uuid4().hex[:12]
        LOGGER.exception("Unhandled web UI error during %s %s request_id=%s", operation, self.path, request_id)
        self._send_json(
            {
                "error": "Непредвиденная ошибка web-layer. Проверьте логи сервера.",
                "code": "internal_error",
                "request_id": request_id,
            },
            HTTPStatus.BAD_GATEWAY,
        )
        return

    def _query(self) -> dict[str, str]:
        parsed = urlparse(self.path)
        return {key: values[-1] for key, values in parse_qs(parsed.query).items() if values}

    def _json_body(self) -> dict:
        try:
            content_length = int(self.headers.get("Content-Length", "0"))
        except ValueError as exc:
            raise ValueError("Некорректный Content-Length.") from exc
        if content_length <= 0:
            return {}
        if content_length > self.settings.web_max_body_bytes:
            raise ValueError("Тело запроса слишком большое.")
        return json.loads(self.rfile.read(content_length).decode("utf-8"))

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        route = parsed.path
        try:
            if route == "/":
                return self._send_file(STATIC_ROOT / "index.html", "text/html; charset=utf-8")
            if route == "/healthz":
                return self._send_json({"status": "ok"})
            if route == "/assets/app.css":
                return self._send_file(STATIC_ROOT / "app.css", "text/css; charset=utf-8")
            if route == "/assets/app.js":
                return self._send_file(STATIC_ROOT / "app.js", "application/javascript; charset=utf-8")
            if route == self.settings.meta_oauth_redirect_path:
                return self._send_json(self.hosted.meta_oauth_callback(self._query()))

            if not self._ensure_api_authorized(route):
                return

            if route == self.settings.mcp_route_path:
                return self._send_json(self.hosted.mcp_transport_placeholder(), HTTPStatus.NOT_IMPLEMENTED)

            query = self._query()
            account_id = query.get("account_id")
            end_date = query.get("end_date")

            if route == "/api/hosted/mcp-connection":
                return self._send_json(self.hosted.mcp_connection_info())
            if route == "/api/hosted/connections":
                return self._send_json(self.hosted.connections())
            if route == "/api/hosted/oauth/meta/start":
                return self._redirect(self.hosted.meta_oauth_redirect_url())
            if route == "/api/hosted/oauth/meta/pending":
                return self._send_json(self.hosted.meta_oauth_pending(str(query["pending_id"])))
            if route == "/api/hosted/oauth/google/start":
                return self._send_json(self.hosted.oauth_start_preview("google_ads"), HTTPStatus.NOT_IMPLEMENTED)

            if route == "/api/meta/dashboard":
                return self._send_json(self.service.dashboard(account_id=account_id, end_date=end_date))
            if route == "/api/meta/workspace":
                return self._send_json(self.service.workspace(account_id=account_id, end_date=end_date))
            if route == "/api/meta/data-contract":
                return self._send_json(self.service.data_contract())
            if route == "/api/meta/campaign-structure":
                return self._send_json(self.service.campaign_structure(account_id=account_id))
            if route == "/api/meta/delivery-issues":
                return self._send_json(self.service.delivery_issues(account_id=account_id, limit=int(query.get("limit", "20"))))
            if route == "/api/meta/assets":
                return self._send_json(self.service.connected_assets(account_id=account_id))
            if route == "/api/meta/top-performers":
                return self._send_json(
                    self.service.top_performers(
                        account_id=account_id,
                        end_date=end_date,
                        lookback_days=int(query.get("lookback_days", "7")),
                        entity_level=query.get("entity_level", "campaign"),
                        metric=query.get("metric", "cost_per_result"),
                        limit=int(query.get("limit", "5")),
                    )
                )
            if route == "/api/meta/no-result-entities":
                return self._send_json(
                    self.service.no_result_entities(
                        account_id=account_id,
                        end_date=end_date,
                        lookback_days=int(query.get("lookback_days", "7")),
                        entity_level=query.get("entity_level", "ad"),
                        min_spend=float(query.get("min_spend", "20")),
                        limit=int(query.get("limit", "10")),
                    )
                )
            if route == "/api/meta/config-diagnostics":
                return self._send_json(self.service.config_diagnostics())
            if route == "/api/meta/auth-diagnostics":
                return self._send_json(self.service.auth_diagnostics())
            if route == "/api/meta/persistence":
                return self._send_json(self.service.persistence_diagnostics())
            if route == "/api/meta/debug-health":
                return self._send_json(self.service.diagnostics_health())
            if route == "/api/meta/skills/catalog":
                return self._send_json(self.service.skill_catalog(account_id=account_id, end_date=end_date))
            if route == "/api/meta/skills/budget-summary":
                return self._send_json(self.service.summarize_budget_skill(account_id=account_id, end_date=end_date))
            if route == "/api/meta/skills/disable-candidates":
                return self._send_json(
                    self.service.disable_candidates_skill(
                        account_id=account_id,
                        end_date=end_date,
                        lookback_days=int(query.get("lookback_days", "7")),
                        entity_level=query.get("entity_level", "ad"),
                        min_spend=float(query.get("min_spend", "20")),
                        limit=int(query.get("limit", "10")),
                    )
                )
            if route == "/api/meta/skills/scale-candidates":
                return self._send_json(
                    self.service.scale_candidates_skill(
                        account_id=account_id,
                        end_date=end_date,
                        lookback_days=int(query.get("lookback_days", "7")),
                        entity_level=query.get("entity_level", "campaign"),
                        max_cost_per_result=float(query.get("max_cost_per_result", "20")),
                        min_conversions=float(query.get("min_conversions", "1")),
                        limit=int(query.get("limit", "10")),
                    )
                )
            if route == "/api/meta/skills/collect-report":
                return self._send_json(
                    self.service.collect_report_skill(
                        account_id=account_id,
                        end_date=end_date,
                        lookback_days=int(query.get("lookback_days", "7")),
                        entity_level=query.get("entity_level", "campaign"),
                        min_spend=float(query.get("min_spend", "20")),
                        max_cost_per_result=float(query.get("max_cost_per_result", "20")),
                    )
                )
        except (AdMCPError, ValueError, KeyError, json.JSONDecodeError, RuntimeError) as exc:
            return self._error(self._client_error_message(exc))
        except Exception as exc:  # noqa: BLE001
            return self._unexpected_error("GET", exc)

        self._error("Route not found.", HTTPStatus.NOT_FOUND)

    def do_POST(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        route = parsed.path
        try:
            if not self._ensure_api_authorized(route):
                return
            payload = self._json_body()
            if route == "/api/hosted/connections/import-local":
                return self._send_json(self.hosted.import_local_provider(str(payload["provider"])))
            if route == "/api/hosted/oauth/meta/select":
                return self._send_json(self.hosted.meta_oauth_select(payload))
            if route == "/api/meta/preview/clone-campaign":
                return self._send_json(
                    self.service.preview_clone_campaign(
                        source_campaign_id=str(payload["source_campaign_id"]),
                        new_name=payload.get("new_name"),
                        daily_budget=payload.get("daily_budget"),
                        lifetime_budget=payload.get("lifetime_budget"),
                        status=str(payload.get("status", "PAUSED")),
                        account_id=payload.get("account_id"),
                    )
                )
            if route == "/api/meta/preview/update-campaign-budget":
                return self._send_json(
                    self.service.preview_update_campaign_budget(
                        campaign_id=str(payload["campaign_id"]),
                        daily_budget=payload.get("daily_budget"),
                        lifetime_budget=payload.get("lifetime_budget"),
                        spend_cap=payload.get("spend_cap"),
                        budget_delta_percent=payload.get("budget_delta_percent"),
                        account_id=payload.get("account_id"),
                    )
                )
            if route == "/api/meta/preview/pause-ads":
                ids = payload.get("ids") or []
                return self._send_json(self.service.preview_pause_ads(ids=[str(item) for item in ids], account_id=payload.get("account_id")))
        except (AdMCPError, ValueError, KeyError, json.JSONDecodeError, RuntimeError) as exc:
            return self._error(self._client_error_message(exc))
        except Exception as exc:  # noqa: BLE001
            return self._unexpected_error("POST", exc)

        self._error("Route not found.", HTTPStatus.NOT_FOUND)

    def log_message(self, format: str, *args) -> None:  # noqa: A003
        return


def main() -> None:
    settings = Settings()
    host = settings.web_host
    port = settings.web_port
    AdsWebHandler.settings = settings
    AdsWebHandler.hosted = HostedConnectionService(settings)
    AdsWebHandler.service = MetaDashboardService(settings)
    if _api_token_required(settings) and not settings.web_api_token.strip():
        LOGGER.warning("AD_MCP_WEB_API_TOKEN is required for production web API access but is not configured.")
    server = ThreadingHTTPServer((host, port), AdsWebHandler)
    print(f"Meta MCP web UI running at http://{host}:{port}")
    server.serve_forever()


if __name__ == "__main__":
    main()

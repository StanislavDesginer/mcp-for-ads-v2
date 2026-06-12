# Live beta status AdForge MCP

Дата обновления: 2026-06-12.

Этот документ фиксирует честный live-статус hosted beta. Маркеры статусов:

- `verified_live` — проверено напрямую на live URL в эту сессию;
- `verified_by_operator` — проверено оператором на предыдущем этапе (этап 11), в эту сессию не перепроверялось;
- `not_verified` — не проверено;
- `needs_credentials` — заблокировано отсутствием provider credentials в live env;
- `needs_vps_access` — требуется SSH-доступ к VPS;
- `needs_provider_dashboard_access` — требуется доступ к кабинету провайдера (Meta App Dashboard / Google Cloud Console).

## Live deployment

- Live URL: `https://77.240.38.131.sslip.io` — `verified_live` (HTTPS отвечает).
- Deployed commit: `d6602c4 Allow hosted MCP public reverse proxy host` — `verified_by_operator` (проверка `git log` на VPS требует SSH).
- Repo на VPS: `/opt/adforge-mcp` — `verified_by_operator`.
- Live env: `/etc/adforge-mcp/adforge-mcp.env` — `verified_by_operator`.
- Storage: `/var/lib/adforge-mcp/connections.json` — `verified_live` (путь подтверждён через `/ready`, storage readable + valid_format).
- Services `adforge-mcp-web`, `adforge-mcp-http` — `verified_live` косвенно: web отвечает на `/health`, MCP transport отвечает на `/mcp` (401 без token, значит процесс жив); `systemctl status` требует SSH.

## Public endpoint checks (выполнено в эту сессию)

- `GET /health` → `{"status": "ok", "service": "adforge-mcp-web"}` — `verified_live`.
- `GET /ready` → `status=ready`, `environment=beta`, `beta_token required+configured`, `preview_only enabled`, `storage ok`, `mcp_transport available` — `verified_live`.
- `GET /api/diagnostics` без token → `401` — `verified_live`.
- `POST /mcp` без token → `401` (`invalid_token`, Authentication required) — `verified_live`.
- `GET /tokens/connections.json` → `403` (private path blocked) — `verified_live`.
- `GET /oauth/meta/callback` → `302` на dashboard с понятной ошибкой — `verified_live`.
- `GET /oauth/google/callback` → `302` на dashboard с понятной ошибкой — `verified_live`.
- `GET /api/hosted/oauth/meta/authorize-url` без token → `401` — `verified_live`.

## Dashboard status

- Dashboard открывается по HTTPS — `verified_by_operator` (этап 11).
- Connections UI: карточки Meta/Google/TikTok/Yandex, OAuth start, pending selection, выбор аккаунтов, reconnect/disconnect, Copy MCP URL, Run diagnostics — реализовано в коде, покрыто unit-тестами; live-прогон с beta token в эту сессию — `not_verified` (token недоступен в этой сессии).

## MCP status

- Hosted MCP transport: Streamable HTTP на `/mcp`, bearer auth — `verified_live` (401 без token).
- Подключение официальным `mcp.client.streamable_http`, tools count 110, `run_diagnostics`, `list_connected_platforms`, `list_ad_accounts` — `verified_by_operator` (этап 11).
- Strict smoke `scripts/smoke_hosted_beta.py --strict-deploy` — `verified_by_operator` (этап 11); повторный прогон в эту сессию требует beta token — `not_verified`.
- MCP diagnostics возвращает `needs_setup`, потому что ни один рекламный аккаунт ещё не подключён — ожидаемое честное состояние.

## Security diagnostics

- `api_auth_required=true` — `verified_live` (401 без token на `/api/*` и `/mcp`).
- `beta_token_configured=true` — `verified_live` (через `/ready`).
- `preview_only=true`, `live_writes_enabled=false` — `verified_live` (через `/ready`); полный `/api/diagnostics/security` требует token — `verified_by_operator`.
- `tokens_returned=false`, `secrets_redacted=true` — заявлено кодом и покрыто unit-тестами; live-ответ `/api/diagnostics/security` в эту сессию — `not_verified` (нужен token).
- Логи на отсутствие секретов — `needs_vps_access`.

## OAuth status по платформам

| Платформа | Live статус | Подтверждение |
| --- | --- | --- |
| Meta Ads | `needs_credentials` — env `AD_MCP_META_OAUTH_APP_ID` / `AD_MCP_META_OAUTH_APP_SECRET` отсутствуют на live | `verified_live`: callback честно отвечает "Meta OAuth is not configured" |
| Google Ads | `needs_credentials` — env `AD_MCP_GOOGLE_OAUTH_CLIENT_ID` / `AD_MCP_GOOGLE_OAUTH_CLIENT_SECRET` / `AD_MCP_GOOGLE_ADS_DEVELOPER_TOKEN` отсутствуют на live | `verified_live`: callback честно отвечает "google_ads OAuth is not configured" |
| TikTok Ads | env частично настроен, `authorize-url` отвечал `oauth_ready`; live OAuth не проходил | `verified_by_operator`; в эту сессию `not_verified` (нужен token) |
| Yandex Direct | env частично настроен, `authorize-url` отвечал `oauth_ready`; live OAuth не проходил | `verified_by_operator`; в эту сессию `not_verified` (нужен token) |

- Connected platforms: 0.
- Connected accounts: 0.
- Live OAuth НЕ был пройден ни для одной платформы. Fake-результаты не создавались.

## Read tools / metrics status

- `list_connected_platforms`, `list_ad_accounts`, `get_account_status`, `run_connection_diagnostics`, `run_diagnostics` — работают и без подключённых аккаунтов (возвращают честный `not_connected` / `needs_setup`) — `verified_by_operator` на live, unit-тесты зелёные локально.
- `list_campaigns`, `get_campaign`, `get_campaign_statuses`, `get_basic_metrics` — вернут реальные данные только после подключения аккаунта; до этого честно возвращают `not_available` / policy error. Live-проверка с реальным аккаунтом — `needs_credentials`.
- MCP tools перечитывают hosted connection store при каждом вызове, поэтому после OAuth-подключения рестарт `adforge-mcp-http` не обязателен для появления аккаунтов в read tools.

## Preview-only status

- `AD_MCP_PREVIEW_ONLY=true` на live — `verified_live` (через `/ready`).
- Все preview tools возвращают `will_apply=false`, `mode=preview_only`; `commit_preview` возвращает `status=blocked` — закреплено unit-тестами и smoke-скриптом.
- Проверка preview tools на реальном `campaign_id` — `needs_credentials` (нет подключённого аккаунта).

## Backup status

- Последний известный backup: `/var/backups/adforge-mcp/connections-20260612-170210.json` — `verified_by_operator`.
- Новый backup после подключения аккаунтов не делался, потому что аккаунты ещё не подключались — `needs_vps_access` после live OAuth.

## Что нужно для завершения этапа 12 (live OAuth Meta / Google)

### Meta Ads

1. Создать/открыть Meta app (тип Business) в Meta App Dashboard — `needs_provider_dashboard_access`.
2. В Facebook Login → Settings добавить Valid OAuth Redirect URI: `https://77.240.38.131.sslip.io/oauth/meta/callback`.
3. Убедиться, что app имеет permissions `ads_read`, `business_management` (для dev mode достаточно роли разработчика/тестера у пользователя с доступом к рекламному кабинету).
4. На VPS добавить в `/etc/adforge-mcp/adforge-mcp.env` (не в repo, не в отчёты): `AD_MCP_META_OAUTH_APP_ID`, `AD_MCP_META_OAUTH_APP_SECRET`.
5. `sudo systemctl restart adforge-mcp-web adforge-mcp-http`.
6. Проверить: `curl -H "Authorization: Bearer <BETA_TOKEN>" https://77.240.38.131.sslip.io/api/hosted/oauth/meta/diagnostics` → `status=configured`.
7. Пройти dashboard flow: Connections → Connect Meta Ads → OAuth → выбор аккаунтов → Save → Run diagnostics.
8. Проверить MCP tools: `list_ad_accounts`, `list_campaigns platform=meta_ads`, `get_basic_metrics platform=meta_ads` за последние 7 дней.

### Google Ads

1. В Google Cloud Console создать OAuth Client (Web application) — `needs_provider_dashboard_access`.
2. Добавить Authorized redirect URI: `https://77.240.38.131.sslip.io/oauth/google/callback`.
3. Настроить OAuth consent screen; если app в testing mode — добавить test user.
4. Включить Google Ads API в проекте; получить Developer Token в Google Ads (API Center); для test developer token работают только test accounts.
5. На VPS добавить в `/etc/adforge-mcp/adforge-mcp.env`: `AD_MCP_GOOGLE_OAUTH_CLIENT_ID`, `AD_MCP_GOOGLE_OAUTH_CLIENT_SECRET`, `AD_MCP_GOOGLE_ADS_DEVELOPER_TOKEN`, опционально `AD_MCP_GOOGLE_ADS_LOGIN_CUSTOMER_ID` (manager account, цифры без дефисов).
6. `sudo systemctl restart adforge-mcp-web adforge-mcp-http`.
7. Пройти dashboard flow: Connections → Connect Google Ads → OAuth (consent + offline access уже запрашиваются кодом) → выбор customer accounts → Save → Run diagnostics.
8. Проверить MCP tools: `list_campaigns platform=google_ads`, `get_basic_metrics platform=google_ads`.

### После подключения (обе платформы)

1. `python scripts/smoke_hosted_beta.py --base-url https://77.240.38.131.sslip.io --token "<BETA_TOKEN>" --strict-deploy` → все checks ok.
2. Проверить логи: `sudo journalctl -u adforge-mcp-web -n 200 | grep -iE "access_token|refresh_token|client_secret|app_secret|developer_token|bearer"` → пусто.
3. Preview-проверка на реальном campaign_id: `preview_change_campaign_budget`, `preview_pause_campaign`, `preview_resume_campaign` → `will_apply=false`, `commit_preview` → `blocked`.
4. Backup: `sudo -u adforge cp /var/lib/adforge-mcp/connections.json "/var/backups/adforge-mcp/connections-$(date +%Y%m%d-%H%M%S).json" && sudo chmod 600 /var/backups/adforge-mcp/connections-*.json`.
5. Обновить этот документ.

## Known limitations

- Реальные write-действия отключены (preview-only) — это осознанное ограничение beta.
- TikTok/Yandex: campaigns/metrics могут возвращать `not_available` — read-интеграция в beta ограничена.
- Connection store — JSON-файл без межпроцессных блокировок; одновременные OAuth-операции из нескольких сессий могут перезаписать друг друга. Для одного beta-оператора приемлемо.
- `sslip.io` домен и self-issued IP-cert цепочка зависят от Let's Encrypt; для продакшена нужен собственный домен.

## Готовность к demo

Готово сейчас (без реальных данных):

- hosted dashboard + beta token gate;
- hosted MCP endpoint с bearer auth (110 tools);
- диагностика и честные `needs_setup`/`not_connected` статусы;
- preview-only guardrails.

Блокеры demo с реальными рекламными данными:

1. Meta OAuth credentials в live env — `needs_credentials`.
2. Google OAuth credentials + developer token в live env — `needs_credentials`.
3. Прохождение live OAuth и выбор аккаунтов в dashboard — после п.1/п.2.
4. Проверка read tools и метрик на реальном аккаунте — после п.3.
5. Backup storage после подключения — после п.3.

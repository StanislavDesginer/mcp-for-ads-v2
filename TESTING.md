# Как тестировать AdForge MCP

AdForge MCP тестируется в двух разных режимах:

1. Beta customer flow - проверка уже развернутого hosted dashboard/MCP.
2. Developer flow - локальные тесты репозитория и серверной логики.

Beta-клиент не скачивает репозиторий и не запускает MCP локально.

## Beta customer flow

Используйте [docs/beta/BETA_DEMO_CHECKLIST_RU.md](docs/beta/BETA_DEMO_CHECKLIST_RU.md).

Короткий smoke:

1. Открыть dashboard URL.
2. Ввести beta token, если dashboard запросил доступ.
3. Открыть `Connections`.
4. Проверить hosted MCP URL.
5. Подключить Meta Ads/Google Ads через OAuth или проверить уже сохраненное подключение.
6. Запустить `Run diagnostics`.
7. Подключить MCP URL в Codex/Claude.
8. Выполнить запросы:
   - `Проверь диагностику AdForge MCP`.
   - `Покажи подключенные рекламные аккаунты`.
   - `Покажи кампании Meta Ads`.
   - `Сделай preview изменения бюджета кампании, но ничего не применяй`.

Ожидаемый safety-result: dangerous action возвращает `will_apply=false`.

## Developer flow

Локальный запуск нужен разработчикам и серверной команде.

### Windows

```powershell
cd "C:\MCP\AdForge-MCP"
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev,google,meta]"
```

### Linux / VPS

```bash
cd /opt/adforge-mcp
python3.11 -m venv .venv
./.venv/bin/python -m pip install -e ".[dev,google,meta]"
```

## Developer checks

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m compileall src
node --check src/ad_mcp/web/static/app.js
.\.venv\Scripts\python.exe scripts/smoke_mcp_beta.py
```

## Local dashboard check

```powershell
.\.venv\Scripts\python.exe -m ad_mcp.web.server
```

Открыть:

```text
http://127.0.0.1:8765
```

## Local hosted MCP transport check

```powershell
.\.venv\Scripts\ad-mcp-http.exe
```

По умолчанию MCP route:

```text
http://127.0.0.1:8766/mcp
```

## Secrets

Локальные `.env`, `ads_config.yaml` и `tokens/connections.json` нужны только developer/server runtime и не коммитятся.

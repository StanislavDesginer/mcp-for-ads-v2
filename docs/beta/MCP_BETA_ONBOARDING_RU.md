# MCP for Ads beta onboarding

Эта инструкция нужна, чтобы beta-тестер мог локально поднять MCP, подключить его к Codex/Claude/GPT-compatible клиенту, проверить диагностику и работать только через безопасные preview-сценарии.

## 1. Установка

```powershell
git clone git@github.com:mcpforge-dev/mcp-for-ads-v2.git
cd mcp-for-ads-v2
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev,google,meta]"
```

Если репозиторий уже скачан:

```powershell
cd C:\MCP\mcp-for-ads-v2
git pull origin main
.\.venv\Scripts\python.exe -m pip install -e ".[dev,google,meta]"
```

## 2. Локальные файлы

Создать в корне проекта два локальных файла:

```powershell
Copy-Item .env.example .env
Copy-Item ads_config.example.yaml ads_config.yaml
```

Эти файлы не коммитятся. Они уже добавлены в `.gitignore`.

Проверка:

```powershell
git check-ignore -v .env ads_config.yaml
git status --short
```

## 3. Что нужно для Meta Ads

В `.env`:

- `META_ACCESS_TOKEN`
- `META_APP_SECRET`
- при нескольких кабинетах отдельные переменные вида `META_VARIKOZA_ACCESS_TOKEN`, `META_VARIKOZA_APP_SECRET`

В `ads_config.yaml`:

- `provider: meta_ads`
- `name`
- `account_id`
- `app_id`
- `app_secret`, лучше через `${META_APP_SECRET}`
- `access_token`, лучше через `${META_ACCESS_TOKEN}`
- `api_version`, например `v20.0`
- нужные action/video metrics

Meta `account_id` можно указывать с `act_` или без него, если конкретный tool это поддерживает. В config лучше хранить стабильный ID кабинета.

## 4. Что нужно для Google Ads

В `ads_config.yaml` для `google_ads`:

- `customer_id`
- `login_customer_id`, если используется manager account
- `developer_token`
- `oauth_client_id`
- `oauth_client_secret`
- `refresh_token`

Секреты лучше держать в `.env` и подставлять в YAML через `${GOOGLE_ADS_REFRESH_TOKEN}` и аналогичные переменные.

## 5. MCP config для клиента

Минимальный пример лежит в:

- `docs/beta/mcp.example.json`

Для локального beta-запуска на этом ноутбуке команда выглядит так:

```json
{
  "mcpServers": {
    "mcp-for-ads": {
      "command": "C:\\MCP\\mcp-for-ads-v2\\.venv\\Scripts\\python.exe",
      "args": ["-m", "ad_mcp.server"],
      "cwd": "C:\\MCP\\mcp-for-ads-v2"
    }
  }
}
```

В Codex, Claude Desktop или другом GPT-compatible MCP-клиенте нужно добавить сервер `mcp-for-ads` с этой командой. Формат поля может отличаться у клиента, но смысл один: запускать `python -m ad_mcp.server` из корня проекта.

## 6. Проверка MCP

Быстрая проверка без live write:

```powershell
.\.venv\Scripts\python.exe scripts\smoke_mcp_beta.py
```

Что проверяет smoke:

- server imports
- tools register
- `get_beta_diagnostics` доступен
- discovery tools отвечают
- preview mutation возвращает `status=preview`
- live write не выполняется

Если нет настроенного Meta account в `ads_config.yaml`, можно явно пропустить preview:

```powershell
.\.venv\Scripts\python.exe scripts\smoke_mcp_beta.py --skip-preview
```

## 7. Диагностика внутри MCP-клиента

После подключения попросить клиента вызвать:

- `list_providers`
- `get_beta_diagnostics`
- `get_provider_capabilities` для `meta_ads`
- `list_accounts` для `meta_ads`
- `describe_auth_strategy` для `meta_ads`

Для Google Ads аналогично заменить provider на `google_ads`.

## 8. Безопасная работа

В beta write-сценарии должны идти через preview:

- `clone_campaign_preview`
- `update_campaign_budget_preview`
- `pause_entities_preview`
- другие tools с суффиксом `_preview`

Не использовать commit/write-confirm действия до отдельной проверки production-политики и доступа. Текущий безопасный режим: `simulated_no_write`.

## 9. Локальные проверки перед передачей beta

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m compileall src
node --check src/ad_mcp/web/static/app.js
.\.venv\Scripts\python.exe scripts\smoke_mcp_beta.py
```

Если системный `node` недоступен, используйте любой установленный Node.js 18+ или bundled Node из Codex runtime.

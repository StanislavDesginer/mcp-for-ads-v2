# Hosted connection store

Этот слой связывает dashboard/OAuth-подключения с MCP tools.

## Runtime source order

MCP и web diagnostics читают рекламные подключения в таком порядке:

1. `tokens/connections.json` - основной hosted store для dashboard/OAuth.
2. `ads_config.yaml` - временный fallback для разработки и bootstrap.
3. `ads_config.example.yaml` - пример, если локального файла нет.

Fallback можно отключить:

```dotenv
AD_MCP_CONNECTIONS_FALLBACK_TO_LOCAL=false
```

Для production после подключения OAuth лучше держать fallback выключенным, чтобы MCP работал только с dashboard connections.

## Где хранится hosted store

По умолчанию:

```dotenv
AD_MCP_CONNECTION_STORE_PATH=tokens/connections.json
```

Папка `tokens/` игнорируется Git, поэтому OAuth tokens и refresh tokens не попадают в репозиторий.

## Формат

Упрощенный пример:

```json
{
  "version": 1,
  "connections": {
    "meta_ads": {
      "provider": "meta_ads",
      "source": "dashboard_oauth",
      "accounts": [
        {
          "name": "Client Meta",
          "account_id": "1234567890",
          "status": "connected",
          "credentials": {
            "app_id": "meta-app-id",
            "app_secret": "meta-app-secret",
            "access_token": "meta-access-token"
          }
        }
      ]
    }
  }
}
```

Dashboard/API responses возвращают только safe account summary и не показывают `credentials`.

## Bootstrap из локального ads_config.yaml

Для внутренней beta можно перенести локальный provider config в hosted store:

```bash
curl -X POST https://mcp.adforge.example/api/hosted/connections/import-local \
  -H "Authorization: Bearer <beta-token>" \
  -H "Content-Type: application/json" \
  -d "{\"provider\":\"meta_ads\"}"
```

Ответ не содержит секреты. Секреты сохраняются только в ignored `tokens/connections.json`.

## Проверка

```bash
python scripts/smoke_mcp_beta.py
```

В блоке diagnostics видно:

```json
"provider_sources": {
  "meta_ads": "hosted_connection_store"
}
```

Если store пустой и fallback включен, источник будет `local_connections_config` или `local_connections_example`.

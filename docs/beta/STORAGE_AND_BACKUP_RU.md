# Storage and backup

В beta AdForge MCP хранит OAuth-подключения в JSON storage:

```text
tokens/connections.json
```

Путь задается через:

```dotenv
AD_MCP_CONNECTION_STORE_PATH=tokens/connections.json
```

## Что хранится

- OAuth access/refresh tokens.
- Выбранные рекламные аккаунты.
- Pending account selections.
- Safe metadata аккаунтов.

Этот файл содержит секреты и не должен попадать в Git, чат, публичные logs или клиентские инструкции.

## Права доступа

```bash
sudo chown -R adforge:adforge /opt/adforge-mcp/tokens
sudo chmod 700 /opt/adforge-mcp/tokens
sudo chmod 600 /opt/adforge-mcp/tokens/connections.json
```

Если файла еще нет, приложение создаст его при первом OAuth save.

## Backup

```bash
sudo install -d -m 700 -o adforge -g adforge /opt/adforge-mcp/backups
sudo -u adforge cp /opt/adforge-mcp/tokens/connections.json \
  /opt/adforge-mcp/backups/connections-$(date +%Y%m%d-%H%M%S).json
```

Рекомендуется хранить backups в защищенном месте и ограничить доступ только оператору проекта.

## Restore

1. Остановить сервисы:

```bash
sudo systemctl stop adforge-mcp-web adforge-mcp-http
```

2. Восстановить файл:

```bash
sudo -u adforge cp /opt/adforge-mcp/backups/connections-YYYYMMDD-HHMMSS.json \
  /opt/adforge-mcp/tokens/connections.json
sudo chmod 600 /opt/adforge-mcp/tokens/connections.json
```

3. Запустить сервисы:

```bash
sudo systemctl start adforge-mcp-web adforge-mcp-http
```

4. Проверить:

```bash
curl -H "Authorization: Bearer <BETA_TOKEN>" https://your-domain.com/api/diagnostics/connections
```

## Почему JSON storage только для beta

JSON storage удобен для быстрого MVP, но не решает production-требования:

- tenant isolation;
- encryption at rest;
- token rotation;
- per-user access control;
- audit trail для token operations;
- concurrent writes под большой нагрузкой.

Для production нужен encrypted DB-backed storage и user isolation.

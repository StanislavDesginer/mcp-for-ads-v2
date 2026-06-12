# Подключение hosted AdForge MCP в Codex

Эта инструкция описывает beta-сценарий. Сервер уже развернут на VPS/WPS. Пользователь не скачивает GitHub-репозиторий и не запускает MCP локально.

## Что нужно заранее

- Dashboard URL.
- Hosted MCP URL, например `https://your-domain.com/mcp`.
- Beta token.
- Подключенные рекламные аккаунты в dashboard.

## Шаги в Codex

1. Открыть настройки Codex.
2. Найти раздел MCP.
3. Нажать `Add server` или аналогичную кнопку добавления MCP server.
4. Указать имя: `AdForge MCP`.
5. Выбрать HTTP/Streamable HTTP transport, если интерфейс клиента дает выбор.
6. Указать URL hosted endpoint: `https://your-domain.com/mcp`.
7. Передать beta token как bearer header:

```http
Authorization: Bearer <BETA_TOKEN>
```

8. Сохранить сервер.
9. Проверить, что tools AdForge MCP появились в списке.

UI Codex может меняться. Важны не названия кнопок, а параметры подключения: server name, hosted MCP endpoint и auth/beta token.

## Пример config

Смотрите [mcp.example.json](mcp.example.json). В нем нет реальных секретов.

```json
{
  "mcpServers": {
    "adforge-mcp": {
      "transport": "streamable_http",
      "url": "https://your-domain.com/mcp",
      "headers": {
        "Authorization": "Bearer <BETA_TOKEN>"
      }
    }
  }
}
```

## Тестовые запросы

- `Проверь диагностику AdForge MCP`.
- `Покажи подключенные рекламные платформы`.
- `Покажи список рекламных аккаунтов`.
- `Покажи кампании Meta Ads`.
- `Покажи базовые метрики за последние 7 дней`.
- `Сделай preview изменения бюджета кампании, но не применяй его`.

## Если Codex не видит tools

Проверьте:

- MCP URL скопирован из dashboard без лишних пробелов;
- beta token передан через `Authorization: Bearer ...`;
- dashboard показывает `MCP ready`;
- endpoint `/api/diagnostics/mcp` доступен через dashboard API;
- hosted MCP process запущен на сервере.

# Gemini и другие MCP clients

Этот документ описывает общий принцип подключения AdForge MCP в Gemini или другой MCP-compatible клиент. Конкретный UI клиента может отличаться.

## Главный принцип

AdForge MCP уже развернут как hosted service. Пользователь подключает внешний MCP endpoint, а рекламные аккаунты подключает отдельно через AdForge dashboard.

Не нужно:

- скачивать GitHub-репозиторий;
- запускать MCP server локально;
- передавать клиенту `.env`;
- вручную копировать provider access tokens.

## Что нужно клиенту

- Name: `AdForge MCP`.
- URL: `https://your-domain.com/mcp`.
- Auth header:

```http
Authorization: Bearer <BETA_TOKEN>
```

## Универсальный пример

```json
{
  "name": "AdForge MCP",
  "url": "https://your-domain.com/mcp",
  "headers": {
    "Authorization": "Bearer <BETA_TOKEN>"
  }
}
```

Если клиент поддерживает `mcpServers`, можно использовать [mcp.example.json](mcp.example.json).

## Порядок проверки

1. В dashboard подключить рекламные аккаунты через OAuth.
2. Убедиться, что Connections показывает `MCP ready`.
3. Добавить hosted MCP URL в клиент.
4. Передать beta token безопасным способом, который поддерживает клиент.
5. Проверить появление tools.
6. Запустить диагностику: `Проверь AdForge MCP`.
7. Запросить аккаунты: `Покажи подключенные рекламные аккаунты`.

## Ограничения

- Возможности конкретного MCP-клиента могут отличаться.
- Если клиент не поддерживает custom headers, потребуется adapter/proxy или другой supported auth способ.
- Рекламные аккаунты подключаются только через AdForge dashboard, не внутри Gemini/Codex/Claude.
- Dangerous actions остаются preview-only.

# Как подключать AdForge MCP

AdForge MCP в beta работает как hosted service. Клиентский onboarding идет через dashboard/OAuth и hosted MCP endpoint, а не через локальные файлы.

## Для beta-клиента

Клиент получает:

- dashboard URL;
- hosted MCP URL;
- beta token.

Дальше клиент:

1. Открывает dashboard.
2. Заходит в `Connections`.
3. Подключает рекламные платформы через OAuth.
4. Выбирает рекламные аккаунты.
5. Копирует MCP URL.
6. Добавляет AdForge MCP в Codex, Claude или другой MCP-клиент.

Подробно:

- [docs/beta/DASHBOARD_CONNECTIONS_RU.md](docs/beta/DASHBOARD_CONNECTIONS_RU.md);
- [docs/beta/CODEX_MCP_SETUP_RU.md](docs/beta/CODEX_MCP_SETUP_RU.md);
- [docs/beta/CLAUDE_CONNECTOR_SETUP_RU.md](docs/beta/CLAUDE_CONNECTOR_SETUP_RU.md);
- [docs/beta/OTHER_MCP_CLIENTS_RU.md](docs/beta/OTHER_MCP_CLIENTS_RU.md).

## Для разработчика и сервера

Runtime-файлы:

- `.env`;
- `ads_config.yaml`, если нужен local fallback/bootstrap;
- `tokens/connections.json`, который создается OAuth storage.

Эти файлы должны лежать только локально или на сервере и не должны коммититься.

Примеры:

- [.env.example](.env.example);
- [ads_config.example.yaml](ads_config.example.yaml).

## Provider data

Для hosted OAuth на сервере нужны env variables из [.env.example](.env.example):

- Meta Ads OAuth app id/secret;
- Google OAuth client id/secret и Google Ads developer token;
- TikTok app id/secret;
- Yandex OAuth client id/secret;
- `AD_MCP_PUBLIC_BASE_URL`;
- `AD_MCP_WEB_API_TOKEN`;
- redirect path для каждого provider.

Клиент не получает provider secrets. Он проходит OAuth в dashboard.

## Security

- Не коммитить `.env`.
- Не коммитить `ads_config.yaml`.
- Не коммитить `tokens/connections.json`.
- Не раскрывать access/refresh tokens.
- Не раскрывать client/app/developer secrets.
- Dangerous actions в beta остаются preview-only.

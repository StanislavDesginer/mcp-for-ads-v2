# Быстрый чеклист AdForge MCP

Этот файл больше не описывает клиентский сценарий “склонировать GitHub и запустить локально”. Beta-модель AdForge MCP - hosted service на нашем VPS/WPS.

## Для beta-клиента

1. Получить dashboard URL, hosted MCP URL и beta token.
2. Открыть dashboard.
3. Перейти в `Connections`.
4. Подключить рекламные кабинеты через OAuth.
5. Выбрать рекламные аккаунты.
6. Запустить диагностику.
7. Скопировать MCP URL.
8. Добавить AdForge MCP в Codex, Claude или другой MCP-клиент.
9. Проверить запросом: `Проверь диагностику AdForge MCP`.

Подробный чеклист demo: [docs/beta/BETA_DEMO_CHECKLIST_RU.md](docs/beta/BETA_DEMO_CHECKLIST_RU.md).

## Для разработчика

Локальная установка и запуск нужны только для разработки, тестов и обслуживания сервера. Используйте:

- [README.md](README.md#developer-setup);
- [TESTING.md](TESTING.md);
- [DEPLOYING.md](DEPLOYING.md).

Не коммитьте `.env`, `ads_config.yaml`, `tokens/connections.json` или реальные provider secrets.

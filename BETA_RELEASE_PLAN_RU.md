# Beta release plan

Цель до конца июня: довести `mcp-for-ads` до бета-состояния, где внешний человек может поднять MCP, подключить рекламный кабинет по инструкции, проверить диагностику и безопасно работать через GPT, Claude, Codex или другой MCP-клиент.

## Принципы беты

- Meta и Google идут в первую бету.
- Yandex Direct и TikTok Ads остаются позже, без блокировки релиза.
- Все write-действия остаются в режиме `preview -> confirm`.
- Секреты не хранятся в Git.
- Любой новый кабинет подключается через понятный onboarding: `.env`, `ads_config.yaml`, диагностика, smoke-check.
- MCP-native skills важнее отдельного чат-слоя в web UI.

## Этап 0: security gate

Срок: 9-11 июня.

- Убрать `.env` и `ads_config.yaml` из Git tracking.
- Перевыпустить засвеченные токены после стабилизации конфига.
- Закрыть web `/api/*` простым beta-auth или сетевым ограничением.
- Не отдавать raw exceptions наружу.
- Проверить, что diagnostics не раскрывают секреты и лишние пути.

Definition of done:
- `git status` не показывает секретные файлы как tracked changes.
- Web API не доступен без beta credentials или ограниченного контура.
- Ошибки в UI человекочитаемые и безопасные.

## Этап 1: MCP beta packaging

Срок: 12-16 июня.

- Проверить MCP server entrypoint для Codex/Claude/GPT-compatible клиентов.
- Подготовить минимальный `mcp.json` пример подключения.
- Описать поддерживаемые tools/skills и их safe-mode поведение.
- Добавить smoke command, который проверяет загрузку server/tools без живого write.

Definition of done:
- Новый пользователь может подключить MCP локально по инструкции.
- Есть проверка `server starts -> tools listed -> diagnostics ok`.

## Этап 2: account onboarding

Срок: 17-20 июня.

- Сделать пошаговый `CONNECTING_BETA_RU.md` для Meta и Google Ads.
- Добавить template-конфиг без секретов.
- Сделать понятную диагностику: missing env, invalid account, expired token, permission denied.
- Для Google Ads добавить первый live-read smoke-test.

Definition of done:
- Человек без участия разработчика понимает, какие данные нужны и куда их положить.
- Ошибка подключения объясняет, что именно исправить.

## Этап 3: reliability test pack

Срок: 21-24 июня.

- Зафиксировать unit/integration smoke matrix.
- Добавить проверки web UI: health, workspace, diagnostics, preview forms.
- Добавить MCP checks: tool registration, read report, skill preset, preview mutation.
- Проверить graceful degradation при rate limit и permission errors.

Definition of done:
- Есть одна команда или короткая последовательность команд для beta regression run.
- Meta rate limits не валят весь workspace.

## Этап 4: VPS beta deploy

Срок: 25-27 июня.

- Деплой на существующий VPS.
- Проверка systemd service, nginx, healthz, logs.
- Проверка live Meta кабинетов.
- Проверка Google Ads кабинета.
- Проверка beta-auth/ограничений.

Definition of done:
- Сервер работает после restart.
- Smoke-test проходит с VPS.
- В логах нет секретов.

## Этап 5: beta handoff

Срок: 28-30 июня.

- Финальная инструкция для пользователя.
- Чеклист подключения MCP-клиента.
- Чеклист подключения рекламного кабинета.
- Known limitations: Yandex/TikTok позже, write только preview.
- GitHub release/tag beta.

Definition of done:
- Можно дать человеку ссылку на репозиторий и инструкцию.
- Он сможет поднять MCP, подключить кабинет, проверить диагностику и выполнить безопасные preview-сценарии.

## Первый рабочий фокус

Начинаем с security gate, потому что без него любой следующий deploy рискует случайно утащить реальные токены в Git или наружу через diagnostics.

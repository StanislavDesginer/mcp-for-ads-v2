# mcp-for-ads

MCP-сервер для работы с рекламными кабинетами `Meta Ads`, `Google Ads`, `TikTok Ads` и `Yandex Direct`.

Сейчас проект в первую очередь решает такие задачи:
- единый слой read-инструментов по рекламным платформам
- безопасные сценарии `preview -> confirm` для write-операций
- веб-панель оператора под `Meta Ads`
- безопасный режим без реальных изменений по умолчанию

## Текущий статус

Что уже работает:
- локальный MCP stdio-сервер запускается
- live-read путь для `Meta Ads` реализован
- каркас для `Google Ads` уже есть и ждёт credentials
- `TikTok Ads` и `Yandex Direct` пока остаются в безопасном preview-режиме
- есть внутренняя веб-панель оператора для `Meta Ads`

Что пока намеренно ограничено:
- реальные изменения в кабинетах не включены по умолчанию
- политика безопасности держит проект в режиме `simulated_no_write`
- production auth, мультиарендность, биллинг и клиентская изоляция ещё не завершены

## Структура репозитория

- [src/ad_mcp](src/ad_mcp) - основной код приложения
- [config/policies/safety.example.yaml](config/policies/safety.example.yaml) - безопасная политика по умолчанию
- [ads_config.example.yaml](ads_config.example.yaml) - пример конфига подключений провайдеров
- [CONNECTING.md](CONNECTING.md) - как подключать кабинеты и секреты
- [TESTING.md](TESTING.md) - как тестировать проект локально и через hosted UI
- [DEPLOYING.md](DEPLOYING.md) - как разворачивать проект на сервере
- [CHECKLIST_RU.md](CHECKLIST_RU.md) - простой пошаговый чеклист для коллеги без техподготовки
- [CREATIVE_BRIEF_RU.md](CREATIVE_BRIEF_RU.md) - внутренний справочный файл

## Локальный запуск

### Windows

```powershell
cd "<путь-к-проекту>\\mcp-for-ads"
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev,google,meta]"
```

### Linux

```bash
cd /opt/mcp-for-ads
python3.11 -m venv .venv
./.venv/bin/python -m pip install -e ".[dev,google,meta]"
```

## Локальные рабочие файлы

Проект читает `.env` из корня репозитория и подставляет переменные внутрь `ads_config.yaml`.

Что нужно сделать:
- взять [.env.example](.env.example)
- создать локальный `.env`
- взять [ads_config.example.yaml](ads_config.example.yaml)
- создать локальный `ads_config.yaml`

Важно:
- `.env` хранить только локально
- `ads_config.yaml` хранить только локально
- не коммитить в Git реальные токены, app secrets и refresh tokens

## Запуск MCP-сервера

```powershell
cd "<путь-к-проекту>\\mcp-for-ads"
.\.venv\Scripts\python.exe -m ad_mcp.server
```

или:

```powershell
ad-mcp-server
```

Важно:
сервер рассчитан на запуск через MCP-клиент, например `Codex`, а не на ручной ввод команд в интерактивной консоли.

## Запуск веб-панели Meta

Значения по умолчанию:
- host: `127.0.0.1`
- port: `8765`

При необходимости переопределяются переменными:
- `AD_MCP_WEB_HOST`
- `AD_MCP_WEB_PORT`

Локальный запуск:

```powershell
cd "<путь-к-проекту>\\mcp-for-ads"
.\.venv\Scripts\python.exe -m ad_mcp.web.server
```

После запуска открыть:
- [http://127.0.0.1:8765](http://127.0.0.1:8765)

Проверка health:
- [http://127.0.0.1:8765/healthz](http://127.0.0.1:8765/healthz)

## Как передавать проект тестеру

Если кто-то другой должен проверить проект, ему нужно передать:
- сам репозиторий
- локальный `.env`
- локальный `ads_config.yaml`

Дальше он может идти по:
- [TESTING.md](TESTING.md)
- [CHECKLIST_RU.md](CHECKLIST_RU.md)

## Что уже покрыто по Meta Ads

Read-инструменты, которые уже есть:
- `get_account_summary`
- `list_account_objects`
- `get_account_object`
- `get_flexible_insights`
- `get_billing_summary`
- `get_spend_overview`
- `estimate_budget_days_remaining`
- `get_connected_assets`
- `get_delivery_issues`
- `get_status_summary`
- `get_breakdown_preset`
- `rank_top_entities`
- `get_top_performers`
- `get_no_result_entities`
- `find_wasting_spend`
- `find_burnout_ads`
- `compare_periods`
- `compare_creatives`
- `detect_anomalies`
- `analyze_audiences`
- `get_executive_summary`
- `audit_account`
- `audit_links_and_utms`
- `get_campaign_structure`
- `get_policy_issues`
- `get_conversion_health`
- `get_asset_health`
- `list_creative_assets`
- `list_lead_forms`
- `get_recommendations_read`
- `list_automated_rules`
- `get_rule_history`
- `get_minimum_budgets_read`
- `get_reach_estimate_read`
- `get_tracking_specs`
- `get_launch_checklist`

Preview-инструменты для write-сценариев:
- `clone_campaign_preview`
- `clone_adset_preview`
- `clone_ad_preview`
- `update_campaign_budget_preview`
- `update_adset_budget_preview`
- `pause_entities_preview`
- `enable_entities_preview`
- `update_targeting_preview`
- `update_placements_preview`
- `replace_ad_creative_preview`
- `create_adset_in_campaign_preview`
- `create_ad_in_existing_adset_preview`
- `create_creative_preview`
- `create_audience_variant_preview`
- `create_engagement_campaign_preview`
- `create_lead_campaign_preview`
- `create_whatsapp_traffic_campaign_preview`
- `create_ab_test_ads_preview`
- `duplicate_campaign_with_geo_preview`
- `duplicate_campaign_with_audience_preview`
- `rebalance_budget_to_end_of_month_preview`
- `pause_underperformers_preview`
- `scale_best_campaigns_preview`
- `scale_winners_by_rule_preview`
- `archive_entities_preview`

## Текущие безопасные ограничения

По умолчанию проект делает вот что:
- блокирует неизвестные аккаунты
- ограничивает mutation-сценарии через [config/policies/safety.example.yaml](config/policies/safety.example.yaml)
- работает в режиме `simulated_no_write`
- пишет аудит в `logs/audit.jsonl`

Если выкладывать проект наружу, нельзя открывать preview/write endpoints без:
- контроля доступа
- reverse proxy
- IP-фильтрации или авторизации
- нормального хранения секретов

## Хостинг

Рекомендуемая база:
- Ubuntu 22.04 LTS или 24.04 LTS
- Python 3.11
- systemd
- Nginx reverse proxy
- `.env` только на сервере
- `ads_config.yaml` только на сервере

Подробный сценарий деплоя:
- [DEPLOYING.md](DEPLOYING.md)

## Тесты

```powershell
cd "<путь-к-проекту>\\mcp-for-ads"
.\.venv\Scripts\python.exe -m pytest -q
```

## Текущая безопасность проекта

Что уже хорошо:
- секреты ожидаются через переменные окружения
- в репозитории лежат только example-файлы
- локальные секретные файлы игнорируются Git
- веб-панель по умолчанию биндингится на localhost

Что ещё нужно сделать перед нормальным production:
- поставить auth перед веб-панелью
- разделить хранение секретов по клиентам
- перевыпустить токены, если они когда-либо отправлялись в чат
- со временем перейти от локального конфига к tenant-aware storage

# Как подключать mcp-for-ads

## Главные рабочие файлы

Проект использует два локальных runtime-файла:

- `ads_config.yaml`
- `.env`

Они специально не хранятся в Git с реальными секретами.

## Что нужно получить от владельца проекта

Чтобы работали реальные запросы к рекламным кабинетам, тестеру нужны:
- локальный `ads_config.yaml`
- локальный `.env`
- реальные credentials нужной платформы

Без этих файлов:
- репозиторий всё равно откроется
- тесты всё равно можно запустить
- hosted UI всё равно откроется
- но live provider calls будут падать по auth или работать на заглушках

Если тестирование идёт через Codex, нужен ещё локальный MCP-конфиг.
Для этого в репозитории есть пример:
- [.codex/config.example.toml](.codex/config.example.toml)

## Куда класть локальные файлы

Оба runtime-файла должны лежать в корне проекта:

```text
mcp-for-ads/
  .env
  ads_config.yaml
  README.md
  pyproject.toml
  src/
```

## ads_config.yaml

Подключения к рекламным платформам читаются из `ads_config.yaml`.

За основу бери:
- [ads_config.example.yaml](ads_config.example.yaml)

Пример для Meta:

```yaml
providers:
  meta_ads:
    provider: meta_ads
    accounts:
      - name: "Example Meta Account"
        account_id: "act_123456789012345"
        status: configured
        app_id: "YOUR_META_APP_ID"
        app_secret: "${META_EXAMPLE_APP_SECRET}"
        access_token: "${META_EXAMPLE_ACCESS_TOKEN}"
        api_version: "v20.0"
```

## .env

Переменные внутри `ads_config.yaml` подставляются из `.env`.

За основу бери:
- [.env.example](.env.example)

Пример:

```dotenv
AD_MCP_ENV=development
AD_MCP_LOG_LEVEL=INFO
AD_MCP_AUDIT_LOG_PATH=logs/audit.jsonl
AD_MCP_CONNECTIONS_CONFIG=ads_config.yaml
AD_MCP_POLICY_CONFIG=config/policies/safety.example.yaml
AD_MCP_WEB_HOST=127.0.0.1
AD_MCP_WEB_PORT=8765

META_EXAMPLE_APP_SECRET=your-meta-app-secret
META_EXAMPLE_ACCESS_TOKEN=your-meta-access-token
```

## Какие данные нужны по платформам

### Meta Ads

Обязательно на каждый кабинет:
- `account_id`
- `app_id`
- `app_secret`
- `access_token`

Дополнительно:
- `api_version`
- `action_metrics`
- `video_metrics`

### Google Ads

Обязательно на каждый кабинет:
- `account_id`
- `customer_id`
- `login_customer_id`
- `developer_token`
- `oauth_client_id`
- `oauth_client_secret`
- `refresh_token`

### TikTok Ads

Обязательно на каждый кабинет:
- `account_id`
- `advertiser_id`
- `app_id`
- `secret`
- `access_token`

### Yandex Direct

Обязательно на каждый кабинет:
- `account_id`
- `login`
- `access_token`

## Как проект читает конфиг

Порядок загрузки такой:

1. корневой `ads_config.yaml`
2. корневой `ads_config.example.yaml`
3. fallback на provider example-файлы из `config/providers/*.example.yaml`

Переменные внутри YAML подставляются из корневого `.env`.

## Hosted web UI

Если проект уже развернули на сервере, тестер может проверить интерфейс без локального MCP, просто открыв:
- [http://77.240.38.131](http://77.240.38.131)

Это удобно для:
- smoke test интерфейса
- диагностики
- проверки, видит ли сервер Meta аккаунты

## Важные замечания по безопасности

- неизвестные аккаунты блокируются по умолчанию
- preview/write сценарии ограничиваются [config/policies/safety.example.yaml](config/policies/safety.example.yaml)
- реальные секреты должны жить только в локальном `.env` и локальном `ads_config.yaml`

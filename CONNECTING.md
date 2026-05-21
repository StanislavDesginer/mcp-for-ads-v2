# Как подключать mcp-for-ads

## Главные рабочие файлы

Проект использует два runtime-файла:

- `ads_config.yaml`
- `.env`

Если проект клонируется из приватного командного репозитория, они уже могут лежать в корне.

Если их нет, их нужно получить отдельно у владельца проекта.

## Что нужно для реальных запросов

Чтобы работали реальные обращения к рекламным платформам, нужны:
- `ads_config.yaml`
- `.env`
- реальные credentials платформы

Без них:
- репозиторий всё равно откроется
- тесты всё равно можно запустить
- hosted UI всё равно откроется
- но live provider calls будут падать по auth или работать на заглушках

## Куда класть файлы

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

Структуру можно смотреть в:
- [ads_config.example.yaml](ads_config.example.yaml)

## .env

Переменные внутри `ads_config.yaml` подставляются из `.env`.

Пример структуры:
- [.env.example](.env.example)

## Какие данные нужны по платформам

### Meta Ads

Обязательно:
- `account_id`
- `app_id`
- `app_secret`
- `access_token`

### Google Ads

Обязательно:
- `account_id`
- `customer_id`
- `login_customer_id`
- `developer_token`
- `oauth_client_id`
- `oauth_client_secret`
- `refresh_token`

### TikTok Ads

Обязательно:
- `account_id`
- `advertiser_id`
- `app_id`
- `secret`
- `access_token`

### Yandex Direct

Обязательно:
- `account_id`
- `login`
- `access_token`

## Hosted web UI

Если проект уже развёрнут на сервере, тестер может просто открыть:
- [http://77.240.38.131](http://77.240.38.131)

Это удобно для:
- быстрого smoke test
- проверки интерфейса
- проверки диагностики
- проверки, что сервер видит Meta аккаунты

# Как тестировать проект

Этот репозиторий можно проверять в двух режимах:

1. только через уже поднятый веб-интерфейс
2. локально через Codex + MCP

## Что тестеру нужно получить от владельца проекта

Если проект клонируется из приватного командного репозитория, в нём уже могут лежать:
- `.env`
- `ads_config.yaml`

Если этих файлов нет, их нужно отдельно получить у владельца проекта.

Без них:
- проект всё равно установится
- тесты всё равно можно запустить
- hosted UI всё равно откроется
- но реальные запросы будут падать по auth или работать на placeholder-значениях

## Самый быстрый способ проверить проект

Открыть уже поднятую панель:
- [http://77.240.38.131](http://77.240.38.131)

Так можно быстро проверить:
- открывается ли Meta dashboard
- работают ли diagnostics-страницы
- грузятся ли account summaries
- не разваливается ли интерфейс

## Локальная установка для тестера

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

## Куда смотрит проект

Рабочие файлы должны лежать в корне проекта:

```text
mcp-for-ads/
  .env
  ads_config.yaml
  pyproject.toml
  src/
```

## Локальный запуск веб-панели

```powershell
cd "<путь-к-проекту>\\mcp-for-ads"
.\.venv\Scripts\python.exe -m ad_mcp.web.server
```

После запуска открыть:
- [http://127.0.0.1:8765](http://127.0.0.1:8765)
- [http://127.0.0.1:8765/healthz](http://127.0.0.1:8765/healthz)

## Локальная работа через Codex + MCP

В репозитории есть пример MCP-конфига для Codex:
- [.codex/config.example.toml](.codex/config.example.toml)

Что нужно сделать:
1. скопировать этот пример в своё место для конфигов Codex
2. заменить placeholder-путь на свой локальный путь к проекту
3. перезапустить Codex в папке проекта

## Примеры запросов в Codex

Когда MCP уже подключён, тестер может задавать такие команды:

```text
Use MCP server ads and show list_accounts for provider meta_ads.
```

```text
Use MCP server ads and call get_account_summary for provider meta_ads and account_id act_1746501262698286.
```

```text
Use MCP server ads and call find_wasting_spend for provider meta_ads, account_id act_1746501262698286, start_date 2026-04-01, end_date 2026-05-21.
```

## Что тестер может проверить

- проект ставится без развала
- MCP server запускается
- Meta accounts подхватываются из локального конфига
- web UI открывается
- diagnostics endpoints отвечают
- read-tools возвращают реальные Meta данные
- preview write tools возвращают safe preview payloads

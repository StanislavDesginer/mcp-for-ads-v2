# Самый простой чеклист

Этот файл нужен для человека, который не хочет разбираться в проекте глубоко и хочет просто запустить всё у себя.

## 1. Создай пустую папку

Например:

```text
C:\Projects\AdForge-MCP
```

## 2. Открой эту папку в Codex

Открывать нужно именно пустую папку, в которую потом клонируется проект.

## 3. Открой встроенную консоль в Codex

Дальше все команды вводятся прямо там.

## 4. Клонируй репозиторий

```powershell
git clone git@github.com:mcpforge-dev/AdForge-MCP.git .
```

Важно:
- точка в конце обязательна
- она значит “клонировать прямо в текущую папку”

## 5. Создай виртуальное окружение

```powershell
py -3.11 -m venv .venv
```

## 6. Установи зависимости

```powershell
.\.venv\Scripts\python.exe -m pip install -e ".[dev,google,meta]"
```

## 7. Проверь, что в папке уже есть рабочие файлы

После `git clone` в проекте уже должны лежать:
- `.env`
- `ads_config.yaml`

Если они есть, отдельно добавлять их не нужно.

## 8. Запусти веб-интерфейс

```powershell
.\.venv\Scripts\python.exe -m ad_mcp.web.server
```

## 9. Открой сайт

В браузере открой:

```text
http://127.0.0.1:8765
```

## 10. Если нужно проверить через Codex + MCP

Используй пример конфига:
- [.codex/config.example.toml](.codex/config.example.toml)

Потом можно писать в Codex такие команды:

```text
Use MCP server adforge and show list_accounts for provider meta_ads.
```

```text
Use MCP server adforge and call get_account_summary for provider meta_ads and account_id act_1746501262698286.
```

```text
Use MCP server adforge and call find_wasting_spend for provider meta_ads, account_id act_1746501262698286, start_date 2026-04-01, end_date 2026-05-21.
```

## Если что-то не работает

Проверь только это:
1. установлен ли Python 3.11
2. установлен ли Git
3. отработала ли команда установки зависимостей
4. открывается ли `http://127.0.0.1:8765`

Если эти 4 пункта ок, значит проект в целом поднялся.

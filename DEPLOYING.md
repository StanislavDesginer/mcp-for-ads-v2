# Развёртывание AdForge MCP

Этот проект уже можно размещать для внутренней команды, но это ещё не публичный SaaS для множества клиентов.

## Куда лучше разворачивать

Рекомендуемая база:
- Ubuntu 22.04 LTS или Ubuntu 24.04 LTS
- Python 3.11
- Nginx
- systemd
- VPS или приватный сервер

## Что уже можно хостить

Безопасно размещать уже сейчас:
- MCP-сервер для доверенных внутренних клиентов
- веб-панель Meta для внутренней работы команды

Пока не готово для анонимного публичного доступа:
- preview/write endpoints без auth
- многоарендное размещение для разных клиентов без изоляции
- открытый интернет-доступ без reverse proxy и контроля доступа

## Рекомендуемая структура на сервере

Папка приложения:

```bash
/opt/adforge-mcp
```

Рабочие файлы:
- `/opt/adforge-mcp/.env`
- `/opt/adforge-mcp/ads_config.yaml`
- `/opt/adforge-mcp/logs/audit.jsonl`

## Первичная установка

```bash
sudo apt update
sudo apt install -y python3.11 python3.11-venv nginx
sudo mkdir -p /opt/adforge-mcp
sudo chown -R $USER:$USER /opt/adforge-mcp
```

После этого скопируй репозиторий в `/opt/adforge-mcp`, а затем:

```bash
cd /opt/adforge-mcp
python3.11 -m venv .venv
./.venv/bin/python -m pip install -e ".[dev,google,meta]"
```

## Настройка окружения

Создай `.env` на основе `.env.example` и заполни его реальными значениями.

Рекомендуемые production-переменные:

```dotenv
AD_MCP_ENV=production
AD_MCP_LOG_LEVEL=INFO
AD_MCP_AUDIT_LOG_PATH=logs/audit.jsonl
AD_MCP_CONNECTIONS_CONFIG=ads_config.yaml
AD_MCP_POLICY_CONFIG=config/policies/safety.example.yaml
AD_MCP_WEB_HOST=127.0.0.1
AD_MCP_WEB_PORT=8765
```

Важно:
- `.env` хранить только на сервере
- `ads_config.yaml` хранить только на сервере

## Ручной запуск веб-панели

```bash
cd /opt/adforge-mcp
./.venv/bin/python -m ad_mcp.web.server
```

Проверка health:

```bash
curl http://127.0.0.1:8765/healthz
```

## Пример systemd-сервиса

Создать файл:

```bash
/etc/systemd/system/adforge-mcp-web.service
```

Пример:

```ini
[Unit]
Description=AdForge MCP web UI
After=network.target

[Service]
Type=simple
WorkingDirectory=/opt/adforge-mcp
EnvironmentFile=/opt/adforge-mcp/.env
ExecStart=/opt/adforge-mcp/.venv/bin/python -m ad_mcp.web.server
Restart=always
RestartSec=5
User=www-data
Group=www-data

[Install]
WantedBy=multi-user.target
```

После создания:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now adforge-mcp-web
sudo systemctl status adforge-mcp-web
```

## Пример Nginx reverse proxy

Создать файл:

```bash
/etc/nginx/sites-available/adforge-mcp
```

Пример:

```nginx
server {
    listen 80;
    server_name your-domain.example;

    location / {
        proxy_pass http://127.0.0.1:8765;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

После этого:

```bash
sudo ln -s /etc/nginx/sites-available/adforge-mcp /etc/nginx/sites-enabled/adforge-mcp
sudo nginx -t
sudo systemctl reload nginx
```

## Минимальный чеклист безопасности

Перед открытием проекта наружу нужно хотя бы:
- включить firewall
- оставить веб-приложение на `127.0.0.1`
- публиковать его только через Nginx
- добавить basic auth, VPN или IP allowlist
- не хранить секреты в Git
- перевыпустить токены, если они когда-либо были в переписке
- следить за `logs/audit.jsonl`

## Практический текущий режим

На сегодня лучший режим использования:
- внутренняя панель оператора
- внутренний MCP-сервер
- ограниченный доступ
- без реальных write-операций, пока не завершены auth controls и live write paths

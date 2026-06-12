# VPS/WPS deployment для hosted beta

Этот документ описывает production-like beta запуск AdForge MCP на VPS/WPS. GitHub clone и настройку сервера делает оператор/разработчик проекта. Beta-клиент не скачивает репозиторий и не запускает MCP локально.

## Архитектура beta deployment

- Web dashboard/API: `127.0.0.1:8765`.
- Hosted MCP transport: `127.0.0.1:8766/mcp`.
- Reverse proxy: Nginx или Caddy на публичном домене.
- HTTPS: Let's Encrypt.
- Runtime secrets: только в `.env` на сервере.
- OAuth connection storage: `tokens/connections.json`.
- Safety: `AD_MCP_PREVIEW_ONLY=true`.

## Требования к серверу

- Ubuntu 22.04 LTS или 24.04 LTS.
- Python 3.11+.
- Git.
- Nginx или Caddy.
- systemd.
- Домен, направленный на IP сервера.
- Доступ по SSH для оператора проекта.

Node.js на VPS не нужен для runtime. Он нужен только разработчику, если на сервере дополнительно запускается `node --check` для dashboard JS.

## Установка пакетов

```bash
sudo apt update
sudo apt install -y git python3.11 python3.11-venv nginx certbot python3-certbot-nginx
```

## Пользователь сервиса

```bash
sudo useradd --system --create-home --home-dir /opt/adforge-mcp --shell /usr/sbin/nologin adforge
sudo mkdir -p /opt/adforge-mcp
sudo chown -R adforge:adforge /opt/adforge-mcp
```

## Клонирование репозитория

Клонирование выполняет оператор проекта на сервере:

```bash
sudo -u adforge git clone git@github.com:mcpforge-dev/AdForge-MCP.git /opt/adforge-mcp
```

Это не клиентский onboarding. Клиент получает только dashboard URL, MCP URL и beta token.

## Python environment

```bash
cd /opt/adforge-mcp
sudo -u adforge python3.11 -m venv .venv
sudo -u adforge ./.venv/bin/python -m pip install --upgrade pip
sudo -u adforge ./.venv/bin/python -m pip install -e ".[google,meta]"
```

## Runtime directories

```bash
sudo -u adforge mkdir -p /opt/adforge-mcp/tokens /opt/adforge-mcp/logs
sudo chmod 700 /opt/adforge-mcp/tokens
```

## Настройка `.env`

```bash
sudo -u adforge cp /opt/adforge-mcp/.env.example /opt/adforge-mcp/.env
sudo -u adforge nano /opt/adforge-mcp/.env
```

Минимальный production-like beta набор:

```dotenv
AD_MCP_ENV=production
AD_MCP_LOG_LEVEL=INFO
AD_MCP_WEB_HOST=127.0.0.1
AD_MCP_WEB_PORT=8765
AD_MCP_MCP_HTTP_HOST=127.0.0.1
AD_MCP_MCP_HTTP_PORT=8766
AD_MCP_MCP_ENDPOINT_PATH=/mcp
AD_MCP_PUBLIC_BASE_URL=https://your-domain.com
AD_MCP_WEB_API_TOKEN=replace-with-strong-beta-token
AD_MCP_PREVIEW_ONLY=true
AD_MCP_CONNECTION_STORE_PATH=tokens/connections.json
AD_MCP_CONNECTIONS_FALLBACK_TO_LOCAL=false
```

OAuth env variables описаны в [ENVIRONMENT_RU.md](ENVIRONMENT_RU.md).

## Systemd запуск

Скопировать примеры:

```bash
sudo cp /opt/adforge-mcp/deploy/adforge-mcp-web.service.example /etc/systemd/system/adforge-mcp-web.service
sudo cp /opt/adforge-mcp/deploy/adforge-mcp-http.service.example /etc/systemd/system/adforge-mcp-http.service
sudo systemctl daemon-reload
sudo systemctl enable --now adforge-mcp-web adforge-mcp-http
```

Проверка:

```bash
sudo systemctl status adforge-mcp-web
sudo systemctl status adforge-mcp-http
```

## Reverse proxy и HTTPS

См. [REVERSE_PROXY_RU.md](REVERSE_PROXY_RU.md).

Коротко:

```bash
sudo cp /opt/adforge-mcp/deploy/nginx.adforge-mcp.example.conf /etc/nginx/sites-available/adforge-mcp
sudo nano /etc/nginx/sites-available/adforge-mcp
sudo ln -s /etc/nginx/sites-available/adforge-mcp /etc/nginx/sites-enabled/adforge-mcp
sudo nginx -t
sudo systemctl reload nginx
sudo certbot --nginx -d your-domain.com
```

## Проверка после запуска

```bash
curl https://your-domain.com/health
curl https://your-domain.com/ready
curl -i https://your-domain.com/api/diagnostics
curl -H "Authorization: Bearer <BETA_TOKEN>" https://your-domain.com/api/diagnostics
curl -H "Authorization: Bearer <BETA_TOKEN>" https://your-domain.com/api/diagnostics/mcp
```

Запрос без token должен получить `401` или `503`, если token не настроен. Запрос с token должен вернуть JSON diagnostics.

## Smoke script

```bash
cd /opt/adforge-mcp
sudo -u adforge ./.venv/bin/python scripts/smoke_hosted_beta.py \
  --base-url https://your-domain.com \
  --token "<BETA_TOKEN>"
```

Live provider checks отдельно:

```bash
sudo -u adforge ./.venv/bin/python scripts/smoke_hosted_beta.py \
  --base-url https://your-domain.com \
  --token "<BETA_TOKEN>" \
  --live
```

`--live` делает только read-checks. Write/apply не вызываются.

## Dashboard check

1. Открыть `https://your-domain.com`.
2. Ввести beta token.
3. Перейти в `Connections`.
4. Проверить hosted MCP URL.
5. Запустить diagnostics.

## MCP endpoint check

В MCP-клиенте использовать:

- URL: `https://your-domain.com/mcp`;
- header: `Authorization: Bearer <BETA_TOKEN>`.

## Preview-only check

Проверить:

```bash
curl -H "Authorization: Bearer <BETA_TOKEN>" https://your-domain.com/ready
```

В ответе должно быть:

```json
"preview_only": {"enabled": true}
```

Также через MCP preview tools должны возвращать `will_apply=false`.

## Logs

```bash
sudo journalctl -u adforge-mcp-web -f
sudo journalctl -u adforge-mcp-http -f
```

Raw access/refresh tokens, client secrets и developer tokens не должны попадать в logs.

## Backup

См. [STORAGE_AND_BACKUP_RU.md](STORAGE_AND_BACKUP_RU.md).

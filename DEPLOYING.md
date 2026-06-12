# Развёртывание AdForge MCP

Актуальная beta-модель: AdForge MCP разворачивает оператор/разработчик проекта на VPS/WPS как hosted service. Beta-клиент не скачивает GitHub-репозиторий и не запускает MCP локально.

Основная инструкция для production-like beta:

- [docs/beta/VPS_DEPLOYMENT_RU.md](docs/beta/VPS_DEPLOYMENT_RU.md)

Связанные документы:

- [docs/beta/ENVIRONMENT_RU.md](docs/beta/ENVIRONMENT_RU.md) - env variables.
- [docs/beta/REVERSE_PROXY_RU.md](docs/beta/REVERSE_PROXY_RU.md) - Nginx/Caddy и HTTPS.
- [docs/beta/SYSTEMD_SERVICE_RU.md](docs/beta/SYSTEMD_SERVICE_RU.md) - systemd units.
- [docs/beta/STORAGE_AND_BACKUP_RU.md](docs/beta/STORAGE_AND_BACKUP_RU.md) - storage, backup, restore.
- [docs/beta/BETA_DEMO_CHECKLIST_RU.md](docs/beta/BETA_DEMO_CHECKLIST_RU.md) - проверка beta-demo.

Коротко:

```bash
cd /opt/adforge-mcp
./.venv/bin/python -m pip install -e ".[google,meta]"
sudo systemctl enable --now adforge-mcp-web adforge-mcp-http
curl https://your-domain.com/health
curl https://your-domain.com/ready
```

Web dashboard/API слушает `127.0.0.1:8765`, hosted MCP transport слушает `127.0.0.1:8766/mcp`, публичный доступ идет через reverse proxy и HTTPS.

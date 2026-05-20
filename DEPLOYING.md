# Deploying mcp-for-ads

This project can be hosted for internal operator use today, but it is not yet a public multi-tenant SaaS.

## Recommended target

- Ubuntu 22.04 LTS or Ubuntu 24.04 LTS
- Python 3.11
- Nginx
- systemd
- private server or VPS

## What to host right now

Safe to host now:
- MCP server for trusted internal clients
- Meta web UI for internal operator usage

Not ready for public anonymous access:
- preview/write endpoints without auth
- multi-client shared deployment without tenant isolation
- public internet exposure without reverse proxy and access control

## Server layout

Suggested application path:

```bash
/opt/mcp-for-ads
```

Suggested runtime files:
- `/opt/mcp-for-ads/.env`
- `/opt/mcp-for-ads/ads_config.yaml`
- `/opt/mcp-for-ads/logs/audit.jsonl`

## Initial install

```bash
sudo apt update
sudo apt install -y python3.11 python3.11-venv nginx
sudo mkdir -p /opt/mcp-for-ads
sudo chown -R $USER:$USER /opt/mcp-for-ads
```

Copy the repository contents into `/opt/mcp-for-ads`, then:

```bash
cd /opt/mcp-for-ads
python3.11 -m venv .venv
./.venv/bin/python -m pip install -e ".[dev,google,meta]"
```

## Environment setup

Create `.env` from `.env.example` and fill in real values.

Recommended production values:

```dotenv
AD_MCP_ENV=production
AD_MCP_LOG_LEVEL=INFO
AD_MCP_AUDIT_LOG_PATH=logs/audit.jsonl
AD_MCP_CONNECTIONS_CONFIG=ads_config.yaml
AD_MCP_POLICY_CONFIG=config/policies/safety.example.yaml
AD_MCP_WEB_HOST=127.0.0.1
AD_MCP_WEB_PORT=8765
```

Keep:
- `.env` server-only
- `ads_config.yaml` server-only

## Run the web UI manually

```bash
cd /opt/mcp-for-ads
./.venv/bin/python -m ad_mcp.web.server
```

Health endpoint:

```bash
curl http://127.0.0.1:8765/healthz
```

## systemd service example

Create:

```bash
/etc/systemd/system/mcp-for-ads-web.service
```

Example:

```ini
[Unit]
Description=mcp-for-ads web UI
After=network.target

[Service]
Type=simple
WorkingDirectory=/opt/mcp-for-ads
EnvironmentFile=/opt/mcp-for-ads/.env
ExecStart=/opt/mcp-for-ads/.venv/bin/python -m ad_mcp.web.server
Restart=always
RestartSec=5
User=www-data
Group=www-data

[Install]
WantedBy=multi-user.target
```

Then:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now mcp-for-ads-web
sudo systemctl status mcp-for-ads-web
```

## Nginx reverse proxy example

Create:

```bash
/etc/nginx/sites-available/mcp-for-ads
```

Example:

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

Then:

```bash
sudo ln -s /etc/nginx/sites-available/mcp-for-ads /etc/nginx/sites-enabled/mcp-for-ads
sudo nginx -t
sudo systemctl reload nginx
```

## Security checklist

Before public hosting, do at least this:
- use firewall rules
- keep web app bound to `127.0.0.1`
- expose only through Nginx
- add basic auth, VPN, or IP allowlisting
- keep secrets out of Git
- rotate any tokens that were ever pasted into chat
- monitor `logs/audit.jsonl`

## Current practical recommendation

Best current deployment mode:
- internal operator dashboard
- internal MCP server
- restricted access
- no real writes until provider write paths and auth controls are finished

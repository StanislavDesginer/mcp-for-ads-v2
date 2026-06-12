# Reverse proxy и HTTPS

AdForge MCP beta публикуется через reverse proxy. Web dashboard и MCP transport должны слушать только localhost.

## Recommended internal routing

- Dashboard/API: `http://127.0.0.1:8765`.
- MCP transport: `http://127.0.0.1:8766/mcp`.
- Public URL: `https://your-domain.com`.

## Nginx example

В репозитории есть пример:

```text
deploy/nginx.adforge-mcp.example.conf
```

Минимальная схема:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    client_max_body_size 1m;

    location /mcp {
        proxy_pass http://127.0.0.1:8766;
        proxy_http_version 1.1;
        proxy_buffering off;
        proxy_read_timeout 300s;
        proxy_send_timeout 300s;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location / {
        proxy_pass http://127.0.0.1:8765;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location ~ /\.(env|git|ssh) { deny all; }
    location ~ /(tokens|secrets|logs|config)/ { deny all; }
}
```

## HTTPS через Let's Encrypt

```bash
sudo certbot --nginx -d your-domain.com
sudo systemctl reload nginx
```

После certbot проверьте:

```bash
curl -I https://your-domain.com/health
curl -I https://your-domain.com/ready
```

## Forwarding headers

Обязательно передавать:

- `Host`;
- `X-Forwarded-For`;
- `X-Forwarded-Proto`;
- `X-Real-IP`, если используется.

## MCP timeouts

Для `/mcp` рекомендуется:

- `proxy_buffering off`;
- `proxy_read_timeout 300s`;
- `proxy_send_timeout 300s`.

Это важно для Streamable HTTP transport.

## Security headers

Web server уже выставляет базовые headers, но reverse proxy может продублировать:

```nginx
add_header X-Content-Type-Options nosniff always;
add_header X-Frame-Options DENY always;
add_header Referrer-Policy no-referrer always;
```

## Что нельзя публиковать

Нельзя отдавать наружу:

- `.env`;
- `.git`;
- `tokens/`;
- `secrets/`;
- `logs/`;
- raw config с секретами.

## Caddy alternative

```caddyfile
your-domain.com {
    reverse_proxy /mcp* 127.0.0.1:8766
    reverse_proxy 127.0.0.1:8765
}
```

Caddy сам выпускает HTTPS certificates, но для beta рекомендуемый путь в документации - Nginx + certbot.

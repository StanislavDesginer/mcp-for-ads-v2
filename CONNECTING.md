# How to connect mcp-for-ads

## Main config files

This project uses two local runtime files:

- `ads_config.yaml`
- `.env`

These files are intentionally not committed with real secrets.

## What a tester needs from the project owner

To run real provider requests, the tester needs:
- a local `ads_config.yaml`
- a local `.env`
- active platform credentials

Without these files:
- the repository still opens
- tests still run
- the hosted UI still opens
- but live provider calls will stay on placeholder values or fail auth

For Codex-based testing, the tester also needs a local Codex MCP config.
Use the example file:
- [.codex/config.example.toml](.codex/config.example.toml)

## Local file placement

Put both local runtime files in the project root:

```text
mcp-for-ads/
  .env
  ads_config.yaml
  README.md
  pyproject.toml
  src/
```

## ads_config.yaml

The project loads provider connections from `ads_config.yaml`.

Start from:
- [ads_config.example.yaml](ads_config.example.yaml)

Meta example:

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

The project expands environment variables inside `ads_config.yaml`.

Start from:
- [.env.example](.env.example)

Example:

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

## Provider credential requirements

### Meta Ads

Required per account:
- `account_id`
- `app_id`
- `app_secret`
- `access_token`

Optional:
- `api_version`
- `action_metrics`
- `video_metrics`

### Google Ads

Required per account:
- `account_id`
- `customer_id`
- `login_customer_id`
- `developer_token`
- `oauth_client_id`
- `oauth_client_secret`
- `refresh_token`

### TikTok Ads

Required per account:
- `account_id`
- `advertiser_id`
- `app_id`
- `secret`
- `access_token`

### Yandex Direct

Required per account:
- `account_id`
- `login`
- `access_token`

## How runtime config is resolved

The server loads configuration in this order:

1. root `ads_config.yaml`
2. root `ads_config.example.yaml`
3. provider examples in `config/providers/*.example.yaml` as fallback

Environment variables inside YAML are expanded from the root `.env`.

## Hosted web UI

If the owner already deployed the web UI, a tester can validate the project without local MCP setup by opening:
- [http://77.240.38.131](http://77.240.38.131)

This is useful for:
- UI smoke testing
- diagnostics checks
- verifying deployed Meta account visibility

## Safety notes

- unknown accounts are blocked by default
- preview/write flows are still constrained by [config/policies/safety.example.yaml](config/policies/safety.example.yaml)
- real secrets should stay only in local `.env` and local `ads_config.yaml`

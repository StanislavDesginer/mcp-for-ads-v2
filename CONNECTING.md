# How To Connect mcp-for-ads

## Where to put connection data
All advertising platform connections are configured in one file in the project root:

- [ads_config.yaml](/Users/rocket/Documents/holymedia-ads/mcp-for-ads/ads_config.yaml)

If the file does not exist yet:
1. Copy [ads_config.example.yaml](/Users/rocket/Documents/holymedia-ads/mcp-for-ads/ads_config.example.yaml) to `ads_config.yaml`
2. Fill in only the providers and accounts you actually want to use

## Environment file
Optional runtime settings are configured in:

- [.env.example](/Users/rocket/Documents/holymedia-ads/mcp-for-ads/.env.example)

If needed, copy it to `.env` and adjust:
- `AD_MCP_CONNECTIONS_CONFIG`
- `AD_MCP_POLICY_CONFIG`
- `AD_MCP_AUDIT_LOG_PATH`

## What data is needed

### Google Ads
For each Google Ads account you need:
- `account_id`
- `customer_id`
- `login_customer_id`
- `developer_token`
- `oauth_client_id`
- `oauth_client_secret`
- `refresh_token`

Optional:
- `name`
- `status`
- `modules.ga4`
- `modules.merchant_center`
- `modules.youtube`
- `modules.search_console`
- `modules.business_profile`

### Meta Ads
For each Meta account you need:
- `account_id`
- `app_id`
- `app_secret`
- `access_token`

Optional:
- `name`
- `status`
- `api_version`
- `action_metrics`
- `video_metrics`

### TikTok Ads
For each TikTok account you need:
- `account_id`
- `advertiser_id`
- `app_id`
- `secret`
- `access_token`

Optional:
- `name`
- `status`

### Yandex Direct
For each Yandex account you need:
- `account_id`
- `login`
- `access_token`

Optional:
- `name`
- `status`

## File structure example
Use this shape inside `ads_config.yaml`:

```yaml
providers:
  google_ads:
    provider: google_ads
    accounts:
      - name: Main Google Account
        account_id: "1234567890"
        customer_id: "123-456-7890"
        login_customer_id: "123-456-7890"
        developer_token: "..."
        oauth_client_id: "..."
        oauth_client_secret: "..."
        refresh_token: "..."
```

## How the project reads credentials
- The server reads the root config file first
- It selects the provider section from `providers.<provider_name>`
- It selects the needed account from `accounts[]` by `account_id`
- Unknown accounts are blocked by policy unless explicitly allowed

## Important safety note
- The project currently supports preparing write operations, but it does **not** execute real writes to ad accounts
- `commit_preview` stays in simulated mode and only returns the request it would send

## Recommended setup steps
1. Create `ads_config.yaml` from `ads_config.example.yaml`
2. Fill in one provider first
3. Start with `Meta Ads` or `Google Ads`
4. Keep only real active accounts in the file
5. Do not commit `ads_config.yaml` with real secrets to git

## Recommended local install
```bash
cd /Users/rocket/Documents/holymedia-ads/mcp-for-ads
python3 -m venv .venv
source .venv/bin/activate
pip install -e .[dev,google,meta]
```

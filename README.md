# mcp-for-ads

Python MCP server for agency workflows across `Google Ads`, `Meta Ads`, `TikTok Ads`, and `Yandex Direct`.

## Current status
- Project scaffold created
- MCP stdio server bootstrapped
- Core discovery/reporting/preview-confirm tools added
- Provider adapters stubbed with capability maps
- Safe no-write commit simulation added
- Provider-specific payload builders added for all 4 networks
- Meta reporting can read live insights when credentials are configured
- Google Ads reporting can read live data when SDK credentials are configured
- TikTok and Yandex reporting return safe preview-mode responses until live clients are wired
- Ready for iterative provider implementation

## Goals
- Read ad account data from multiple networks through one MCP server
- Support safe write flows via `preview -> confirm`
- Expose both low-level CRUD tools and higher-level intent tools
- Avoid GUI and database dependencies

## Run locally
```bash
cd /Users/rocket/Documents/holymedia-ads/mcp-for-ads
python3 -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
ad-mcp-server
```

## Web UI MVP
- A lightweight Meta-only operator dashboard is now available for the currently configured account.
- It is built as a hostable single-page web UI on top of the existing provider logic and safe preview flows.
- Start it locally with:

```bash
cd C:\Users\Станислав\Documents\New project\mcp-for-ads
.\.venv\Scripts\python.exe -m pip install -e .[dev,meta]
ad-mcp-web
```

- Open [http://127.0.0.1:8765](http://127.0.0.1:8765)
- Current MVP includes:
- dashboard metrics from one Meta account
- delivery issues
- connected assets
- campaign structure
- top performers
- no-result spend watchlist
- safe preview actions for campaign clone, budget update, and bulk ad pause

## Connections config
- All provider connections now live in one root file: [ads_config.example.yaml](/Users/rocket/Documents/holymedia-ads/mcp-for-ads/ads_config.example.yaml)
- Full setup instructions are in [CONNECTING.md](/Users/rocket/Documents/holymedia-ads/mcp-for-ads/CONNECTING.md)

## First implemented tools
- `list_providers`
- `get_provider_capabilities`
- `list_supported_objects`
- `list_supported_metrics`
- `list_supported_dimensions`
- `list_supported_campaign_types`
- `list_supported_audience_types`
- `list_accounts`
- `describe_auth`
- `describe_auth_strategy`
- `list_objects`
- `get_object`
- `get_performance_report`
- `preview_create_object`
- `preview_update_object`
- `preview_delete_or_archive_object`
- `commit_preview`
- `create_campaign_from_brief`
- `create_ad_group_from_brief`
- `create_ad_from_brief`
- `create_keyword_from_brief`
- `create_audience_from_brief`
- `configure_schedule_from_brief`

## Current write-mode behavior
- All write actions are intentionally simulated
- `commit_preview` does not mutate real ad accounts
- The server returns the provider-native payload it would send
- This allows safe testing of prompts, flows, and validation before enabling real writes later
- Provider allowlist and mutation limits are enforced through `config/policies/safety*.yaml`

## Simulated write coverage
- `Google Ads`: campaign, ad_group, ad, keyword, audience, schedule, asset/extension
- `Meta Ads`: campaign, adset, ad, audience, schedule
- `TikTok Ads`: campaign, adgroup, ad, audience, schedule
- `Yandex Direct`: campaign, ad_group, ad, keyword, audience, schedule

## Important note
- The codebase now contains the provider-native write payload builders needed to create and update objects through ad platform APIs.
- Those operations are intentionally kept behind simulated commit responses, so the project can be tested safely without mutating real ad accounts.

## Provider status
- `Meta Ads`: live reporting path implemented when `facebook-business` and account config are present
- `Google Ads`: live reporting path implemented when `google-ads` SDK and account config are present
- `TikTok Ads`: safe preview provider with reporting contract and write-payload generation
- `Yandex Direct`: safe preview provider with reporting contract and write-payload generation

## Security notes
- Audit logs redact keys that look like secrets or tokens
- Unknown accounts are blocked by default
- Mutation previews validate `bulk_count` and `budget_delta_percent` against policy thresholds
- Date ranges are validated as ISO dates before provider execution
- `execution_mode` is enforced as `simulated_no_write` in runtime, not only in config text
- Entity aliases like `adgroup`, `ad_group`, and `adset` are normalized provider-side to reduce accidental misuse

## What is intentionally not finished yet
- Real OAuth/token refresh flows across all providers
- Real API clients for TikTok/Yandex live read paths
- Real API clients for all provider write paths
- Full provider-native validation for every object type
- Optional Google partner modules

## Suggested next install
```bash
cd /Users/rocket/Documents/holymedia-ads/mcp-for-ads
python3 -m venv .venv
source .venv/bin/activate
pip install -e .[dev,google,meta]
```

## Local references used
- `/Users/rocket/Documents/holymedia-ads/google-ads`
- `/Users/rocket/Documents/holymedia-ads/reports-holymedia`

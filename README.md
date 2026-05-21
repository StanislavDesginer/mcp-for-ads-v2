# mcp-for-ads

MCP server for ad operations across `Meta Ads`, `Google Ads`, `TikTok Ads`, and `Yandex Direct`.

The project currently focuses on:
- unified read tools across providers
- safe `preview -> confirm` write flows
- a Meta-focused web operator UI
- no-write safety by default

## Status

What is working now:
- MCP stdio server starts locally
- Meta Ads live read path is implemented
- Google Ads read path scaffold is present and ready for credentials
- TikTok Ads and Yandex Direct stay in safe preview mode until live clients are finished
- Meta web UI is available as an internal operator dashboard

What is intentionally still restricted:
- real mutation execution is not enabled by default
- safety policy enforces `simulated_no_write`
- production auth, tenancy, billing, and client isolation are not finished yet

## Repository layout

- [src/ad_mcp](src/ad_mcp) - application code
- [config/policies/safety.example.yaml](config/policies/safety.example.yaml) - safe default policy
- [ads_config.example.yaml](ads_config.example.yaml) - example provider connection config
- [CONNECTING.md](CONNECTING.md) - provider setup notes
- [TESTING.md](TESTING.md) - tester quickstart for local Codex and hosted web UI
- [DEPLOYING.md](DEPLOYING.md) - server deployment notes
- [CREATIVE_BRIEF_RU.md](CREATIVE_BRIEF_RU.md) - internal brief/reference

## Local setup

### Windows

```powershell
cd "<project-path>\\mcp-for-ads"
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev,google,meta]"
```

### Linux

```bash
cd /opt/mcp-for-ads
python3.11 -m venv .venv
./.venv/bin/python -m pip install -e ".[dev,google,meta]"
```

## Environment files

The project loads `.env` from the repository root and expands variables inside `ads_config.yaml`.

Start from [.env.example](.env.example) and create a local `.env`.

Important:
- keep `.env` local
- keep `ads_config.yaml` local
- do not commit secrets, tokens, app secrets, or refresh tokens into Git

## Running the MCP server

```powershell
cd "<project-path>\\mcp-for-ads"
.\.venv\Scripts\python.exe -m ad_mcp.server
```

or:

```powershell
ad-mcp-server
```

The server is designed to be started by an MCP client such as Codex, not manually typed into an interactive shell.

## Running the Meta web UI

Default bind:
- host: `127.0.0.1`
- port: `8765`

You can override these with:
- `AD_MCP_WEB_HOST`
- `AD_MCP_WEB_PORT`

Start locally:

```powershell
cd "<project-path>\\mcp-for-ads"
.\.venv\Scripts\python.exe -m ad_mcp.web.server
```

Open:
- [http://127.0.0.1:8765](http://127.0.0.1:8765)

Health check:
- [http://127.0.0.1:8765/healthz](http://127.0.0.1:8765/healthz)

## Tester handoff

If someone else needs to test the project, give them:
- the repository
- a local `.env`
- a local `ads_config.yaml`

They should then follow [TESTING.md](TESTING.md).

## Current Meta tool coverage

Read-oriented tools already added include:
- `get_account_summary`
- `list_account_objects`
- `get_account_object`
- `get_flexible_insights`
- `get_billing_summary`
- `get_spend_overview`
- `estimate_budget_days_remaining`
- `get_connected_assets`
- `get_delivery_issues`
- `get_status_summary`
- `get_breakdown_preset`
- `rank_top_entities`
- `get_top_performers`
- `get_no_result_entities`
- `find_wasting_spend`
- `find_burnout_ads`
- `compare_periods`
- `compare_creatives`
- `detect_anomalies`
- `analyze_audiences`
- `get_executive_summary`
- `audit_account`
- `audit_links_and_utms`
- `get_campaign_structure`
- `get_policy_issues`
- `get_conversion_health`
- `get_asset_health`
- `list_creative_assets`
- `list_lead_forms`
- `get_recommendations_read`
- `list_automated_rules`
- `get_rule_history`
- `get_minimum_budgets_read`
- `get_reach_estimate_read`
- `get_tracking_specs`
- `get_launch_checklist`

Write-preview tools include:
- `clone_campaign_preview`
- `clone_adset_preview`
- `clone_ad_preview`
- `update_campaign_budget_preview`
- `update_adset_budget_preview`
- `pause_entities_preview`
- `enable_entities_preview`
- `update_targeting_preview`
- `update_placements_preview`
- `replace_ad_creative_preview`
- `create_adset_in_campaign_preview`
- `create_ad_in_existing_adset_preview`
- `create_creative_preview`
- `create_audience_variant_preview`
- `create_engagement_campaign_preview`
- `create_lead_campaign_preview`
- `create_whatsapp_traffic_campaign_preview`
- `create_ab_test_ads_preview`
- `duplicate_campaign_with_geo_preview`
- `duplicate_campaign_with_audience_preview`
- `rebalance_budget_to_end_of_month_preview`
- `pause_underperformers_preview`
- `scale_best_campaigns_preview`
- `scale_winners_by_rule_preview`
- `archive_entities_preview`

## Safety defaults

Current safe defaults:
- unknown accounts are blocked
- mutation policy is constrained by [config/policies/safety.example.yaml](config/policies/safety.example.yaml)
- execution mode is `simulated_no_write`
- audit logging writes to `logs/audit.jsonl`

For hosting, do not expose preview/write endpoints to the public internet without:
- access control
- reverse proxy
- IP filtering or auth
- proper secret storage

## Hosting notes

Recommended baseline:
- Ubuntu 22.04 LTS or 24.04 LTS
- Python 3.11
- systemd
- Nginx reverse proxy
- `.env` stored on server only
- `ads_config.yaml` stored on server only

For a deployment-oriented walkthrough, see [DEPLOYING.md](DEPLOYING.md).

## Tests

Run tests with:

```powershell
cd "<project-path>\\mcp-for-ads"
.\.venv\Scripts\python.exe -m pytest -q
```

## Current security posture

Good right now:
- secrets are expected from environment variables
- tracked example files are present
- local secret files are ignored by Git
- web UI binds to localhost by default

Still important before real production use:
- add auth in front of the web UI
- separate per-client secrets storage
- rotate any tokens that were ever pasted into chat
- move from single-project local config to tenant-aware storage

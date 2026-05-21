# Testing Guide

This repository can be tested in two modes:

1. hosted web UI only
2. local Codex + MCP tools

## What a tester needs from the project owner

For live Meta requests, the tester needs two local files that are not committed:
- `.env`
- `ads_config.yaml`

Without them:
- the repository still installs
- tests still run
- hosted UI still opens
- but live provider calls will fail auth or stay on placeholder values

## Fastest way to test right now

Use the hosted panel:
- [http://77.240.38.131](http://77.240.38.131)

This is the best option for a quick smoke test of:
- Meta dashboard loading
- diagnostics screens
- account summaries
- web UI behavior

## Local setup for a tester

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

## Local runtime files

Put the local files in the repository root:

```text
mcp-for-ads/
  .env
  ads_config.yaml
  pyproject.toml
  src/
```

Start from these tracked examples:
- [ads_config.example.yaml](ads_config.example.yaml)
- [.env.example](.env.example)

Provider credential structure is documented in [CONNECTING.md](CONNECTING.md).

## Local web UI

Run:

```powershell
cd "<project-path>\\mcp-for-ads"
.\.venv\Scripts\python.exe -m ad_mcp.web.server
```

Open:
- [http://127.0.0.1:8765](http://127.0.0.1:8765)
- [http://127.0.0.1:8765/healthz](http://127.0.0.1:8765/healthz)

## Local Codex + MCP setup

The repository includes an example Codex MCP config:
- [.codex/config.example.toml](.codex/config.example.toml)

To use it:
1. copy the example into your own Codex config location
2. replace the Windows path placeholders with your real local project path
3. restart Codex in the project folder

## Example Codex prompts

Once MCP is connected, a tester can ask:

```text
Use MCP server ads and show list_accounts for provider meta_ads.
```

```text
Use MCP server ads and call get_account_summary for provider meta_ads and account_id act_1746501262698286.
```

```text
Use MCP server ads and call find_wasting_spend for provider meta_ads, account_id act_1746501262698286, start_date 2026-04-01, end_date 2026-05-21.
```

```text
Use MCP server ads and call get_top_performers for provider meta_ads, account_id act_1746501262698286, end_date 2026-05-21.
```

## What a tester can validate

- project installs cleanly
- MCP server starts
- Meta accounts resolve from local config
- web UI loads
- diagnostics endpoints work
- read tools return real Meta data
- preview write tools return safe preview payloads

## Safety notes for testers

- keep `.env` local
- keep `ads_config.yaml` local
- do not commit live tokens or app secrets
- rotate any tokens that were previously pasted into chats

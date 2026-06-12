# Beta security

AdForge MCP beta построен вокруг безопасной hosted-модели: сервер и секреты находятся на VPS/WPS, клиент подключает только dashboard и hosted MCP endpoint.

## Preview-only mode

В beta реальные write-действия отключены.

```env
AD_MCP_PREVIEW_ONLY=true
```

Это означает:

- dangerous tools возвращают `mode=preview_only`;
- dangerous tools возвращают `will_apply=false`;
- `commit_preview` блокируется;
- provider write endpoints не вызываются;
- preview показывает expected result, но ничего не применяет в рекламном кабинете.

## Beta token

Web API и hosted MCP endpoint закрываются beta token:

```env
AD_MCP_WEB_API_TOKEN=change-this-beta-token
```

Клиент передает токен как:

```http
Authorization: Bearer <BETA_TOKEN>
```

В production-like окружении без `AD_MCP_WEB_API_TOKEN` API должен быть заблокирован.

## Секреты

Нельзя коммитить:

- `.env`;
- `ads_config.yaml`;
- `tokens/connections.json`;
- `access_token`;
- `refresh_token`;
- `client_secret`;
- `app_secret`;
- `developer_token`.

OAuth credentials и provider secrets должны приходить только из env на сервере.

## Что скрывается в API

Diagnostics и dashboard не должны показывать:

- полный access token;
- полный refresh token;
- полный client secret;
- полный app secret;
- Google Ads developer token;
- beta token.

Env variables показываются только как `present` или `missing`.

## Connection storage

`tokens/connections.json` - beta storage. Он нужен для быстрой beta-итерации и хранит OAuth connections runtime-уровня.

Для production потребуется:

- database-backed encrypted storage;
- user isolation;
- per-user/per-tenant access control;
- rotation и revoke flow;
- audit trail для token operations.

## Logs

В logs не должны попадать raw tokens или secrets. Ошибки OAuth/provider API должны редактироваться перед выводом наружу.

## Preview response

Preview должен содержать:

- `platform`;
- `account_id`;
- `object_type`;
- `object_id`;
- `action`;
- `current_value`;
- `requested_value`;
- `expected_result`;
- `risk_level`;
- `will_apply=false`;
- причину, что beta работает в preview-only mode.

Если текущее состояние невозможно прочитать, preview не должен выдумывать current value.

## Known beta risks

- JSON storage не является production database.
- Multi-tenant isolation еще не финализирован.
- Реальные provider credentials требуют ручной проверки на live аккаунтах.
- TikTok/Yandex read support ограничен, поэтому нельзя обещать live campaigns/metrics до отдельной реализации.

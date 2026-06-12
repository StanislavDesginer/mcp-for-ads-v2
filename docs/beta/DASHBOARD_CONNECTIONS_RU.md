# Dashboard Connections

Dashboard Connections - основной onboarding-экран beta-пользователя. Через него подключаются рекламные платформы, выбираются аккаунты и проверяется готовность hosted MCP.

## Как открыть

1. Открыть dashboard URL, который выдала команда AdForge.
2. Если dashboard попросил beta token, вставить токен, полученный отдельно.
3. Открыть раздел `Connections`.

Пользователь не должен скачивать репозиторий, запускать локальный сервер или редактировать `.env`.

## Hosted MCP block

В верхнем блоке Connections отображаются:

- имя сервера `AdForge MCP`;
- transport, обычно `streamable_http`;
- MCP URL, например `https://your-domain.com/mcp`;
- состояние connection store;
- кнопка `Copy MCP URL`.

Этот URL нужен для Codex, Claude, Gemini или другого MCP-клиента.

## Подключение Meta Ads

1. В карточке `Meta Ads` нажать `Connect`.
2. Пройти Meta OAuth.
3. Подтвердить нужные разрешения.
4. После возврата в dashboard выбрать рекламные аккаунты.
5. Нажать сохранение выбора.
6. Запустить `Run diagnostics`.
7. Убедиться, что статус стал `MCP ready` или `connected`.

## Подключение Google Ads

1. В карточке `Google Ads` нажать `Connect`.
2. Пройти Google OAuth.
3. Разрешить доступ к Google Ads.
4. После callback выбрать customer accounts.
5. Сохранить выбор.
6. Запустить диагностику.

Для Google Ads на сервере также должен быть настроен `AD_MCP_GOOGLE_ADS_DEVELOPER_TOKEN`.

## Подключение TikTok Ads

1. В карточке `TikTok Ads` нажать `Connect`, если OAuth credentials настроены.
2. Пройти TikTok OAuth.
3. Выбрать доступные advertiser accounts.
4. Сохранить подключение.

В текущей beta TikTok connection flow может быть доступен, но campaigns/metrics могут возвращать `not_available`.

## Подключение Yandex Direct

1. В карточке `Yandex Direct` нажать `Connect`, если OAuth credentials настроены.
2. Пройти Yandex OAuth.
3. Выбрать доступные client logins.
4. Сохранить подключение.

В текущей beta Yandex connection flow может быть доступен, но campaigns/metrics могут возвращать `not_available`.

## Account selection

После успешного OAuth dashboard показывает pending selection:

- provider;
- список доступных аккаунтов;
- checkbox для выбора;
- кнопку сохранения.

Если аккаунты не выбрать, MCP tools увидят платформу как `no_accounts_selected`.

## Статусы

| Status | Значение |
| --- | --- |
| `not_connected` | Платформа не подключена. |
| `connecting` | OAuth начат или ожидается callback. |
| `pending_account_selection` | OAuth прошел, нужно выбрать аккаунты. |
| `connected` | Подключение сохранено. |
| `mcp_ready` | MCP tools могут использовать платформу. |
| `error` | Последняя операция завершилась ошибкой. |
| `expired` | Pending selection или token истек. |
| `reconnect_required` | Нужно переподключить платформу. |
| `not_available` | Возможность пока ограничена или не реализована. |

## Reconnect

Нажмите `Reconnect` в карточке платформы. Dashboard снова запустит OAuth flow и после callback предложит выбрать аккаунты.

## Disconnect

Нажмите `Disconnect` в карточке платформы. Backend удалит сохраненные tokens/accounts этой платформы из beta connection store.

## Troubleshooting

`env missing`: на сервере не заполнены OAuth env variables. Нужно заполнить `.env` на VPS/WPS и перезапустить сервисы.

`invalid redirect URL`: redirect URI в приложении провайдера не совпадает с dashboard callback URL.

`OAuth callback error`: provider вернул ошибку или state истек. Запустите reconnect.

`no accounts returned`: у пользователя нет доступных рекламных аккаунтов или не хватает permissions.

`token expired`: переподключите платформу через reconnect.

`provider API error`: запустите `Run diagnostics`, проверьте permissions, developer token и доступы в рекламном кабинете.

`no accounts selected`: OAuth прошел, но аккаунты не были выбраны в pending selection.

`MCP client sees no tools`: проверьте MCP URL, beta token и доступность `/api/diagnostics/mcp`.

`diagnostics failed`: проверьте backend logs и endpoint `GET /api/diagnostics`.

# Dashboard Connections

`Connections` - основной рабочий раздел dashboard. Через него beta-пользователь подключает рекламные платформы, выбирает аккаунты и проверяет готовность hosted MCP.

Dashboard состоит из трёх разделов:

- `Overview` - статус сервиса, счётчики подключений, next steps и блок `Connect to MCP client` с MCP URL.
- `Connections` - карточки платформ, OAuth, выбор аккаунтов, reconnect/disconnect.
- `Diagnostics` - запуск полной диагностики (service, security, MCP, platforms).

В header всегда виден бейдж `Preview-only: ON` - опасные действия только предпросматриваются и не применяются к рекламным кабинетам.

## Вход (token gate)

1. Открыть dashboard URL, который выдала команда AdForge.
2. На экране входа вставить beta token в поле `Beta access token` и нажать `Enter dashboard`.
3. При неверном токене показывается `Invalid or missing beta token`.

Токен хранится только в браузере и нигде не отображается после входа. Кнопка `Sign out` в header очищает его.

Пользователь не должен скачивать репозиторий, запускать локальный сервер или редактировать `.env`.

## Hosted MCP block (Overview)

В разделе `Overview`, блок `Connect to MCP client`:

- MCP URL, например `https://your-domain.com/mcp`;
- кнопка `Copy MCP URL`;
- пример заголовка авторизации `Authorization: Bearer <BETA_TOKEN>` (без реального токена).

Этот URL нужен для Codex, Claude или другого MCP-клиента. Beta token передаётся как Bearer authorization.

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

## Статусы карточек

В карточке платформы статус показан бейджем:

| Бейдж | Значение |
| --- | --- |
| `Credentials missing` | OAuth credentials провайдера не настроены на сервере. Кнопка `Connect` заблокирована. |
| `Ready to connect` | Credentials есть, можно запускать OAuth. |
| `Select accounts` | OAuth прошёл, нужно выбрать аккаунты (pending selection). |
| `Connected` | Подключение сохранено, аккаунты доступны MCP tools. |
| `Reconnect required` | Pending selection истёк - нужно переподключить. |
| `Limited beta` | Дополнительный бейдж для TikTok/Yandex: OAuth groundwork, campaigns/metrics могут быть `not_available`. |
| `Error` | Последняя операция завершилась ошибкой (см. `Last error` в карточке). |

Diagnostics-статусы платформ (`Run diagnostics`): `mcp_ready`, `env_missing`, `not_connected`, `token_expired`, `api_error`, `needs_setup`.

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

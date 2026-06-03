(function () {
  const state = {
    accountId: "",
    endDate: new Date().toISOString().slice(0, 10),
    workspace: null,
    selectedSkillId: "collect_report",
    selectedSkill: null,
  };

  const el = {
    statusDot: document.getElementById("status-dot"),
    statusText: document.getElementById("status-text"),
    lastRefreshTime: document.getElementById("last-refresh-time"),
    topbarAccountName: document.getElementById("topbar-account-name"),
    filterAccountId: document.getElementById("filter-account-id"),
    filterEndDate: document.getElementById("filter-end-date"),
    applyFilters: document.getElementById("apply-filters"),
    refreshAll: document.getElementById("refresh-all"),
    navButtons: Array.from(document.querySelectorAll(".nav-button")),
    panels: Array.from(document.querySelectorAll("[data-section-panel]")),
    overviewHeadline: document.getElementById("overview-headline"),
    overviewOperatorSummary: document.getElementById("overview-operator-summary"),
    overviewMetrics: document.getElementById("overview-metrics"),
    overviewAccount: document.getElementById("overview-account"),
    overviewStatuses: document.getElementById("overview-statuses"),
    structureContent: document.getElementById("structure-content"),
    issuesContent: document.getElementById("issues-content"),
    assetsContent: document.getElementById("assets-content"),
    performersContent: document.getElementById("performers-content"),
    performersLevel: document.getElementById("performers-level"),
    performersMetric: document.getElementById("performers-metric"),
    performersLookback: document.getElementById("performers-lookback"),
    performersRefresh: document.getElementById("performers-refresh"),
    wasteContent: document.getElementById("waste-content"),
    wasteLevel: document.getElementById("waste-level"),
    wasteLookback: document.getElementById("waste-lookback"),
    wasteMinSpend: document.getElementById("waste-min-spend"),
    wasteRefresh: document.getElementById("waste-refresh"),
    diagnosticsHealth: document.getElementById("diagnostics-health"),
    diagnosticsConfig: document.getElementById("diagnostics-config"),
    diagnosticsAuth: document.getElementById("diagnostics-auth"),
    diagnosticsPersistence: document.getElementById("diagnostics-persistence"),
    diagnosticsContract: document.getElementById("diagnostics-contract"),
    diagnosticsTroubleshooting: document.getElementById("diagnostics-troubleshooting-content"),
    diagnosticsRefresh: document.getElementById("diagnostics-refresh"),
    skillsCatalog: document.getElementById("skills-catalog"),
    skillsPromptBox: document.getElementById("skills-prompt-box"),
    skillsCopyPrompt: document.getElementById("skills-copy-prompt"),
    skillsRunSelected: document.getElementById("skills-run-selected"),
    skillsResult: document.getElementById("skills-result"),
    drawer: document.getElementById("preview-drawer"),
    drawerBackdrop: document.getElementById("drawer-backdrop"),
    drawerClose: document.getElementById("drawer-close"),
    drawerCopy: document.getElementById("drawer-copy"),
    drawerJson: document.getElementById("drawer-json"),
    drawerRiskFlags: document.getElementById("drawer-risk-flags"),
    actionTabs: Array.from(document.querySelectorAll(".action-tab")),
    actionPanels: Array.from(document.querySelectorAll(".action-panel")),
    formClone: document.getElementById("form-clone"),
    formBudget: document.getElementById("form-budget"),
    formPause: document.getElementById("form-pause"),
    toastRoot: document.getElementById("toast-root"),
  };

  const api = {
    workspace: (params) => requestJson(`/api/meta/workspace${withQuery(params)}`),
    performers: (params) => requestJson(`/api/meta/top-performers${withQuery(params)}`),
    noResult: (params) => requestJson(`/api/meta/no-result-entities${withQuery(params)}`),
    configDiagnostics: () => requestJson("/api/meta/config-diagnostics"),
    authDiagnostics: () => requestJson("/api/meta/auth-diagnostics"),
    debugHealth: () => requestJson("/api/meta/debug-health"),
    persistence: () => requestJson("/api/meta/persistence"),
    dataContract: () => requestJson("/api/meta/data-contract"),
    budgetSkill: (params) => requestJson(`/api/meta/skills/budget-summary${withQuery(params)}`),
    disableSkill: (params) => requestJson(`/api/meta/skills/disable-candidates${withQuery(params)}`),
    scaleSkill: (params) => requestJson(`/api/meta/skills/scale-candidates${withQuery(params)}`),
    reportSkill: (params) => requestJson(`/api/meta/skills/collect-report${withQuery(params)}`),
    previewClone: (payload) => requestJson("/api/meta/preview/clone-campaign", "POST", payload),
    previewBudget: (payload) => requestJson("/api/meta/preview/update-campaign-budget", "POST", payload),
    previewPause: (payload) => requestJson("/api/meta/preview/pause-ads", "POST", payload),
  };

  function init() {
    el.filterEndDate.value = state.endDate;
    bindNavigation();
    bindTopbar();
    bindSectionRefreshers();
    bindSkills();
    bindDrawer();
    bindPreviewForms();
    bindActionTabs();
    setActiveSection("skills");
    refreshAll();
  }

  function bindNavigation() {
    el.navButtons.forEach((button) => {
      button.addEventListener("click", () => setActiveSection(button.dataset.section));
    });
  }

  function bindTopbar() {
    el.applyFilters.addEventListener("click", () => {
      syncFiltersFromForm();
      refreshAll();
    });
    el.refreshAll.addEventListener("click", () => {
      syncFiltersFromForm();
      refreshAll();
    });
  }

  function bindSectionRefreshers() {
    el.performersRefresh.addEventListener("click", () => {
      syncFiltersFromForm();
      loadPerformers();
    });
    el.wasteRefresh.addEventListener("click", () => {
      syncFiltersFromForm();
      loadNoResultSpend();
    });
    el.diagnosticsRefresh.addEventListener("click", () => {
      loadDiagnostics();
    });
  }

  function bindSkills() {
    el.skillsCopyPrompt.addEventListener("click", async () => {
      const text = el.skillsPromptBox.value.trim();
      if (!text) {
        toast("Сначала выберите навык.", "info");
        return;
      }
      await copyText(text);
      toast("Prompt скопирован.", "success");
    });

    el.skillsRunSelected.addEventListener("click", () => {
      runSelectedSkill();
    });
  }

  function bindDrawer() {
    const close = () => {
      el.drawer.classList.remove("is-open");
      el.drawer.setAttribute("aria-hidden", "true");
      el.drawerBackdrop.hidden = true;
    };

    el.drawerClose.addEventListener("click", close);
    el.drawerBackdrop.addEventListener("click", close);
    el.drawerCopy.addEventListener("click", async () => {
      await copyText(el.drawerJson.textContent || "");
      toast("JSON скопирован.", "success");
    });
  }

  function bindActionTabs() {
    el.actionTabs.forEach((tab) => {
      tab.addEventListener("click", () => {
        const target = tab.dataset.actionTab;
        el.actionTabs.forEach((item) => {
          const active = item === tab;
          item.classList.toggle("is-active", active);
          item.setAttribute("aria-selected", String(active));
        });
        el.actionPanels.forEach((panel) => {
          const active = panel.id === `panel-${target}`;
          panel.classList.toggle("is-active", active);
          panel.hidden = !active;
        });
      });
    });
  }

  function bindPreviewForms() {
    el.formClone.addEventListener("submit", async (event) => {
      event.preventDefault();
      const form = new FormData(el.formClone);
      await submitPreview(event.submitter, () =>
        api.previewClone({
          account_id: state.accountId,
          source_campaign_id: form.get("source_campaign_id"),
          new_name: emptyToNull(form.get("new_name")),
          status: form.get("status"),
          daily_budget: toNumberOrNull(form.get("daily_budget")),
          lifetime_budget: toNumberOrNull(form.get("lifetime_budget")),
        }),
      );
    });

    el.formBudget.addEventListener("submit", async (event) => {
      event.preventDefault();
      const form = new FormData(el.formBudget);
      await submitPreview(event.submitter, () =>
        api.previewBudget({
          account_id: state.accountId,
          campaign_id: form.get("campaign_id"),
          daily_budget: toNumberOrNull(form.get("daily_budget")),
          lifetime_budget: toNumberOrNull(form.get("lifetime_budget")),
          spend_cap: toNumberOrNull(form.get("spend_cap")),
          budget_delta_percent: toNumberOrNull(form.get("budget_delta_percent")),
        }),
      );
    });

    el.formPause.addEventListener("submit", async (event) => {
      event.preventDefault();
      const form = new FormData(el.formPause);
      await submitPreview(event.submitter, () =>
        api.previewPause({
          account_id: state.accountId,
          ids: parseIds(form.get("ids")),
        }),
      );
    });
  }

  async function submitPreview(button, action) {
    const submitButton = button || document.activeElement;
    if (submitButton) {
      submitButton.classList.add("is-loading");
      submitButton.disabled = true;
    }
    try {
      const preview = await action();
      renderPreview(preview);
      toast("Preview собран.", "success");
    } catch (error) {
      toast(error.message || "Не удалось собрать preview.", "error");
    } finally {
      if (submitButton) {
        submitButton.classList.remove("is-loading");
        submitButton.disabled = false;
      }
    }
  }

  async function refreshAll() {
    setStatus("loading", "Обновляю данные…");
    try {
      await loadWorkspace();
      await Promise.allSettled([loadDiagnostics(), loadPerformers(), loadNoResultSpend()]);
      setStatus("ok", "Данные обновлены");
    } catch (error) {
      setStatus("error", error.message || "Ошибка загрузки данных");
      renderError(el.overviewMetrics, error.message || "Не удалось загрузить workspace.");
    } finally {
      el.lastRefreshTime.textContent = `Обновлено: ${new Date().toLocaleTimeString("ru-RU")}`;
    }
  }

  async function loadWorkspace() {
    const payload = await api.workspace({
      account_id: state.accountId || undefined,
      end_date: state.endDate || undefined,
    });
    state.workspace = payload;
    state.accountId = payload.account_id || state.accountId;
    populateAccountSelect(payload.header?.available_accounts || []);
    if (state.accountId) {
      el.filterAccountId.value = state.accountId;
    }
    el.topbarAccountName.textContent = payload.header?.account_name || payload.account_id || "Meta Ads account";
    renderOverview(payload);
    renderStructure(payload.sections?.structure || {});
    renderIssues(payload.sections?.issues || {});
    renderAssets(payload.sections?.assets || {});
    renderPerformers(payload.sections?.performers || {});
    renderNoResult(payload.sections?.no_result || {});
    renderDiagnosticsFromWorkspace(payload);
    renderSkillCatalog(payload.skills?.catalog || []);
    renderSelectedSkillFromWorkspace();
  }

  async function loadPerformers() {
    renderLoading(el.performersContent, "Обновляем top performers…");
    try {
      const payload = await api.performers({
        account_id: state.accountId,
        end_date: state.endDate,
        entity_level: el.performersLevel.value,
        metric: el.performersMetric.value,
        lookback_days: el.performersLookback.value || "7",
        limit: "8",
      });
      renderPerformers(payload);
    } catch (error) {
      renderError(el.performersContent, error.message || "Не удалось обновить top performers.");
    }
  }

  async function loadNoResultSpend() {
    renderLoading(el.wasteContent, "Обновляем no-result spend…");
    try {
      const payload = await api.noResult({
        account_id: state.accountId,
        end_date: state.endDate,
        entity_level: el.wasteLevel.value,
        lookback_days: el.wasteLookback.value || "7",
        min_spend: el.wasteMinSpend.value || "20",
        limit: "12",
      });
      renderNoResult(payload);
    } catch (error) {
      renderError(el.wasteContent, error.message || "Не удалось обновить список сущностей без результата.");
    }
  }

  async function loadDiagnostics() {
    renderLoading(el.diagnosticsHealth, "Проверяем конфигурацию…");
    try {
      const [health, config, auth, persistence, contract] = await Promise.all([
        api.debugHealth(),
        api.configDiagnostics(),
        api.authDiagnostics(),
        api.persistence(),
        api.dataContract(),
      ]);
      renderDiagnostics(health, config, auth, persistence, contract);
    } catch (error) {
      renderError(el.diagnosticsHealth, error.message || "Не удалось обновить диагностику.");
    }
  }

  function renderOverview(workspace) {
    const summary = workspace.summary || {};
    const metrics = summary.metrics || [];
    const currency = workspace.header?.currency;

    el.overviewHeadline.textContent = summary.headline || "Сводка пока не собрана.";
    renderOperatorSummary(summary.operator_summary || [], workspace.persistence || {});

    el.overviewMetrics.innerHTML = metrics.length
      ? metrics
          .map(
            (metric) => `
              <article class="metric-card">
                <span class="metric-card__label">${esc(metric.label)}</span>
                <strong class="metric-card__value">${formatValue(metric.value, metric.format, currency)}</strong>
                <span class="metric-card__hint">${esc(metric.id)}</span>
              </article>
            `,
          )
          .join("")
      : renderEmptyMarkup("KPI по этому кабинету пока не собраны.");

    const account = workspace.sections?.overview?.account?.data || {};
    const totals = workspace.sections?.overview?.totals || {};
    el.overviewAccount.innerHTML = renderKvGrid([
      ["Название", account.name || workspace.header?.account_name || "—"],
      ["ID аккаунта", workspace.account_id || "—"],
      ["Валюта", workspace.header?.currency || account.currency || "—"],
      ["Часовой пояс", workspace.header?.timezone || account.timezone_name || "—"],
      ["Campaigns", totals.campaigns ?? "—"],
      ["Ad sets", totals.adsets ?? "—"],
      ["Ads", totals.ads ?? "—"],
    ]);

    const statusRows = summary.status_rows || [];
    if (!statusRows.length) {
      renderEmpty(el.overviewStatuses, "Статусы пока не получены.");
      return;
    }
    const byGroup = statusRows.reduce((acc, row) => {
      const group = row.group || "other";
      acc[group] = acc[group] || [];
      acc[group].push(row);
      return acc;
    }, {});

    el.overviewStatuses.innerHTML = Object.entries(byGroup)
      .map(
        ([group, rows]) => `
          <div class="status-list">
            <h5>${esc(group)}</h5>
            <div class="status-chips">
              ${rows
                .map(
                  (row) =>
                    `<span class="status-chip ${statusClass(row.status)}">${esc(row.status)} · ${formatNumber(row.count)}</span>`,
                )
                .join("")}
            </div>
          </div>
        `,
      )
      .join("");
  }

  function renderOperatorSummary(rows, persistence) {
    const items = [...rows];
    if (persistence && Object.keys(persistence).length) {
      items.push({
        label: "Синк в ClickHouse",
        value: describePersistenceShort(persistence),
      });
    }
    if (!items.length) {
      renderEmpty(el.overviewOperatorSummary, "Операторская сводка пока недоступна.");
      return;
    }
    el.overviewOperatorSummary.innerHTML = `
      <div class="list-box">
        ${items
          .map(
            (row) => `
              <div class="list-row">
                <div class="list-row__head">
                  <span class="list-row__title">${esc(row.label || "Показатель")}</span>
                </div>
                <div class="list-row__text">${esc(stringify(row.value))}</div>
              </div>
            `,
          )
          .join("")}
      </div>
    `;
  }

  function renderStructure(payload) {
    const rows = payload.rows || [];
    if (!rows.length) {
      renderEmpty(el.structureContent, "Структура кампаний пока не получена.");
      return;
    }
    el.structureContent.innerHTML = `
      <div class="structure-list">
        ${rows
          .map(
            (campaign) => `
              <details class="structure-item">
                <summary>
                  <span class="structure-item__name">${esc(campaign.campaign_name || campaign.campaign_id || "Campaign")}</span>
                  <span class="status-chip ${statusClass(campaign.campaign_status)}">${esc(campaign.campaign_status || "UNKNOWN")}</span>
                </summary>
                <div class="structure-item__body">
                  ${
                    (campaign.adsets || [])
                      .map(
                        (adset) => `
                          <div class="list-row">
                            <div class="list-row__head">
                              <span class="list-row__title">${esc(adset.adset_name || adset.adset_id || "Ad set")}</span>
                              <span class="status-chip ${statusClass(adset.adset_status)}">${esc(adset.adset_status || "UNKNOWN")}</span>
                            </div>
                            <ul class="structure-sublist">
                              ${(adset.ads || [])
                                .map((ad) => `<li>${esc(ad.ad_name || ad.ad_id || "Ad")} · ${esc(ad.ad_status || "UNKNOWN")}</li>`)
                                .join("")}
                            </ul>
                          </div>
                        `,
                      )
                      .join("") || renderEmptyMarkup("Для кампании пока нет ad sets.")
                  }
                </div>
              </details>
            `,
          )
          .join("")}
      </div>
    `;
  }

  function renderIssues(payload) {
    const issues = payload.issues || [];
    if (!issues.length) {
      renderEmpty(el.issuesContent, "Проблем доставки не найдено.");
      return;
    }
    el.issuesContent.innerHTML = `
      <div class="list-box">
        ${issues
          .map(
            (issue) => `
              <article class="list-row">
                <div class="list-row__head">
                  <span class="list-row__title">${esc(issue.name || issue.id || "Сущность")}</span>
                  <span class="status-chip ${statusClass(issue.status)}">${esc(issue.status || "UNKNOWN")}</span>
                </div>
                <div class="list-row__meta">${esc(issue.object_type || "entity")} · ${esc(issue.id || "—")}</div>
                <div class="list-row__text">${esc(issue.review_feedback || stringify(issue.issues_info) || "Нужна ручная проверка.")}</div>
              </article>
            `,
          )
          .join("")}
      </div>
    `;
  }

  function renderAssets(payload) {
    const assets = payload.assets || {};
    const groups = [
      ["Страницы", assets.pages || []],
      ["Instagram", assets.instagram_accounts || []],
      ["Пиксели", assets.pixels || []],
      ["Custom conversions", assets.custom_conversions || []],
    ];

    el.assetsContent.innerHTML = groups
      .map(
        ([title, rows]) => `
          <article class="panel-card">
            <h4>${esc(title)}</h4>
            ${
              rows.length
                ? `<div class="list-box">
                    ${rows
                      .map(
                        (row) => `
                          <div class="list-row">
                            <div class="list-row__head">
                              <span class="list-row__title">${esc(row.name || row.id || "Asset")}</span>
                            </div>
                            <div class="list-row__meta mono-text">${esc(row.id || "—")}</div>
                          </div>
                        `,
                      )
                      .join("")}
                  </div>`
                : renderEmptyMarkup("Нет подключённых объектов в этой группе.")
            }
          </article>
        `,
      )
      .join("");
  }

  function renderPerformers(payload) {
    const rows = payload.rows || [];
    if (!rows.length) {
      renderEmpty(el.performersContent, "Подходящие top performers пока не найдены.");
      return;
    }
    el.performersContent.innerHTML = renderTable(rows, [
      ["entity_name", "Сущность"],
      ["spend", "Расход", "currency"],
      ["conversions", "Конверсии", "number"],
      ["cost_per_result", "Цена результата", "currency"],
      ["ctr", "CTR", "percent"],
      ["cpc", "CPC", "currency"],
    ]);
  }

  function renderNoResult(payload) {
    const rows = payload.rows || [];
    if (!rows.length) {
      renderEmpty(el.wasteContent, "Сущностей с расходом без результата не найдено.");
      return;
    }
    el.wasteContent.innerHTML = renderTable(rows, [
      ["entity_name", "Сущность"],
      ["spend", "Расход", "currency"],
      ["conversions", "Конверсии", "number"],
      ["ctr", "CTR", "percent"],
      ["objective", "Objective"],
    ]);
  }

  function renderDiagnosticsFromWorkspace(workspace) {
    const diagnostics = workspace.sections?.diagnostics || {};
    renderDiagnostics(
      diagnostics.health || {},
      diagnostics.config || {},
      diagnostics.auth || {},
      diagnostics.persistence || workspace.persistence || {},
      workspace.data_contract || {},
    );
  }

  function renderDiagnostics(health, config, auth, persistence, contractPayload) {
    const contract = contractPayload.clickhouse || contractPayload;

    el.diagnosticsHealth.innerHTML = `
      <article class="diag-health-card">
        <h4>Health</h4>
        <div class="diag-stack">
          <div class="kv-row"><span>Статус</span><strong>${esc(health.status || "unknown")}</strong></div>
          <div class="kv-row"><span>Accounts checked</span><strong>${formatNumber(health.auth?.accounts_checked || 0)}</strong></div>
          <div class="kv-row"><span>Auth OK</span><strong>${formatNumber(health.auth?.auth_ok_count || 0)}</strong></div>
          <div class="kv-row"><span>Auth failed</span><strong>${formatNumber(health.auth?.auth_failed_count || 0)}</strong></div>
        </div>
      </article>
      <article class="diag-health-card">
        <h4>Runtime</h4>
        <div class="diag-stack">
          <div class="kv-row"><span>.env найден</span><strong>${boolText(config.env?.exists)}</strong></div>
          <div class="kv-row"><span>Accounts loaded</span><strong>${formatNumber(config.runtime?.accounts_total || 0)}</strong></div>
          <div class="kv-row"><span>Env substitution OK</span><strong>${boolText(config.env_substitution?.all_resolved)}</strong></div>
          <div class="kv-row"><span>ClickHouse host</span><strong>${esc(contract.database?.host || "не задан")}</strong></div>
        </div>
      </article>
    `;

    const accounts = config.runtime?.accounts || [];
    el.diagnosticsConfig.innerHTML = `
      <article class="panel-card">
        <h4>Runtime-конфигурация</h4>
        ${
          accounts.length
            ? renderTable(accounts, [
                ["name", "Аккаунт"],
                ["account_id", "Account ID"],
                ["app_id", "App ID"],
                ["access_token.masked", "Token"],
                ["app_secret.masked", "App secret"],
              ])
            : renderEmptyMarkup("Runtime-конфигурация пока не загрузила аккаунты.")
        }
      </article>
    `;

    const checks = auth.checks || [];
    el.diagnosticsAuth.innerHTML = `
      <article class="panel-card">
        <h4>Проверка авторизации</h4>
        ${
          checks.length
            ? renderTable(checks, [
                ["name", "Аккаунт"],
                ["account_id", "Account ID"],
                ["auth_ok", "Auth OK", "boolean"],
                ["account_name_from_meta", "Имя из Meta"],
                ["meta_account_status", "Статус Meta"],
                ["error", "Ошибка"],
              ])
            : renderEmptyMarkup("Проверки авторизации пока не выполнялись.")
        }
      </article>
    `;

    el.diagnosticsPersistence.innerHTML = `
      <article class="panel-card">
        <h4>ClickHouse persistence</h4>
        ${renderPersistence(persistence)}
      </article>
    `;

    el.diagnosticsContract.innerHTML = `
      <article class="panel-card">
        <h4>Data contract / ClickHouse</h4>
        ${renderDataContract(contract)}
      </article>
    `;

    el.diagnosticsTroubleshooting.innerHTML = renderTroubleshooting(config, auth, persistence);
  }

  function renderPersistence(persistence) {
    const tables = persistence.tables || {};
    const existingTables = persistence.existing_tables || [];
    const statusRows = [
      ["Включён", boolText(persistence.enabled)],
      ["Настроен", boolText(persistence.configured)],
      ["Доступен", boolText(persistence.reachable)],
      ["Схема готова", boolText(persistence.schema_ready)],
      ["Host", persistence.host || "—"],
      ["База", persistence.database || "—"],
      ["User", persistence.user || "—"],
    ];

    return `
      <div class="result-stack">
        ${renderKvGrid(statusRows)}
        ${
          Object.keys(tables).length
            ? `<div class="list-box">
                ${Object.entries(tables)
                  .map(
                    ([tableName, inserted]) => `
                      <div class="list-row">
                        <div class="list-row__head">
                          <span class="list-row__title">${esc(tableName)}</span>
                        </div>
                        <div class="list-row__text">Синхронизировано строк: ${esc(stringify(inserted))}</div>
                      </div>
                    `,
                  )
                  .join("")}
              </div>`
            : ""
        }
        ${
          existingTables.length
            ? `<div class="result-summary"><strong>Существующие таблицы:</strong> ${esc(existingTables.join(", "))}</div>`
            : ""
        }
        ${
          persistence.last_error || persistence.reason
            ? `<div class="error-state">${esc(persistence.last_error || persistence.reason)}</div>`
            : ""
        }
      </div>
    `;
  }

  function renderDataContract(contract) {
    const database = contract.database || {};
    const tables = contract.tables || [];
    const uiOutputs = contract.ui_outputs || [];

    return `
      <div class="result-stack">
        <div class="result-summary">
          <strong>База:</strong> ${esc(database.engine || "ClickHouse")} · ${esc(database.host || "—")}:${esc(database.port || "—")} · ${esc(database.database || "—")}
        </div>
        <div class="result-summary">
          <strong>Режим:</strong> ${esc(database.mode || "runtime_contract")} · <strong>Secure:</strong> ${esc(boolText(database.secure))}
        </div>
        <div class="list-box">
          ${tables
            .map(
              (table) => `
                <article class="list-row">
                  <div class="list-row__head">
                    <span class="list-row__title">${esc(table.name)}</span>
                    <span class="list-row__meta mono-text">${esc((table.order_by || []).join(", "))}</span>
                  </div>
                  <div class="list-row__text">${esc(table.purpose || "")}</div>
                  <div class="mono-text">${esc((table.columns || []).map((column) => `${column.name}:${column.type}`).join(" · "))}</div>
                </article>
              `,
            )
            .join("")}
        </div>
        <article class="panel-card">
          <h4>Связь UI → данные</h4>
          ${renderTable(uiOutputs, [
            ["section", "Раздел"],
            ["source_tables", "Таблицы", "array"],
            ["keys", "Ключи", "array"],
          ])}
        </article>
      </div>
    `;
  }

  function renderTroubleshooting(config, auth, persistence) {
    const missingVars = config.env_substitution?.missing_vars || [];
    const failedChecks = (auth.checks || []).filter((item) => !item.auth_ok);
    const tips = [];

    if (!config.env?.exists) {
      tips.push("Файл .env не найден в корне проекта.");
    }
    if (missingVars.length) {
      tips.push(`Не подставились env-переменные: ${missingVars.join(", ")}.`);
    }
    if (failedChecks.length) {
      tips.push("Есть кабинеты с невалидной Meta-авторизацией. Проверьте токены и права system user.");
    }
    if (persistence.enabled && !persistence.configured) {
      tips.push("ClickHouse включён, но параметры подключения не заполнены.");
    }
    if (persistence.enabled && persistence.configured && !persistence.reachable) {
      tips.push("ClickHouse не отвечает. Проверьте host, порт, пароль и сетевой доступ.");
    }
    if (!tips.length) {
      tips.push("Базовая конфигурация выглядит корректно. Можно переходить к проверке summaries и skill-сценариев.");
    }
    return `<div class="list-box">${tips.map((tip) => `<div class="list-row__text">${esc(tip)}</div>`).join("")}</div>`;
  }

  function renderSkillCatalog(skills) {
    if (!skills.length) {
      renderEmpty(el.skillsCatalog, "Навыки пока не зарегистрированы.");
      return;
    }
    if (!skills.find((item) => item.id === state.selectedSkillId)) {
      state.selectedSkillId = skills[0].id;
    }
    state.selectedSkill = skills.find((item) => item.id === state.selectedSkillId) || skills[0];
    el.skillsCatalog.innerHTML = skills
      .map(
        (skill) => `
          <button type="button" class="skill-card ${skill.id === state.selectedSkillId ? "is-selected" : ""}" data-skill-id="${esc(skill.id)}">
            <span class="skill-card__title">${esc(skill.title)}</span>
            <span class="skill-card__description">${esc(skill.description || "")}</span>
            <span class="skill-card__meta mono-text">${esc(skill.mcp_tool || "")}</span>
          </button>
        `,
      )
      .join("");
    el.skillsPromptBox.value = state.selectedSkill?.prompt || "";
    el.skillsCatalog.querySelectorAll("[data-skill-id]").forEach((button) => {
      button.addEventListener("click", () => {
        state.selectedSkillId = button.getAttribute("data-skill-id") || "";
        renderSkillCatalog(skills);
        renderSelectedSkillFromWorkspace();
      });
    });
  }

  function renderSelectedSkillFromWorkspace() {
    if (!state.workspace?.skills) {
      renderEmpty(el.skillsResult, "Workspace ещё не загрузился.");
      return;
    }
    const skillResult = skillResultFromWorkspace(state.selectedSkillId, state.workspace.skills);
    renderSkillResult(skillResult);
  }

  function skillResultFromWorkspace(skillId, skills) {
    switch (skillId) {
      case "budget_summary":
        return skills.budget_summary || null;
      case "disable_candidates":
        return skills.disable_candidates || null;
      case "scale_candidates":
        return skills.scale_candidates || null;
      case "collect_report":
      default:
        return skills.collect_report || null;
    }
  }

  async function runSelectedSkill() {
    if (!state.selectedSkill) {
      toast("Навык не выбран.", "info");
      return;
    }

    el.skillsRunSelected.classList.add("is-loading");
    el.skillsRunSelected.disabled = true;
    renderLoading(el.skillsResult, "Запускаем навык…");

    try {
      let payload;
      if (state.selectedSkillId === "budget_summary") {
        payload = await api.budgetSkill({ account_id: state.accountId, end_date: state.endDate });
      } else if (state.selectedSkillId === "disable_candidates") {
        payload = await api.disableSkill({
          account_id: state.accountId,
          end_date: state.endDate,
          lookback_days: el.wasteLookback.value || "7",
          entity_level: el.wasteLevel.value,
          min_spend: el.wasteMinSpend.value || "20",
          limit: "10",
        });
      } else if (state.selectedSkillId === "scale_candidates") {
        payload = await api.scaleSkill({
          account_id: state.accountId,
          end_date: state.endDate,
          lookback_days: el.performersLookback.value || "7",
          entity_level: el.performersLevel.value,
          max_cost_per_result: "20",
          min_conversions: "1",
          limit: "10",
        });
      } else {
        payload = await api.reportSkill({
          account_id: state.accountId,
          end_date: state.endDate,
          lookback_days: "7",
          entity_level: el.performersLevel.value,
          min_spend: el.wasteMinSpend.value || "20",
          max_cost_per_result: "20",
        });
      }
      renderSkillResult(payload);
      toast("Навык выполнен.", "success");
    } catch (error) {
      renderError(el.skillsResult, error.message || "Не удалось выполнить навык.");
      toast(error.message || "Не удалось выполнить навык.", "error");
    } finally {
      el.skillsRunSelected.classList.remove("is-loading");
      el.skillsRunSelected.disabled = false;
    }
  }

  function renderSkillResult(payload) {
    if (!payload) {
      renderEmpty(el.skillsResult, "Результат навыка пока не получен.");
      return;
    }

    const sections = [];
    if (payload.summary) {
      sections.push(`<div class="result-summary"><strong>${esc(payload.title || "Навык")}</strong><p>${esc(payload.summary)}</p></div>`);
    }

    if (Array.isArray(payload.candidates) && payload.candidates.length) {
      sections.push(
        renderTable(payload.candidates, [
          ["entity_name", "Сущность"],
          ["spend", "Расход", "currency"],
          ["conversions", "Конверсии", "number"],
          ["cost_per_result", "Цена результата", "currency"],
          ["reason", "Причина"],
          ["source", "Источник"],
        ]),
      );
    }

    if (Array.isArray(payload.periods) && payload.periods.length) {
      sections.push(
        renderTable(payload.periods, [
          ["period", "Период"],
          ["spend", "Расход", "currency"],
          ["impressions", "Показы", "number"],
          ["clicks", "Клики", "number"],
          ["conversions", "Конверсии", "number"],
        ]),
      );
    }

    if (payload.billing) {
      sections.push(`<article class="panel-card"><h4>Billing snapshot</h4>${renderKvGrid(Object.entries(payload.billing || {}))}</article>`);
    }

    if (payload.sections) {
      sections.push(`
        <article class="panel-card">
          <h4>Сводка по секциям</h4>
          <div class="result-stack">
            ${Object.entries(payload.sections)
              .map(([key, value]) => `<div class="result-summary"><strong>${esc(key)}</strong><p>${esc(stringify(value.summary || value.title || value.skill || value))}</p></div>`)
              .join("")}
          </div>
        </article>
      `);
    }

    if (Array.isArray(payload.next_actions) && payload.next_actions.length) {
      sections.push(`
        <article class="panel-card">
          <h4>Следующие шаги</h4>
          <ul class="plain-list">
            ${payload.next_actions.map((item) => `<li>${esc(item)}</li>`).join("")}
          </ul>
        </article>
      `);
    }

    if (Array.isArray(payload.recommended_actions) && payload.recommended_actions.length) {
      sections.push(`
        <article class="panel-card">
          <h4>Рекомендованные действия</h4>
          <ul class="plain-list">
            ${payload.recommended_actions.map((item) => `<li>${esc(item)}</li>`).join("")}
          </ul>
        </article>
      `);
    }

    el.skillsResult.innerHTML = sections.join("") || renderEmptyMarkup("Результат навыка пустой.");
  }

  function renderPreview(preview) {
    el.drawer.classList.add("is-open");
    el.drawer.setAttribute("aria-hidden", "false");
    el.drawerBackdrop.hidden = false;
    el.drawerRiskFlags.innerHTML = (preview.risk_flags || []).length
      ? (preview.risk_flags || []).map((flag) => `<span class="status-chip is-warning">${esc(flag)}</span>`).join("")
      : `<span class="status-chip is-success">Рисков не выявлено</span>`;
    el.drawerJson.textContent = stringify(preview);
  }

  function populateAccountSelect(accounts) {
    const currentValue = state.accountId || el.filterAccountId.value;
    const options = [`<option value="">Выбрать аккаунт</option>`]
      .concat(
        accounts.map(
          (account) =>
            `<option value="${escAttr(account.account_id)}" ${account.account_id === currentValue ? "selected" : ""}>${esc(account.name)} · ${esc(account.account_id)}</option>`,
        ),
      )
      .join("");
    el.filterAccountId.innerHTML = options;
  }

  function syncFiltersFromForm() {
    state.accountId = (el.filterAccountId.value || "").trim();
    state.endDate = el.filterEndDate.value || state.endDate;
  }

  function setActiveSection(section) {
    el.navButtons.forEach((button) => {
      const active = button.dataset.section === section;
      button.classList.toggle("is-active", active);
      button.setAttribute("aria-current", active ? "page" : "false");
    });
    el.panels.forEach((panel) => {
      const active = panel.dataset.sectionPanel === section;
      panel.classList.toggle("is-active", active);
      panel.hidden = !active;
    });
  }

  function setStatus(kind, text) {
    el.statusDot.dataset.state = kind;
    el.statusText.textContent = text;
  }

  function toast(message, tone = "info") {
    if (!el.toastRoot) return;
    const item = document.createElement("div");
    item.className = `toast toast--${tone}`;
    item.textContent = message;
    el.toastRoot.appendChild(item);
    window.setTimeout(() => {
      item.classList.add("is-hidden");
      window.setTimeout(() => item.remove(), 220);
    }, 2800);
  }

  function renderLoading(container, text) {
    container.innerHTML = `<div class="empty-state"><p>${esc(text)}</p></div>`;
  }

  function renderError(container, text) {
    container.innerHTML = `<div class="error-state">${esc(text)}</div>`;
  }

  function renderEmpty(container, text) {
    container.innerHTML = renderEmptyMarkup(text);
  }

  function renderEmptyMarkup(text) {
    return `<div class="empty-state"><p>${esc(text)}</p></div>`;
  }

  function renderKvGrid(entries) {
    return `
      <div class="kv-grid">
        ${entries
          .map(([label, value]) => `
            <div class="kv-row">
              <span>${esc(label)}</span>
              <strong>${esc(stringify(value))}</strong>
            </div>
          `)
          .join("")}
      </div>
    `;
  }

  function renderTable(rows, columns) {
    if (!rows.length) {
      return renderEmptyMarkup("Нет данных для отображения.");
    }
    return `
      <div class="table-shell">
        <table class="data-table">
          <thead>
            <tr>${columns.map(([, label]) => `<th>${esc(label)}</th>`).join("")}</tr>
          </thead>
          <tbody>
            ${rows
              .map(
                (row) => `
                  <tr>
                    ${columns
                      .map(([key, , format]) => `<td>${formatCell(readPath(row, key), format, row.currency)}</td>`)
                      .join("")}
                  </tr>
                `,
              )
              .join("")}
          </tbody>
        </table>
      </div>
    `;
  }

  function formatCell(value, format, currencyHint) {
    if (format === "boolean") {
      return esc(boolText(Boolean(value)));
    }
    if (format === "array") {
      return esc(Array.isArray(value) ? value.join(", ") : stringify(value));
    }
    return esc(formatValue(value, format, currencyHint));
  }

  function formatValue(value, format, currencyHint = "USD") {
    if (value === null || value === undefined || value === "") {
      return "—";
    }
    if (format === "currency") {
      return formatCurrency(value, currencyHint);
    }
    if (format === "number") {
      return formatNumber(value);
    }
    if (format === "percent") {
      return formatPercent(value);
    }
    return stringify(value);
  }

  function formatCurrency(value, currency = "USD") {
    const amount = Number(value || 0);
    return new Intl.NumberFormat("ru-RU", {
      style: "currency",
      currency: currency || "USD",
      maximumFractionDigits: 2,
    }).format(amount);
  }

  function formatNumber(value) {
    return new Intl.NumberFormat("ru-RU", { maximumFractionDigits: 2 }).format(Number(value || 0));
  }

  function formatPercent(value) {
    const number = Number(value || 0);
    if (number > 0 && number <= 1) {
      return `${new Intl.NumberFormat("ru-RU", { maximumFractionDigits: 2 }).format(number * 100)}%`;
    }
    return `${new Intl.NumberFormat("ru-RU", { maximumFractionDigits: 2 }).format(number)}%`;
  }

  function boolText(value) {
    return value ? "Да" : "Нет";
  }

  function stringify(value) {
    if (value === null || value === undefined || value === "") {
      return "—";
    }
    if (typeof value === "string") {
      return value;
    }
    if (typeof value === "number" || typeof value === "boolean") {
      return String(value);
    }
    try {
      return JSON.stringify(value, null, 2);
    } catch (error) {
      return String(value);
    }
  }

  function describePersistenceShort(persistence) {
    const status = persistence.status || (persistence.reachable ? "ready" : "unknown");
    if (status === "ok") {
      return "Синхронизация выполнена";
    }
    if (status === "failed") {
      return `Ошибка: ${persistence.reason || persistence.last_error || "unknown"}`;
    }
    if (status === "skipped") {
      return `Пропущено: ${persistence.reason || "unknown"}`;
    }
    return `Статус: ${status}`;
  }

  function parseIds(value) {
    return String(value || "")
      .split(/[\s,;]+/)
      .map((item) => item.trim())
      .filter(Boolean);
  }

  function toNumberOrNull(value) {
    const text = String(value || "").trim();
    if (!text) return null;
    const number = Number(text.replace(",", "."));
    return Number.isFinite(number) ? number : null;
  }

  function emptyToNull(value) {
    const text = String(value || "").trim();
    return text ? text : null;
  }

  function withQuery(params) {
    const query = new URLSearchParams();
    Object.entries(params || {}).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== "") {
        query.set(key, String(value));
      }
    });
    const text = query.toString();
    return text ? `?${text}` : "";
  }

  async function requestJson(url, method = "GET", body) {
    const response = await fetch(url, {
      method,
      headers: body ? { "Content-Type": "application/json" } : undefined,
      body: body ? JSON.stringify(body) : undefined,
    });
    const text = await response.text();
    let payload = {};
    if (text) {
      try {
        payload = JSON.parse(text);
      } catch (error) {
        throw new Error(text);
      }
    }
    if (!response.ok) {
      throw new Error(payload.error || payload.message || `HTTP ${response.status}`);
    }
    return payload;
  }

  async function copyText(text) {
    if (navigator.clipboard?.writeText) {
      await navigator.clipboard.writeText(text);
      return;
    }
    const area = document.createElement("textarea");
    area.value = text;
    area.setAttribute("readonly", "readonly");
    area.style.position = "fixed";
    area.style.opacity = "0";
    document.body.appendChild(area);
    area.select();
    document.execCommand("copy");
    area.remove();
  }

  function readPath(source, path) {
    return String(path)
      .split(".")
      .reduce((acc, key) => (acc && typeof acc === "object" ? acc[key] : undefined), source);
  }

  function esc(value) {
    return String(value ?? "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/\"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }

  function escAttr(value) {
    return esc(value);
  }

  function statusClass(status) {
    const normalized = String(status || "").toUpperCase();
    if (["ACTIVE", "OK", "READY", "SUCCESS"].includes(normalized)) return "is-success";
    if (["PAUSED", "PENDING_REVIEW", "LEARNING", "LIMITED"].includes(normalized)) return "is-warning";
    if (["DISAPPROVED", "ERROR", "FAILED", "REJECTED"].includes(normalized)) return "is-danger";
    return "is-neutral";
  }

  init();
})();

(() => {
  "use strict";

  const state = {
    activeSection: "overview",
    filters: {
      accountId: "",
      endDate: "",
    },
  };

  const dom = {
    statusDot: document.getElementById("status-dot"),
    statusText: document.getElementById("status-text"),
    lastRefreshTime: document.getElementById("last-refresh-time"),
    accountName: document.getElementById("topbar-account-name"),
    accountFilter: document.getElementById("filter-account-id"),
    dateFilter: document.getElementById("filter-end-date"),
    toastRoot: document.getElementById("toast-root"),
    drawer: document.getElementById("preview-drawer"),
    drawerBackdrop: document.getElementById("drawer-backdrop"),
    drawerTitle: document.getElementById("drawer-title"),
    drawerJson: document.getElementById("drawer-json"),
    drawerRisks: document.getElementById("drawer-risk-flags"),
  };

  const containers = {
    overviewMetrics: document.getElementById("overview-metrics"),
    overviewAccount: document.getElementById("overview-account"),
    overviewStatuses: document.getElementById("overview-statuses"),
    structure: document.getElementById("structure-content"),
    issues: document.getElementById("issues-content"),
    assets: document.getElementById("assets-content"),
    performers: document.getElementById("performers-content"),
    waste: document.getElementById("waste-content"),
    diagnosticsHealth: document.getElementById("diagnostics-health"),
    diagnosticsConfig: document.getElementById("diagnostics-config"),
    diagnosticsAuth: document.getElementById("diagnostics-auth"),
    diagnosticsTroubleshooting: document.getElementById("diagnostics-troubleshooting-content"),
  };

  const format = {
    number(value) {
      return new Intl.NumberFormat("ru-RU").format(Number(value || 0));
    },
    money(value) {
      return new Intl.NumberFormat("ru-RU", {
        style: "currency",
        currency: "USD",
        maximumFractionDigits: 2,
      }).format(Number(value || 0));
    },
    percent(value) {
      return `${Number(value || 0).toFixed(2)}%`;
    },
    dateTime(value) {
      if (!value) {
        return "";
      }
      const date = new Date(value);
      if (Number.isNaN(date.getTime())) {
        return "";
      }
      return new Intl.DateTimeFormat("ru-RU", {
        dateStyle: "short",
        timeStyle: "short",
      }).format(date);
    },
  };

  function esc(value) {
    return String(value ?? "")
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#39;");
  }

  function buildQuery(params) {
    const query = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (value === null || value === undefined || value === "") {
        return;
      }
      query.set(key, String(value));
    });
    return query.toString() ? `?${query.toString()}` : "";
  }

  function normalizeErrorMessage(error) {
    const raw = String(error?.message || "Ошибка загрузки");
    if (raw.includes("facebook-business SDK is not installed")) {
      return "На сервере не установлен facebook-business SDK.";
    }
    if (raw.includes("OAuthException") || raw.includes("code\": 190") || raw.includes("code: 190")) {
      return "Ошибка авторизации Meta API (OAuthException 190). Проверьте токен и account_id в конфиге.";
    }
    const firstLine = raw
      .split(/\r?\n/)
      .map((line) => line.trim())
      .find(Boolean);
    if (!firstLine) {
      return "Ошибка загрузки";
    }
    return firstLine.length > 200 ? `${firstLine.slice(0, 197)}...` : firstLine;
  }

  async function requestJson(url, options = {}) {
    const response = await fetch(url, options);
    let payload = null;
    try {
      payload = await response.json();
    } catch {
      payload = {};
    }
    if (!response.ok) {
      throw new Error(payload.error || `Ошибка HTTP ${response.status}`);
    }
    return payload;
  }

  const api = {
    dashboard() {
      const query = buildQuery({
        account_id: state.filters.accountId,
        end_date: state.filters.endDate,
      });
      return requestJson(`/api/meta/dashboard${query}`);
    },
    structure() {
      const query = buildQuery({ account_id: state.filters.accountId });
      return requestJson(`/api/meta/campaign-structure${query}`);
    },
    issues() {
      const query = buildQuery({ account_id: state.filters.accountId, limit: 30 });
      return requestJson(`/api/meta/delivery-issues${query}`);
    },
    assets() {
      const query = buildQuery({ account_id: state.filters.accountId });
      return requestJson(`/api/meta/assets${query}`);
    },
    performers(filters) {
      const query = buildQuery({
        account_id: state.filters.accountId,
        end_date: state.filters.endDate,
        lookback_days: filters.lookbackDays,
        entity_level: filters.entityLevel,
        metric: filters.metric,
        limit: 12,
      });
      return requestJson(`/api/meta/top-performers${query}`);
    },
    noResultSpend(filters) {
      const query = buildQuery({
        account_id: state.filters.accountId,
        end_date: state.filters.endDate,
        lookback_days: filters.lookbackDays,
        entity_level: filters.entityLevel,
        min_spend: filters.minSpend,
        limit: 20,
      });
      return requestJson(`/api/meta/no-result-entities${query}`);
    },
    configDiagnostics() {
      return requestJson("/api/meta/config-diagnostics");
    },
    authDiagnostics() {
      return requestJson("/api/meta/auth-diagnostics");
    },
    debugHealth() {
      return requestJson("/api/meta/debug-health");
    },
    previewCloneCampaign(payload) {
      return requestJson("/api/meta/preview/clone-campaign", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
    },
    previewUpdateCampaignBudget(payload) {
      return requestJson("/api/meta/preview/update-campaign-budget", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
    },
    previewPauseAds(payload) {
      return requestJson("/api/meta/preview/pause-ads", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
    },
  };

  function showToast(message, variant = "info") {
    const toast = document.createElement("div");
    toast.className = `toast toast--${variant}`;
    toast.textContent = message;
    dom.toastRoot.appendChild(toast);

    setTimeout(() => {
      toast.remove();
    }, 3800);
  }

  function setStatus(kind, text) {
    dom.statusDot.className = `status-dot ${kind === "ok" ? "is-ok" : kind === "error" ? "is-error" : "is-loading"}`;
    dom.statusText.textContent = text;
  }

  function stampRefreshTime() {
    dom.lastRefreshTime.textContent = `Обновлено: ${new Intl.DateTimeFormat("ru-RU", { timeStyle: "medium" }).format(new Date())}`;
  }

  function renderLoading(container, label = "Загрузка данных…") {
    container.innerHTML = `<div class="loading-state">${esc(label)}</div>`;
  }

  function renderEmpty(container, label = "Нет данных для отображения") {
    container.innerHTML = `<div class="empty-state">${esc(label)}</div>`;
  }

  function renderError(container, error) {
    container.innerHTML = `<div class="error-state">${esc(error)}</div>`;
  }

  function renderTable(container, columns, rows, emptyText) {
    if (!rows.length) {
      renderEmpty(container, emptyText);
      return;
    }
    const headerHtml = columns.map((column) => `<th>${esc(column.label)}</th>`).join("");
    const rowsHtml = rows
      .map((row) => {
        const cells = columns
          .map((column) => {
            const raw = typeof column.get === "function" ? column.get(row) : row[column.key];
            const value = typeof column.format === "function" ? column.format(raw, row) : raw;
            return `<td>${esc(value ?? "—")}</td>`;
          })
          .join("");
        return `<tr>${cells}</tr>`;
      })
      .join("");

    container.innerHTML = `
      <div class="table-wrap">
        <table>
          <thead><tr>${headerHtml}</tr></thead>
          <tbody>${rowsHtml}</tbody>
        </table>
      </div>
    `;
  }

  function statusBadge(status) {
    const normalized = String(status || "UNKNOWN").toUpperCase();
    const warningStatuses = new Set(["DISAPPROVED", "WITH_ISSUES", "REJECTED", "PAUSED"]);
    const classes = warningStatuses.has(normalized) ? "status-chip is-warning" : "status-chip";
    return `<span class="${classes}">${esc(normalized)}</span>`;
  }

  function renderOverview(data) {
    const periods = data.spend?.periods || [];
    const today = periods.find((item) => item.period === "today") || {};
    const week = periods.find((item) => item.period === "last_7_days") || {};
    const month = periods.find((item) => item.period === "last_30_days") || {};

    const metrics = [
      { label: "Расход сегодня", value: format.money(today.spend), hint: "Текущие сутки" },
      { label: "Расход за 7 дней", value: format.money(week.spend), hint: "Короткое окно" },
      { label: "Расход за 30 дней", value: format.money(month.spend), hint: "Месячный диапазон" },
      { label: "Проблемы доставки", value: format.number(data.issues?.issue_count), hint: "Требуют проверки" },
    ];

    containers.overviewMetrics.innerHTML = metrics
      .map(
        (metric) => `
          <article class="metric-card">
            <div class="metric-card__label">${esc(metric.label)}</div>
            <div class="metric-card__value">${esc(metric.value)}</div>
            <div class="metric-card__hint">${esc(metric.hint)}</div>
          </article>
        `,
      )
      .join("");

    const account = data.account || {};
    const accountName = account.name || account.account_name || data.account_id || "Meta Ads account";
    dom.accountName.textContent = `${accountName}${data.account_id ? ` (${data.account_id})` : ""}`;

    const keyValues = [
      ["Название", accountName],
      ["Account ID", data.account_id || "—"],
      ["Валюта", account.currency || "—"],
      ["Часовой пояс", account.timezone_name || "—"],
      ["Кампаний", format.number(data.totals?.campaigns)],
      ["Ad set", format.number(data.totals?.adsets)],
      ["Объявлений", format.number(data.totals?.ads)],
    ];

    containers.overviewAccount.innerHTML = `
      <div class="kv-grid">
        ${keyValues
          .map(
            ([label, value]) => `
              <div class="kv-row">
                <span>${esc(label)}</span>
                <strong>${esc(value)}</strong>
              </div>
            `,
          )
          .join("")}
      </div>
    `;

    const statuses = data.statuses || {};
    const groups = [
      ["Campaign statuses", statuses.campaigns || {}],
      ["Ad set statuses", statuses.adsets || {}],
      ["Ad statuses", statuses.ads || {}],
    ];

    containers.overviewStatuses.innerHTML = groups
      .map(([title, group]) => {
        const entries = Object.entries(group);
        return `
          <article class="status-list">
            <h5>${esc(title)}</h5>
            <div class="status-chips">
              ${entries.length ? entries.map(([status, count]) => `${statusBadge(status)} ${esc(format.number(count))}`).join("") : '<span class="status-chip">Нет данных</span>'}
            </div>
          </article>
        `;
      })
      .join("");
  }

  function renderStructure(data) {
    const rows = data.rows || [];
    if (!rows.length) {
      renderEmpty(containers.structure, "Структура кампаний пока пустая.");
      return;
    }

    containers.structure.innerHTML = `
      <div class="structure-list">
        ${rows
          .map((campaign) => {
            const adsets = campaign.adsets || [];
            return `
              <details class="structure-item">
                <summary>
                  <span class="structure-item__name">${esc(campaign.campaign_name || campaign.campaign_id || "Без названия")}</span>
                  ${statusBadge(campaign.campaign_status || "UNKNOWN")}
                </summary>
                <div class="structure-item__body">
                  <div class="list-row__meta">Campaign ID: ${esc(campaign.campaign_id || "—")}</div>
                  ${
                    adsets.length
                      ? adsets
                          .map((adset) => {
                            const ads = adset.ads || [];
                            return `
                              <div class="list-row">
                                <div class="list-row__head">
                                  <div class="list-row__title">${esc(adset.adset_name || adset.adset_id || "Ad set")}</div>
                                  ${statusBadge(adset.adset_status || "UNKNOWN")}
                                </div>
                                <div class="list-row__meta">Ad set ID: ${esc(adset.adset_id || "—")}</div>
                                <ul class="structure-sublist">
                                  ${
                                    ads.length
                                      ? ads
                                          .map(
                                            (ad) =>
                                              `<li>${esc(ad.ad_name || ad.ad_id || "Ad")}: ${esc(ad.ad_status || "UNKNOWN")}</li>`,
                                          )
                                          .join("")
                                      : "<li>Объявления не найдены</li>"
                                  }
                                </ul>
                              </div>
                            `;
                          })
                          .join("")
                      : '<div class="empty-state">Ad set не найдены.</div>'
                  }
                </div>
              </details>
            `;
          })
          .join("")}
      </div>
    `;
  }

  function renderIssues(data) {
    const rows = data.issues || data.rows || [];
    if (!rows.length) {
      renderEmpty(containers.issues, "Проблемы доставки не обнаружены.");
      return;
    }

    containers.issues.innerHTML = `
      <div class="list-box">
        ${rows
          .map(
            (row) => `
              <article class="list-row">
                <div class="list-row__head">
                  <div class="list-row__title">${esc(row.name || row.ad_name || row.id || "Сущность")}</div>
                  ${statusBadge(row.effective_status || row.status || "UNKNOWN")}
                </div>
                <div class="list-row__text">${esc(row.issue_summary || row.review_feedback || "Meta сообщает о проблеме доставки или модерации.")}</div>
              </article>
            `,
          )
          .join("")}
      </div>
    `;
  }

  function renderAssets(data) {
    const summary = data.summary || {};
    const rows = [
      { name: "Страницы", value: summary.pages },
      { name: "Instagram", value: summary.instagram_accounts },
      { name: "Пиксели", value: summary.pixels },
      { name: "Кастомные конверсии", value: summary.custom_conversions },
      { name: "Лид-формы", value: summary.lead_forms },
    ];
    renderTable(
      containers.assets,
      [
        { key: "name", label: "Актив" },
        { key: "value", label: "Количество", format: (value) => format.number(value) },
      ],
      rows,
      "Нет данных по подключённым активам.",
    );
  }

  function renderPerformers(data) {
    const rows = data.rows || [];
    renderTable(
      containers.performers,
      [
        { key: "entity_name", label: "Сущность", format: (value, row) => value || row.campaign_name || row.entity_id || "—" },
        { key: "spend", label: "Расход", format: (value) => format.money(value) },
        { key: "conversions", label: "Конверсии", format: (value) => format.number(value) },
        { key: "cost_per_result", label: "Цена за результат", format: (value) => format.money(value) },
        { key: "ctr", label: "CTR", format: (value) => format.percent(value) },
      ],
      rows,
      "Нет результатов по заданным параметрам.",
    );
  }

  function renderNoResultSpend(data) {
    const rows = data.rows || [];
    renderTable(
      containers.waste,
      [
        { key: "entity_name", label: "Сущность", format: (value, row) => value || row.campaign_name || row.entity_id || "—" },
        { key: "spend", label: "Расход", format: (value) => format.money(value) },
        { key: "conversions", label: "Конверсии", format: (value) => format.number(value) },
        { key: "ctr", label: "CTR", format: (value) => format.percent(value) },
      ],
      rows,
      "Сущностей с расходом без результата не найдено.",
    );
  }

  function renderDiagnostics(configData, authData, healthData) {
    const healthStatus = String(healthData?.status || "unknown").toUpperCase();
    containers.diagnosticsHealth.innerHTML = `
      <article class="diag-health-card">
        <h4>Debug health</h4>
        <div class="status-chips">${healthStatus === "OK" ? statusBadge("ok") : statusBadge(healthStatus)}</div>
        <div class="kv-grid" style="margin-top: 8px;">
          <div class="kv-row"><span>accounts checked</span><strong>${esc(format.number(healthData?.auth?.accounts_checked || 0))}</strong></div>
          <div class="kv-row"><span>auth ok</span><strong>${esc(format.number(healthData?.auth?.auth_ok_count || 0))}</strong></div>
          <div class="kv-row"><span>auth failed</span><strong>${esc(format.number(healthData?.auth?.auth_failed_count || 0))}</strong></div>
        </div>
      </article>
      <article class="diag-health-card">
        <h4>Runtime config</h4>
        <div class="kv-grid">
          <div class="kv-row"><span>.env найден</span><strong>${configData?.env?.exists ? "Да" : "Нет"}</strong></div>
          <div class="kv-row"><span>ads_config.yaml найден</span><strong>${configData?.connections?.primary_exists ? "Да" : "Нет"}</strong></div>
          <div class="kv-row"><span>provider meta_ads загружен</span><strong>${configData?.provider_loaded ? "Да" : "Нет"}</strong></div>
          <div class="kv-row"><span>аккаунтов в runtime</span><strong>${esc(format.number(configData?.runtime?.accounts_total || 0))}</strong></div>
          <div class="kv-row"><span>env подстановки</span><strong>${configData?.env_substitution?.all_resolved ? "ОК" : "Есть пропуски"}</strong></div>
        </div>
      </article>
    `;

    const accountRows = configData?.runtime?.accounts || [];
    renderTable(
      containers.diagnosticsConfig,
      [
        { key: "name", label: "Аккаунт" },
        { key: "account_id", label: "account_id" },
        { key: "status", label: "status" },
        { key: "app_id", label: "app_id" },
        { key: "token", label: "access_token", get: (row) => row.access_token?.masked || "(пусто)" },
        { key: "secret", label: "app_secret", get: (row) => row.app_secret?.masked || "(пусто)" },
        {
          key: "env",
          label: "env refs",
          get: (row) => {
            const tokenVars = row.access_token?.env_ref?.vars || [];
            const secretVars = row.app_secret?.env_ref?.vars || [];
            const vars = [...new Set([...tokenVars, ...secretVars])];
            return vars.length ? vars.join(", ") : "(literal)";
          },
        },
        {
          key: "resolved",
          label: "env resolved",
          get: (row) => {
            const tokenOk = row.access_token?.env_ref?.resolved ?? true;
            const secretOk = row.app_secret?.env_ref?.resolved ?? true;
            return tokenOk && secretOk ? "yes" : "no";
          },
        },
      ],
      accountRows,
      "Аккаунты не найдены в runtime-конфиге.",
    );

    const authRows = authData?.checks || [];
    renderTable(
      containers.diagnosticsAuth,
      [
        { key: "name", label: "Аккаунт" },
        { key: "account_id", label: "account_id" },
        { key: "auth_ok", label: "auth check", get: (row) => (row.auth_ok ? "ok" : "failed") },
        { key: "account_name_from_meta", label: "Meta name", get: (row) => row.account_name_from_meta || "—" },
        { key: "meta_account_status", label: "Meta status", get: (row) => row.meta_account_status ?? "—" },
        { key: "access_token_masked", label: "Token (masked)" },
        { key: "app_secret_masked", label: "Secret (masked)" },
        { key: "error", label: "Ошибка", get: (row) => row.error || "—" },
      ],
      authRows,
      "Нет данных по auth-проверке.",
    );

    const troubleshooting = [];
    if (!configData?.env?.exists) {
      troubleshooting.push("Файл .env не найден в корне проекта. Проверьте путь и имя файла.");
    }
    if (!configData?.connections?.primary_exists) {
      troubleshooting.push("ads_config.yaml не найден. Используется example-конфиг с шаблонными значениями.");
    }
    const missingVars = configData?.env_substitution?.missing_vars || [];
    if (missingVars.length) {
      troubleshooting.push(`Не заданы переменные окружения: ${missingVars.join(", ")}.`);
    }
    const failedAuth = authRows.filter((item) => !item.auth_ok);
    if (failedAuth.length) {
      troubleshooting.push("Есть аккаунты с неуспешной авторизацией Meta API. Проверьте токен, app_secret и доступы к ad account.");
    }
    if (!troubleshooting.length) {
      troubleshooting.push("Ключевых проблем не обнаружено. Конфиг и базовая auth-проверка выглядят корректно.");
    }

    containers.diagnosticsTroubleshooting.innerHTML = `
      <div class="diag-stack">
        ${troubleshooting.map((line) => `<div class="list-row__text">• ${esc(line)}</div>`).join("")}
        <div class="mono-text">runtime source: ${esc(configData?.connections?.runtime_source || "—")}</div>
        <div class="mono-text">raw source: ${esc(configData?.connections?.raw_source_path || "—")}</div>
      </div>
    `;
  }

  function openPreviewDrawer(payload, title) {
    dom.drawerTitle.textContent = title;
    dom.drawerJson.textContent = JSON.stringify(payload, null, 2);

    const risks = payload.risk_flags || [];
    dom.drawerRisks.innerHTML = risks.length
      ? risks.map((risk) => `<div class="risk-flag">${esc(risk)}</div>`).join("")
      : '<div class="empty-state">Risk flags не обнаружены.</div>';

    dom.drawer.classList.add("is-open");
    dom.drawer.setAttribute("aria-hidden", "false");
    dom.drawerBackdrop.hidden = false;
  }

  function closePreviewDrawer() {
    dom.drawer.classList.remove("is-open");
    dom.drawer.setAttribute("aria-hidden", "true");
    dom.drawerBackdrop.hidden = true;
  }

  async function loadOverview() {
    renderLoading(containers.overviewMetrics, "Загружаем KPI…");
    renderLoading(containers.overviewAccount, "Загружаем паспорт аккаунта…");
    renderLoading(containers.overviewStatuses, "Загружаем статусы…");

    const data = await api.dashboard();
    renderOverview(data);
  }

  async function loadStructure() {
    renderLoading(containers.structure, "Загружаем структуру кампаний…");
    const data = await api.structure();
    renderStructure(data);
  }

  async function loadIssues() {
    renderLoading(containers.issues, "Загружаем проблемы доставки…");
    const data = await api.issues();
    renderIssues(data);
  }

  async function loadAssets() {
    renderLoading(containers.assets, "Загружаем активы…");
    const data = await api.assets();
    renderAssets(data);
  }

  async function loadPerformers() {
    renderLoading(containers.performers, "Загружаем top performers…");
    const filters = {
      entityLevel: document.getElementById("performers-level").value,
      metric: document.getElementById("performers-metric").value,
      lookbackDays: Number(document.getElementById("performers-lookback").value || 7),
    };
    const data = await api.performers(filters);
    renderPerformers(data);
  }

  async function loadNoResultSpend() {
    renderLoading(containers.waste, "Загружаем сущности без результата…");
    const filters = {
      entityLevel: document.getElementById("waste-level").value,
      lookbackDays: Number(document.getElementById("waste-lookback").value || 7),
      minSpend: Number(document.getElementById("waste-min-spend").value || 20),
    };
    const data = await api.noResultSpend(filters);
    renderNoResultSpend(data);
  }

  async function loadDiagnostics() {
    renderLoading(containers.diagnosticsHealth, "Загружаем debug health…");
    renderLoading(containers.diagnosticsConfig, "Загружаем конфигурацию…");
    renderLoading(containers.diagnosticsAuth, "Проверяем авторизацию Meta…");
    renderLoading(containers.diagnosticsTroubleshooting, "Собираем troubleshooting…");

    const [configData, authData, healthData] = await Promise.all([
      api.configDiagnostics(),
      api.authDiagnostics(),
      api.debugHealth(),
    ]);
    renderDiagnostics(configData, authData, healthData);
  }

  async function refreshAll() {
    setStatus("loading", "Обновление данных…");

    const tasks = [
      {
        key: "overview",
        run: loadOverview,
        onError(message) {
          renderError(containers.overviewMetrics, message);
          renderError(containers.overviewAccount, message);
          renderError(containers.overviewStatuses, message);
        },
      },
      {
        key: "structure",
        run: loadStructure,
        onError(message) {
          renderError(containers.structure, message);
        },
      },
      {
        key: "issues",
        run: loadIssues,
        onError(message) {
          renderError(containers.issues, message);
        },
      },
      {
        key: "assets",
        run: loadAssets,
        onError(message) {
          renderError(containers.assets, message);
        },
      },
      {
        key: "performers",
        run: loadPerformers,
        onError(message) {
          renderError(containers.performers, message);
        },
      },
      {
        key: "no-result-spend",
        run: loadNoResultSpend,
        onError(message) {
          renderError(containers.waste, message);
        },
      },
      {
        key: "diagnostics",
        run: loadDiagnostics,
        onError(message) {
          renderError(containers.diagnosticsHealth, message);
          renderError(containers.diagnosticsConfig, message);
          renderError(containers.diagnosticsAuth, message);
          renderError(containers.diagnosticsTroubleshooting, message);
        },
      },
    ];

    const results = await Promise.allSettled(
      tasks.map(async (task) => {
        try {
          await task.run();
        } catch (error) {
          const message = normalizeErrorMessage(error);
          task.onError(message);
          throw new Error(`[${task.key}] ${message}`);
        }
      }),
    );
    const failed = results.filter((result) => result.status === "rejected");

    if (failed.length) {
      const reasons = Array.from(
        new Set(
          failed
            .map((result) => (result.status === "rejected" ? result.reason?.message || "Ошибка загрузки" : ""))
            .filter(Boolean),
        ),
      );
      const primaryReason = reasons[0] || "Ошибка загрузки";
      setStatus("error", `Есть ошибки загрузки: ${failed.length}. ${primaryReason}`);
      reasons.forEach((reason) => {
        showToast(reason, "error");
      });
    } else {
      setStatus("ok", "Данные актуальны");
      showToast("Данные успешно обновлены", "success");
    }

    stampRefreshTime();
  }

  function setActiveSection(sectionId) {
    state.activeSection = sectionId;

    document.querySelectorAll(".nav-button").forEach((button) => {
      const isActive = button.dataset.section === sectionId;
      button.classList.toggle("is-active", isActive);
    });

    document.querySelectorAll("[data-section-panel]").forEach((panel) => {
      const isActive = panel.id === sectionId;
      panel.classList.toggle("is-active", isActive);
      panel.hidden = !isActive;
    });
  }

  function bindSectionNavigation() {
    document.querySelectorAll(".nav-button").forEach((button) => {
      button.addEventListener("click", () => {
        setActiveSection(button.dataset.section);
      });
    });
  }

  function bindActionTabs() {
    document.querySelectorAll(".action-tab").forEach((tabButton) => {
      tabButton.addEventListener("click", () => {
        const target = tabButton.dataset.actionTab;

        document.querySelectorAll(".action-tab").forEach((item) => {
          const active = item === tabButton;
          item.classList.toggle("is-active", active);
          item.setAttribute("aria-selected", active ? "true" : "false");
        });

        document.querySelectorAll(".action-panel").forEach((panel) => {
          const active = panel.id === `panel-${target}`;
          panel.classList.toggle("is-active", active);
          panel.hidden = !active;
        });
      });
    });
  }

  function setSubmitLoading(form, loading) {
    const button = form.querySelector(".submit-button");
    if (!button) {
      return;
    }
    button.classList.toggle("is-loading", loading);
    button.disabled = loading;
  }

  function sanitizeOptionalNumber(value) {
    if (value === "" || value === null || value === undefined) {
      return null;
    }
    const numeric = Number(value);
    return Number.isFinite(numeric) ? numeric : null;
  }

  function bindPreviewForms() {
    const cloneForm = document.getElementById("form-clone");
    const budgetForm = document.getElementById("form-budget");
    const pauseForm = document.getElementById("form-pause");

    cloneForm.addEventListener("submit", async (event) => {
      event.preventDefault();
      setSubmitLoading(cloneForm, true);
      const formData = new FormData(cloneForm);
      try {
        const payload = {
          source_campaign_id: String(formData.get("source_campaign_id") || "").trim(),
          new_name: String(formData.get("new_name") || "").trim() || null,
          status: String(formData.get("status") || "PAUSED"),
          daily_budget: sanitizeOptionalNumber(formData.get("daily_budget")),
          lifetime_budget: sanitizeOptionalNumber(formData.get("lifetime_budget")),
          account_id: state.filters.accountId || null,
        };
        const preview = await api.previewCloneCampaign(payload);
        openPreviewDrawer(preview, "Preview: clone campaign");
        showToast("Preview клонирования готов", "success");
      } catch (error) {
        showToast(`Ошибка preview: ${error.message}`, "error");
      } finally {
        setSubmitLoading(cloneForm, false);
      }
    });

    budgetForm.addEventListener("submit", async (event) => {
      event.preventDefault();
      setSubmitLoading(budgetForm, true);
      const formData = new FormData(budgetForm);
      try {
        const payload = {
          campaign_id: String(formData.get("campaign_id") || "").trim(),
          daily_budget: sanitizeOptionalNumber(formData.get("daily_budget")),
          lifetime_budget: sanitizeOptionalNumber(formData.get("lifetime_budget")),
          spend_cap: sanitizeOptionalNumber(formData.get("spend_cap")),
          budget_delta_percent: sanitizeOptionalNumber(formData.get("budget_delta_percent")),
          account_id: state.filters.accountId || null,
        };
        const preview = await api.previewUpdateCampaignBudget(payload);
        openPreviewDrawer(preview, "Preview: update campaign budget");
        showToast("Preview изменения бюджета готов", "success");
      } catch (error) {
        showToast(`Ошибка preview: ${error.message}`, "error");
      } finally {
        setSubmitLoading(budgetForm, false);
      }
    });

    pauseForm.addEventListener("submit", async (event) => {
      event.preventDefault();
      setSubmitLoading(pauseForm, true);
      const formData = new FormData(pauseForm);
      try {
        const ids = String(formData.get("ids") || "")
          .split(/[\n,]+/)
          .map((item) => item.trim())
          .filter(Boolean);
        const payload = {
          ids,
          account_id: state.filters.accountId || null,
        };
        const preview = await api.previewPauseAds(payload);
        openPreviewDrawer(preview, "Preview: pause ads");
        showToast("Preview паузы объявлений готов", "success");
      } catch (error) {
        showToast(`Ошибка preview: ${error.message}`, "error");
      } finally {
        setSubmitLoading(pauseForm, false);
      }
    });
  }

  function bindTopBarActions() {
    document.getElementById("apply-filters").addEventListener("click", async () => {
      state.filters.accountId = dom.accountFilter.value.trim();
      state.filters.endDate = dom.dateFilter.value;
      await refreshAll();
    });

    document.getElementById("refresh-all").addEventListener("click", async () => {
      await refreshAll();
    });

    document.getElementById("performers-refresh").addEventListener("click", async () => {
      try {
        await loadPerformers();
        showToast("Раздел top performers обновлён", "info");
      } catch (error) {
        renderError(containers.performers, error.message);
        showToast(`Ошибка раздела: ${error.message}`, "error");
      }
    });

    document.getElementById("waste-refresh").addEventListener("click", async () => {
      try {
        await loadNoResultSpend();
        showToast("Раздел no-result spend обновлён", "info");
      } catch (error) {
        renderError(containers.waste, error.message);
        showToast(`Ошибка раздела: ${error.message}`, "error");
      }
    });

    document.getElementById("diagnostics-refresh").addEventListener("click", async () => {
      try {
        await loadDiagnostics();
        showToast("Диагностика обновлена", "info");
      } catch (error) {
        const message = normalizeErrorMessage(error);
        renderError(containers.diagnosticsHealth, message);
        renderError(containers.diagnosticsConfig, message);
        renderError(containers.diagnosticsAuth, message);
        renderError(containers.diagnosticsTroubleshooting, message);
        showToast(`Ошибка диагностики: ${message}`, "error");
      }
    });
  }

  function bindDrawerActions() {
    document.getElementById("drawer-close").addEventListener("click", closePreviewDrawer);
    dom.drawerBackdrop.addEventListener("click", closePreviewDrawer);

    document.getElementById("drawer-copy").addEventListener("click", async () => {
      try {
        await navigator.clipboard.writeText(dom.drawerJson.textContent || "");
        showToast("JSON скопирован", "success");
      } catch {
        showToast("Не удалось скопировать JSON", "error");
      }
    });
  }

  async function boot() {
    bindSectionNavigation();
    bindActionTabs();
    bindPreviewForms();
    bindTopBarActions();
    bindDrawerActions();

    setStatus("loading", "Загрузка данных…");

    try {
      await refreshAll();
      setActiveSection("overview");
    } catch (error) {
      setStatus("error", "Ошибка первичной загрузки");
      showToast(`Ошибка запуска UI: ${error.message}`, "error");
      Object.values(containers).forEach((container) => {
        renderError(container, error.message);
      });
    }
  }

  void boot();
})();

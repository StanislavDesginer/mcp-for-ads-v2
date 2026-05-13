const state = {
  accountId: "",
  accountName: "",
  lastRefreshed: null,
};

// ─── HTTP ───────────────────────────────────────────────────────────────────

async function requestJson(url, options = {}) {
  const response = await fetch(url, options);
  const payload = await response.json();
  if (!response.ok) {
    throw new Error(payload.error || "Ошибка запроса");
  }
  return payload;
}

// ─── Formatters ─────────────────────────────────────────────────────────────

function money(value) {
  return new Intl.NumberFormat("ru-RU", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 2,
  }).format(Number(value || 0));
}

function number(value) {
  return new Intl.NumberFormat("ru-RU").format(Number(value || 0));
}

function formatPercent(value) {
  return `${Number(value || 0).toFixed(2)}%`;
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

// ─── Toast notifications ─────────────────────────────────────────────────────

function showToast(message, type = "info", duration = 4000) {
  const root = document.getElementById("toast-root");
  const toast = document.createElement("div");
  toast.className = `toast toast-${type}`;
  toast.textContent = message;
  root.appendChild(toast);
  setTimeout(() => {
    toast.classList.add("is-leaving");
    toast.addEventListener("animationend", () => toast.remove(), { once: true });
  }, duration);
}

// ─── Skeleton loaders ────────────────────────────────────────────────────────

function skeletonLines(count = 3) {
  const widths = ["wide", "mid", "short", "wide", "mid"];
  return Array.from({ length: count }, (_, i) =>
    `<div class="skeleton-line ${widths[i % widths.length]}"></div>`
  ).join("");
}

function showSkeleton(containerId, lines = 3) {
  const el = document.getElementById(containerId);
  if (el) el.innerHTML = skeletonLines(lines);
}

function showMetricSkeleton() {
  document.getElementById("metrics").innerHTML = Array.from({ length: 4 }).map(() => `
    <article class="metric-card skeleton-metric">
      ${skeletonLines(3)}
    </article>
  `).join("");
}

function showCardError(containerId, message) {
  const el = document.getElementById(containerId);
  if (el) el.innerHTML = `<div class="card-error">${escapeHtml(message)}</div>`;
}

// ─── Preview drawer ───────────────────────────────────────────────────────────

function openPreviewDrawer(data, title = "Предварительный просмотр") {
  document.getElementById("drawer-title").textContent = title;

  // Risk flags
  const risks = data.risk_flags || data.risks || [];
  const risksEl = document.getElementById("preview-risks");
  risksEl.innerHTML = risks.map(r =>
    `<div class="risk-item">${escapeHtml(String(r))}</div>`
  ).join("");

  document.getElementById("preview-output").textContent = JSON.stringify(data, null, 2);
  document.getElementById("preview-drawer").classList.add("is-open");
  document.getElementById("preview-overlay").classList.add("is-open");
}

function closePreviewDrawer() {
  document.getElementById("preview-drawer").classList.remove("is-open");
  document.getElementById("preview-overlay").classList.remove("is-open");
}

function bindDrawer() {
  document.getElementById("drawer-close").addEventListener("click", closePreviewDrawer);
  document.getElementById("preview-overlay").addEventListener("click", closePreviewDrawer);

  document.getElementById("drawer-copy").addEventListener("click", (e) => {
    const text = document.getElementById("preview-output").textContent;
    navigator.clipboard.writeText(text).then(() => {
      const btn = e.currentTarget;
      btn.textContent = "Скопировано ✓";
      btn.classList.add("is-copied");
      setTimeout(() => {
        btn.textContent = "Копировать JSON";
        btn.classList.remove("is-copied");
      }, 2000);
    });
  });
}

// ─── Status indicator ────────────────────────────────────────────────────────

function setStatus(state_) {
  const dot = document.getElementById("status-dot");
  const label = document.getElementById("status-label");
  if (state_ === "ok") {
    dot.className = "status-dot";
    label.textContent = "Подключено";
  } else if (state_ === "error") {
    dot.className = "status-dot is-error";
    label.textContent = "Ошибка подключения";
  } else {
    dot.className = "status-dot is-loading";
    label.textContent = "Загрузка...";
  }
}

function updateRefreshTime() {
  const el = document.getElementById("refresh-time");
  if (!el) return;
  const now = new Date();
  const hh = String(now.getHours()).padStart(2, "0");
  const mm = String(now.getMinutes()).padStart(2, "0");
  el.textContent = `Обновлено в ${hh}:${mm}`;
}

// ─── Navigation ──────────────────────────────────────────────────────────────

function setActiveNav(action) {
  document.querySelectorAll(".nav-btn").forEach((btn) => {
    btn.classList.toggle("is-active", btn.getAttribute("data-load") === action);
  });
}

function bindTabs() {
  document.querySelectorAll(".tab-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      const target = btn.getAttribute("data-tab");
      document.querySelectorAll(".tab-btn").forEach(b => b.classList.remove("is-active"));
      document.querySelectorAll(".tab-panel").forEach(p => p.classList.remove("is-active"));
      btn.classList.add("is-active");
      document.querySelector(`[data-panel="${target}"]`).classList.add("is-active");
    });
  });
}

// ─── Render functions ────────────────────────────────────────────────────────

function renderMetrics(data) {
  const periods = data.spend?.periods || [];
  const today = periods.find(p => p.period === "today") || {};
  const week  = periods.find(p => p.period === "last_7_days") || {};
  const month = periods.find(p => p.period === "last_30_days") || {};
  const cards = [
    { label: "Расход сегодня",  value: money(today.spend), sub: "Текущий день по кабинету" },
    { label: "Расход за 7 дней", value: money(week.spend),  sub: "Короткое окно для контроля" },
    { label: "Расход за 30 дней", value: money(month.spend), sub: "Общий объём за месяц" },
    { label: "Открытые проблемы", value: number(data.issues?.issue_count), sub: "Что требует внимания" },
  ];
  document.getElementById("metrics").innerHTML = cards.map(c => `
    <article class="metric-card">
      <div class="metric-label">${escapeHtml(c.label)}</div>
      <div class="metric-value">${escapeHtml(c.value)}</div>
      <div class="metric-sub">${escapeHtml(c.sub)}</div>
    </article>
  `).join("");
}

function renderOverview(data) {
  const account = data.account || {};
  const totals  = data.totals  || {};
  const statuses = data.statuses || {};
  state.accountName = account.name || account.account_name || data.account_id || "Meta Ads";
  document.getElementById("account-badge").textContent =
    `${state.accountName} (${data.account_id})`;

  document.getElementById("account-overview").innerHTML = `
    <div class="stat-grid">
      <div class="mini-stat"><span>Кампании</span><strong>${number(totals.campaigns)}</strong></div>
      <div class="mini-stat"><span>Адсеты</span><strong>${number(totals.adsets)}</strong></div>
      <div class="mini-stat"><span>Объявления</span><strong>${number(totals.ads)}</strong></div>
    </div>
    <div class="summary-table">
      <div class="summary-row"><span>Название кабинета</span><strong>${escapeHtml(state.accountName)}</strong></div>
      <div class="summary-row"><span>Валюта</span><strong>${escapeHtml(account.currency || "—")}</strong></div>
      <div class="summary-row"><span>Часовой пояс</span><strong>${escapeHtml(account.timezone_name || "—")}</strong></div>
      <div class="summary-row"><span>ID кабинета</span><strong>${escapeHtml(data.account_id || "")}</strong></div>
    </div>
    <div class="status-grid">
      <div class="status-card"><span>Статусы кампаний</span><div class="status-row">${renderStatusChips(statuses.campaigns || {})}</div></div>
      <div class="status-card"><span>Статусы адсетов</span><div class="status-row">${renderStatusChips(statuses.adsets || {})}</div></div>
      <div class="status-card"><span>Статусы объявлений</span><div class="status-row">${renderStatusChips(statuses.ads || {})}</div></div>
    </div>
  `;
}

function renderStatusChips(statusMap) {
  const entries = Object.entries(statusMap);
  if (!entries.length) return '<span class="status-chip">Нет данных</span>';
  return entries.map(([key, val]) => `
    <span class="status-chip ${key === "DISAPPROVED" || key === "WITH_ISSUES" ? "chip-warn" : ""}">
      ${escapeHtml(key)}: ${number(val)}
    </span>
  `).join("");
}

function renderIssues(data) {
  const issues = data.issues || data.rows || [];
  document.getElementById("issues-list").innerHTML = issues.length ? `
    <div class="list">
      ${issues.map(issue => `
        <div class="list-item">
          <div class="issue-title">
            <span>${escapeHtml(issue.name || issue.ad_name || issue.id || "Проблема")}</span>
            <span class="status-chip chip-warn">${escapeHtml(issue.effective_status || issue.status || "UNKNOWN")}</span>
          </div>
          <div class="issue-text">${escapeHtml(issue.issue_summary || issue.review_feedback || "Meta сообщает о проблеме с доставкой или статусом.")}</div>
        </div>
      `).join("")}
    </div>
  ` : '<div class="list-item">Явных проблем доставки сейчас не найдено.</div>';
}

function renderAssets(data) {
  const summary = data.summary || {};
  const labels = {
    pages: "Страницы",
    instagram_accounts: "Instagram-аккаунты",
    pixels: "Пиксели",
    custom_conversions: "Кастомные конверсии",
    lead_forms: "Лид-формы",
  };
  const rows = Object.entries(summary).map(([key, val]) => `
    <div class="summary-row">
      <span>${escapeHtml(labels[key] || key)}</span>
      <strong>${number(val)}</strong>
    </div>
  `).join("");
  document.getElementById("assets-list").innerHTML = rows
    ? `<div class="summary-table">${rows}</div>`
    : '<div class="list-item">Данные по активам пока не вернулись.</div>';
}

function renderStructure(data) {
  const rows = data.rows || [];
  document.getElementById("campaign-structure").innerHTML = rows.length ? `
    <div class="tree">
      ${rows.map(campaign => `
        <div class="tree-item">
          <div class="entity-title">
            <span>${escapeHtml(campaign.campaign_name || campaign.campaign_id)}</span>
            <span class="status-chip">${escapeHtml(campaign.campaign_status || "UNKNOWN")}</span>
          </div>
          <div class="tree-meta">ID: ${escapeHtml(campaign.campaign_id || "")}</div>
          <div class="tree-stack">
            ${(campaign.adsets || []).slice(0, 5).map(adset => `
              <div class="sub-tree">
                <strong>${escapeHtml(adset.adset_name || adset.adset_id)}</strong>
                <div class="tree-meta">Статус: ${escapeHtml(adset.adset_status || "UNKNOWN")}</div>
                <ul>
                  ${(adset.ads || []).slice(0, 4).map(ad =>
                    `<li>${escapeHtml(ad.ad_name || ad.ad_id)} (${escapeHtml(ad.ad_status || "UNKNOWN")})</li>`
                  ).join("") || "<li>Объявлений не найдено</li>"}
                </ul>
              </div>
            `).join("") || '<div class="sub-tree">Адсеты не найдены.</div>'}
          </div>
        </div>
      `).join("")}
    </div>
  ` : '<div class="list-item">Структура кампаний пока не загружена.</div>';
}

function renderRankList(targetId, rows, kind) {
  document.getElementById(targetId).innerHTML = rows.length ? `
    <div class="list">
      ${rows.map(row => `
        <div class="list-item">
          <div class="entity-title">
            <span>${escapeHtml(row.entity_name || row.campaign_name || row.ad_name || row.entity_id || "Сущность")}</span>
            <span class="status-chip ${kind === "waste" ? "chip-warn" : ""}">${kind === "winners" ? "Эффективно" : "Риск"}</span>
          </div>
          <div class="meta-text">Расход: ${money(row.spend)} · CTR: ${formatPercent(row.ctr)}</div>
          <div class="meta-text">
            ${kind === "winners"
              ? `Конверсии: ${number(row.conversions)} · Цена за результат: ${money(row.cost_per_result)}`
              : `Конверсии: ${number(row.conversions)} · Требует проверки или паузы`}
          </div>
        </div>
      `).join("")}
    </div>
  ` : '<div class="list-item">Подходящих сущностей не найдено.</div>';
}

// ─── Data loaders ─────────────────────────────────────────────────────────────

async function loadDashboard() {
  setActiveNav("dashboard");
  showMetricSkeleton();
  showSkeleton("account-overview", 5);
  showSkeleton("issues-list", 3);
  try {
    const data = await requestJson("/api/meta/dashboard");
    state.accountId = data.account_id || "";
    renderMetrics(data);
    renderOverview(data);
    renderIssues(data.issues || {});
    setStatus("ok");
    updateRefreshTime();
  } catch (err) {
    showCardError("account-overview", err.message);
    showToast(`Ошибка загрузки сводки: ${err.message}`, "error");
    setStatus("error");
  }
}

async function loadStructure() {
  setActiveNav("structure");
  showSkeleton("campaign-structure", 6);
  try {
    renderStructure(await requestJson("/api/meta/campaign-structure"));
  } catch (err) {
    showCardError("campaign-structure", err.message);
    showToast(`Ошибка структуры: ${err.message}`, "error");
  }
}

async function loadIssues() {
  setActiveNav("issues");
  showSkeleton("issues-list", 4);
  try {
    renderIssues(await requestJson("/api/meta/delivery-issues"));
  } catch (err) {
    showCardError("issues-list", err.message);
    showToast(`Ошибка загрузки проблем: ${err.message}`, "error");
  }
}

async function loadAssets() {
  setActiveNav("assets");
  showSkeleton("assets-list", 4);
  try {
    renderAssets(await requestJson("/api/meta/assets"));
  } catch (err) {
    showCardError("assets-list", err.message);
    showToast(`Ошибка загрузки активов: ${err.message}`, "error");
  }
}

async function loadWinners() {
  setActiveNav("winners");
  showSkeleton("winners-list", 4);
  try {
    const data = await requestJson("/api/meta/top-performers");
    renderRankList("winners-list", data.rows || [], "winners");
  } catch (err) {
    showCardError("winners-list", err.message);
    showToast(`Ошибка топ-кампаний: ${err.message}`, "error");
  }
}

async function loadWaste() {
  setActiveNav("waste");
  showSkeleton("waste-list", 4);
  try {
    const data = await requestJson("/api/meta/no-result-entities");
    renderRankList("waste-list", data.rows || [], "waste");
  } catch (err) {
    showCardError("waste-list", err.message);
    showToast(`Ошибка слива: ${err.message}`, "error");
  }
}

// ─── Form actions ─────────────────────────────────────────────────────────────

async function submitAction(url, payload, drawerTitle) {
  try {
    const data = await requestJson(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    openPreviewDrawer(data, drawerTitle);
    showToast("Preview готов — проверьте перед применением", "success");
  } catch (err) {
    showToast(`Ошибка: ${err.message}`, "error");
  }
}

function setFormLoading(btn, isLoading) {
  btn.classList.toggle("is-loading", isLoading);
  btn.disabled = isLoading;
}

function bindActions() {
  // Nav buttons
  document.querySelectorAll("[data-load]").forEach((btn) => {
    btn.addEventListener("click", async () => {
      const action = btn.getAttribute("data-load");
      if (action === "dashboard") await loadDashboard();
      if (action === "structure") await loadStructure();
      if (action === "issues")   await loadIssues();
      if (action === "assets")   await loadAssets();
      if (action === "winners")  await loadWinners();
      if (action === "waste")    await loadWaste();
    });
  });

  // Refresh all
  document.getElementById("refresh-all").addEventListener("click", async () => {
    showToast("Обновление данных...", "info", 2000);
    await Promise.allSettled([
      loadDashboard(), loadStructure(), loadAssets(), loadWinners(), loadWaste(),
    ]);
    showToast("Все данные обновлены", "success");
  });

  // Clone form
  document.getElementById("clone-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const btn = e.currentTarget.querySelector(".form-submit-btn");
    const form = new FormData(e.currentTarget);
    setFormLoading(btn, true);
    await submitAction("/api/meta/preview/clone-campaign", {
      source_campaign_id: form.get("source_campaign_id"),
      new_name: form.get("new_name") || null,
      daily_budget: form.get("daily_budget") ? Number(form.get("daily_budget")) : null,
    }, "Preview: клонирование кампании");
    setFormLoading(btn, false);
  });

  // Budget form
  document.getElementById("budget-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const btn = e.currentTarget.querySelector(".form-submit-btn");
    const form = new FormData(e.currentTarget);
    setFormLoading(btn, true);
    await submitAction("/api/meta/preview/update-campaign-budget", {
      campaign_id: form.get("campaign_id"),
      daily_budget: form.get("daily_budget") ? Number(form.get("daily_budget")) : null,
      budget_delta_percent: form.get("budget_delta_percent") ? Number(form.get("budget_delta_percent")) : null,
    }, "Preview: изменение бюджета");
    setFormLoading(btn, false);
  });

  // Pause form
  document.getElementById("pause-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const btn = e.currentTarget.querySelector(".form-submit-btn");
    const form = new FormData(e.currentTarget);
    const ids = String(form.get("ids") || "")
      .split(",").map(s => s.trim()).filter(Boolean);
    setFormLoading(btn, true);
    await submitAction("/api/meta/preview/pause-ads", { ids }, "Preview: постановка на паузу");
    setFormLoading(btn, false);
  });
}

// ─── Boot ─────────────────────────────────────────────────────────────────────

async function boot() {
  setStatus("loading");
  bindTabs();
  bindActions();
  bindDrawer();
  // Load all sections in parallel; each handles its own errors
  await Promise.allSettled([
    loadDashboard(),
    loadStructure(),
    loadAssets(),
    loadWinners(),
    loadWaste(),
  ]);
}

boot();

"""Build a standalone HTML dashboard from the processed expense CSV files."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd


def read_json_records(path: Path) -> list[dict]:
    if not path.exists():
        return []
    df = pd.read_csv(path)
    return json.loads(df.fillna("").to_json(orient="records"))


def js_json(data: object) -> str:
    return json.dumps(data, ensure_ascii=True).replace("</", "<\\/")


def build_dashboard(processed_dir: Path, output_path: Path) -> None:
    transactions = read_json_records(processed_dir / "transactions_clean.csv")
    monthly = read_json_records(processed_dir / "monthly_summary.csv")
    recurring = read_json_records(processed_dir / "recurring_payments.csv")

    html = DASHBOARD_TEMPLATE.replace("__TRANSACTIONS__", js_json(transactions))
    html = html.replace("__MONTHLY__", js_json(monthly))
    html = html.replace("__RECURRING__", js_json(recurring))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html, encoding="utf-8")


DASHBOARD_TEMPLATE = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Personal Expense Analytics Dashboard</title>
  <script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>
  <style>
    :root {
      --bg: #07111f;
      --surface: rgba(15, 23, 42, 0.62);
      --surface-strong: rgba(15, 23, 42, 0.78);
      --text: #e5edf6;
      --muted: #9aa7b6;
      --border: rgba(148, 163, 184, 0.22);
      --soft-border: rgba(148, 163, 184, 0.16);
      --teal: #2dd4bf;
      --green: #22c55e;
      --red: #fb7185;
      --amber: #f59e0b;
      --blue: #60a5fa;
      --navy: #f8fafc;
      --glass-shadow: 0 24px 60px rgba(0, 0, 0, 0.38);
      --glass-shadow-soft: 0 12px 32px rgba(0, 0, 0, 0.30);
      color-scheme: dark;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      min-height: 100vh;
      background:
        radial-gradient(circle at 14% 8%, rgba(45, 212, 191, 0.18), transparent 30%),
        radial-gradient(circle at 84% 4%, rgba(96, 165, 250, 0.16), transparent 32%),
        radial-gradient(circle at 50% 100%, rgba(245, 158, 11, 0.10), transparent 34%),
        linear-gradient(180deg, var(--bg) 0%, #0b1728 52%, #111827 100%);
      color: var(--text);
    }
    body::before {
      content: "";
      position: fixed;
      inset: 0;
      pointer-events: none;
      background-image:
        linear-gradient(rgba(148, 163, 184, 0.08) 1px, transparent 1px),
        linear-gradient(90deg, rgba(148, 163, 184, 0.07) 1px, transparent 1px);
      background-size: 48px 48px;
      mask-image: linear-gradient(to bottom, rgba(0, 0, 0, 0.42), transparent 70%);
    }
    header {
      background: rgba(7, 17, 31, 0.74);
      border-bottom: 1px solid rgba(148, 163, 184, 0.16);
      backdrop-filter: blur(22px) saturate(165%);
      -webkit-backdrop-filter: blur(22px) saturate(165%);
      position: sticky;
      top: 0;
      z-index: 2;
      box-shadow: 0 14px 42px rgba(0, 0, 0, 0.28);
    }
    .header-inner {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 18px;
      width: min(1480px, 100%);
      margin: 0 auto;
      padding: 20px 28px;
    }
    h1 {
      font-size: 22px;
      line-height: 1.2;
      margin: 0;
      letter-spacing: 0;
      color: var(--navy);
    }
    .eyebrow {
      color: var(--teal);
      font-size: 12px;
      font-weight: 760;
      margin-bottom: 5px;
      text-transform: uppercase;
      letter-spacing: 0;
    }
    .subtitle {
      color: var(--muted);
      margin-top: 4px;
      font-size: 13px;
    }
    .title-row {
      display: flex;
      align-items: center;
      gap: 10px;
      flex-wrap: wrap;
    }
    .period-pill {
      display: inline-flex;
      align-items: center;
      min-height: 24px;
      padding: 0 9px;
      border-radius: 999px;
      border: 1px solid rgba(45, 212, 191, 0.28);
      color: var(--teal);
      background: rgba(45, 212, 191, 0.10);
      font-size: 12px;
      font-weight: 700;
      backdrop-filter: blur(12px);
      -webkit-backdrop-filter: blur(12px);
    }
    .filters {
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      justify-content: flex-end;
    }
    select, input {
      height: 40px;
      border: 1px solid rgba(148, 163, 184, 0.25);
      background: rgba(15, 23, 42, 0.62);
      color: var(--text);
      border-radius: 6px;
      padding: 0 10px;
      font-size: 13px;
      min-width: 150px;
      box-shadow: 0 8px 22px rgba(0, 0, 0, 0.22);
      backdrop-filter: blur(16px) saturate(150%);
      -webkit-backdrop-filter: blur(16px) saturate(150%);
      outline: none;
    }
    select:focus, input:focus {
      border-color: var(--teal);
      box-shadow: 0 0 0 3px rgba(45, 212, 191, 0.14);
    }
    select option {
      background: #0f172a;
      color: var(--text);
    }
    input::placeholder {
      color: rgba(154, 167, 182, 0.72);
    }
    main {
      width: min(1480px, 100%);
      margin: 0 auto;
      padding: 22px 28px 34px;
      display: grid;
      gap: 18px;
    }
    .kpis {
      display: grid;
      grid-template-columns: repeat(6, minmax(0, 1fr));
      gap: 14px;
    }
    .kpi, .panel {
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 8px;
      box-shadow: var(--glass-shadow);
      backdrop-filter: blur(22px) saturate(155%);
      -webkit-backdrop-filter: blur(22px) saturate(155%);
    }
    .kpi {
      padding: 17px 18px;
      min-height: 116px;
      position: relative;
      overflow: hidden;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
    }
    .kpi::before {
      content: "";
      position: absolute;
      inset: 0 auto 0 0;
      width: 4px;
      background: var(--blue);
    }
    .kpi::after {
      content: "";
      position: absolute;
      inset: 0;
      pointer-events: none;
      background: linear-gradient(135deg, rgba(255, 255, 255, 0.10), rgba(255, 255, 255, 0) 44%);
    }
    .kpi-income::before { background: var(--green); }
    .kpi-expense::before { background: var(--red); }
    .kpi-savings::before { background: var(--teal); }
    .kpi-rate::before { background: var(--amber); }
    .kpi-average::before { background: var(--blue); }
    .kpi-savings {
      grid-column: span 2;
      background:
        linear-gradient(135deg, rgba(45, 212, 191, 0.16), rgba(15, 23, 42, 0.62)),
        var(--surface);
    }
    .kpi-negative::before { background: var(--red); }
    .kpi-negative {
      background:
        linear-gradient(135deg, rgba(251, 113, 133, 0.13), rgba(15, 23, 42, 0.62)),
        var(--surface);
    }
    .kpi-label {
      color: var(--muted);
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: 0;
      margin-bottom: 8px;
      position: relative;
      z-index: 1;
    }
    .kpi-value {
      font-weight: 720;
      font-size: 23px;
      line-height: 1.1;
      overflow-wrap: anywhere;
      color: var(--navy);
      position: relative;
      z-index: 1;
    }
    .kpi-savings .kpi-value {
      font-size: 32px;
    }
    .kpi-note {
      margin-top: 7px;
      color: var(--muted);
      font-size: 12px;
      position: relative;
      z-index: 1;
    }
    .grid-2 {
      display: grid;
      grid-template-columns: minmax(0, 1.35fr) minmax(420px, 1fr);
      gap: 18px;
    }
    .grid-3 {
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 18px;
    }
    .panel {
      padding: 16px;
      min-height: 360px;
    }
    .panel h2 {
      margin: 0;
      font-size: 15px;
      line-height: 1.3;
      letter-spacing: 0;
      color: var(--navy);
    }
    .panel-header {
      display: flex;
      align-items: flex-start;
      justify-content: space-between;
      gap: 12px;
      margin-bottom: 12px;
    }
    .panel-subtitle {
      color: var(--muted);
      font-size: 12px;
      margin-top: 4px;
      line-height: 1.35;
    }
    .panel-badge {
      flex: 0 0 auto;
      border-radius: 999px;
      border: 1px solid var(--soft-border);
      color: var(--muted);
      background: rgba(15, 23, 42, 0.52);
      padding: 5px 9px;
      font-size: 12px;
      font-weight: 650;
    }
    .chart {
      height: 300px;
      width: 100%;
    }
    .category-panel {
      min-height: 420px;
    }
    .category-layout {
      display: grid;
      grid-template-columns: minmax(210px, 0.92fr) minmax(190px, 1fr);
      gap: 12px;
      align-items: center;
      min-height: 328px;
    }
    .donut-chart {
      height: 320px;
      min-width: 0;
    }
    .category-legend {
      display: grid;
      gap: 8px;
      align-content: center;
      min-width: 0;
    }
    .category-row {
      display: grid;
      grid-template-columns: 12px minmax(0, 1fr) auto;
      align-items: center;
      gap: 8px;
      min-height: 32px;
      padding: 7px 8px;
      border: 1px solid var(--soft-border);
      border-radius: 7px;
      background: rgba(15, 23, 42, 0.52);
      backdrop-filter: blur(14px);
      -webkit-backdrop-filter: blur(14px);
    }
    .category-swatch {
      width: 10px;
      height: 10px;
      border-radius: 50%;
    }
    .category-name {
      font-size: 12px;
      font-weight: 700;
      color: var(--navy);
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }
    .category-meta {
      color: var(--muted);
      font-size: 11px;
      margin-top: 2px;
    }
    .category-value {
      text-align: right;
      font-size: 12px;
      font-weight: 760;
      color: var(--navy);
      white-space: nowrap;
    }
    .story-grid {
      display: grid;
      gap: 10px;
    }
    .story-card {
      border: 1px solid var(--soft-border);
      border-radius: 8px;
      padding: 11px 12px;
      background: rgba(15, 23, 42, 0.50);
      box-shadow: var(--glass-shadow-soft);
    }
    .story-title {
      font-size: 12px;
      color: var(--muted);
      margin-bottom: 5px;
    }
    .story-text {
      font-size: 13px;
      line-height: 1.45;
      color: var(--text);
    }
    .story-good { border-left: 4px solid var(--green); }
    .story-risk { border-left: 4px solid var(--red); }
    .story-watch { border-left: 4px solid var(--amber); }
    .story-info { border-left: 4px solid var(--blue); }
    .table-panel {
      min-height: 0;
    }
    table {
      width: 100%;
      border-collapse: collapse;
      font-size: 12px;
    }
    th, td {
      text-align: left;
      padding: 9px 8px;
      border-bottom: 1px solid rgba(148, 163, 184, 0.12);
      vertical-align: top;
    }
    th {
      color: var(--muted);
      font-weight: 650;
      background: rgba(15, 23, 42, 0.88);
      position: sticky;
      top: 0;
      backdrop-filter: blur(16px);
      -webkit-backdrop-filter: blur(16px);
    }
    tbody tr:hover {
      background: rgba(148, 163, 184, 0.08);
    }
    .table-wrap {
      max-height: 430px;
      overflow: auto;
      border: 1px solid var(--border);
      border-radius: 8px;
      background: rgba(15, 23, 42, 0.38);
    }
    .amount-credit { color: var(--green); font-weight: 650; }
    .amount-debit { color: var(--red); font-weight: 650; }
    @media (max-width: 1180px) {
      .kpis { grid-template-columns: repeat(2, minmax(0, 1fr)); }
      .kpi-savings { grid-column: span 2; }
      .grid-2, .grid-3 { grid-template-columns: 1fr; }
      .header-inner { align-items: flex-start; flex-direction: column; }
      .filters { justify-content: flex-start; width: 100%; }
      .category-layout { grid-template-columns: 1fr; }
      .category-legend { grid-template-columns: repeat(2, minmax(0, 1fr)); }
    }
    @media (max-width: 640px) {
      .header-inner, main { padding-left: 16px; padding-right: 16px; }
      .kpis { grid-template-columns: 1fr; }
      .kpi-savings { grid-column: span 1; }
      .kpi-savings .kpi-value { font-size: 28px; }
      select, input { width: 100%; min-width: 0; }
      .filters { flex-direction: column; }
      .panel { padding: 12px; }
      .category-legend { grid-template-columns: 1fr; }
      .category-name { white-space: normal; }
    }
  </style>
</head>
<body>
  <header>
    <div class="header-inner">
      <div>
        <div class="eyebrow">Finance analytics portfolio</div>
        <div class="title-row">
          <h1>Personal Expense Analytics</h1>
          <span class="period-pill">FY 2025-26</span>
        </div>
        <div class="subtitle">ICICI savings account transactions, Apr 2025 to Mar 2026</div>
      </div>
      <div class="filters">
        <select id="monthFilter"></select>
        <select id="categoryFilter"></select>
        <input id="searchFilter" type="search" placeholder="Search transactions">
      </div>
    </div>
  </header>

  <main>
    <section class="kpis">
      <div id="savingsCard" class="kpi kpi-savings"><div class="kpi-label">Net Savings</div><div id="savingsKpi" class="kpi-value"></div><div class="kpi-note">Income minus expenses</div></div>
      <div class="kpi kpi-income"><div class="kpi-label">Total Income</div><div id="incomeKpi" class="kpi-value"></div><div class="kpi-note">Credits</div></div>
      <div class="kpi kpi-expense"><div class="kpi-label">Total Expenses</div><div id="expenseKpi" class="kpi-value"></div><div class="kpi-note">Debits</div></div>
      <div class="kpi kpi-rate"><div class="kpi-label">Savings Rate</div><div id="rateKpi" class="kpi-value"></div><div class="kpi-note">Net savings / income</div></div>
      <div class="kpi kpi-average"><div class="kpi-label">Avg Monthly Expense</div><div id="avgKpi" class="kpi-value"></div><div class="kpi-note">Filtered months</div></div>
    </section>

    <section class="grid-2">
      <div class="panel">
        <div class="panel-header">
          <div>
            <h2>Monthly Income vs Expenses</h2>
            <div class="panel-subtitle">Compare cash inflow, outflow, and seasonality across the year.</div>
          </div>
          <span class="panel-badge">Monthly</span>
        </div>
        <div id="monthlyChart" class="chart"></div>
      </div>
      <div class="panel category-panel">
        <div class="panel-header">
          <div>
            <h2>Category-wise Spending</h2>
            <div class="panel-subtitle">All categories are shown in the legend so labels never get clipped.</div>
          </div>
          <span class="panel-badge">Expenses</span>
        </div>
        <div class="category-layout">
          <div id="categoryChart" class="chart donut-chart"></div>
          <div id="categoryLegend" class="category-legend"></div>
        </div>
      </div>
    </section>

    <section class="grid-3">
      <div class="panel">
        <div class="panel-header">
          <div>
            <h2>Data Story</h2>
            <div class="panel-subtitle">Plain-English interpretation of the current filter.</div>
          </div>
        </div>
        <div id="storyCards" class="story-grid"></div>
      </div>
      <div class="panel">
        <div class="panel-header">
          <div>
            <h2>Spending Trend</h2>
            <div class="panel-subtitle">Daily debit movement after filters are applied.</div>
          </div>
        </div>
        <div id="trendChart" class="chart"></div>
      </div>
      <div class="panel">
        <div class="panel-header">
          <div>
            <h2>Cash Withdrawal Trend</h2>
            <div class="panel-subtitle">Offline cash usage by month.</div>
          </div>
        </div>
        <div id="cashChart" class="chart"></div>
      </div>
    </section>

    <section class="grid-2">
      <div class="panel table-panel">
        <div class="panel-header">
          <div>
            <h2>Recurring Payments</h2>
            <div class="panel-subtitle">Repeated merchants and fixed-cost behavior.</div>
          </div>
        </div>
        <div class="table-wrap"><table id="recurringTable"></table></div>
      </div>
      <div class="panel table-panel">
        <div class="panel-header">
          <div>
            <h2>Transaction Explorer</h2>
            <div class="panel-subtitle">Latest 250 transactions matching the selected filters.</div>
          </div>
        </div>
        <div class="table-wrap"><table id="transactionTable"></table></div>
      </div>
    </section>
  </main>

  <script>
    const transactions = __TRANSACTIONS__;
    const monthlySummary = __MONTHLY__;
    const recurringPayments = __RECURRING__;

    const monthFilter = document.getElementById("monthFilter");
    const categoryFilter = document.getElementById("categoryFilter");
    const searchFilter = document.getElementById("searchFilter");

    const palette = ["#2dd4bf", "#60a5fa", "#f59e0b", "#fb7185", "#22c55e", "#a78bfa", "#06b6d4", "#94a3b8", "#f97316", "#ec4899", "#84cc16", "#38bdf8"];
    const plotConfig = { displayModeBar: false, responsive: true };
    const layoutBase = {
      margin: { l: 44, r: 18, t: 12, b: 48 },
      paper_bgcolor: "rgba(0,0,0,0)",
      plot_bgcolor: "rgba(0,0,0,0)",
      font: { family: "Inter, sans-serif", size: 12, color: "#e5edf6" },
      xaxis: { gridcolor: "rgba(148, 163, 184, 0.18)", zeroline: false, tickfont: { color: "#9aa7b6" } },
      yaxis: { gridcolor: "rgba(148, 163, 184, 0.18)", zeroline: false, tickfont: { color: "#9aa7b6" } },
      legend: { orientation: "h", y: -0.18, font: { color: "#9aa7b6" } },
      hoverlabel: { bgcolor: "#111827", bordercolor: "rgba(148, 163, 184, 0.35)", font: { color: "#f8fafc" } }
    };

    function formatInr(value) {
      const amount = Number(value || 0);
      const sign = amount < 0 ? "-" : "";
      return sign + "INR " + Math.abs(amount).toLocaleString("en-IN", { maximumFractionDigits: 0 });
    }
    function formatShortInr(value) {
      const amount = Number(value || 0);
      if (Math.abs(amount) >= 100000) return "INR " + (amount / 100000).toFixed(1) + "L";
      if (Math.abs(amount) >= 1000) return "INR " + (amount / 1000).toFixed(1) + "K";
      return formatInr(amount);
    }
    function formatPct(value) {
      if (!Number.isFinite(value)) return "0.0%";
      return (value * 100).toFixed(1) + "%";
    }
    function escapeHtml(value) {
      return String(value)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
    }
    function sum(rows, field) {
      return rows.reduce((total, row) => total + Number(row[field] || 0), 0);
    }
    function groupSum(rows, keyField, valueField) {
      const grouped = new Map();
      rows.forEach(row => grouped.set(row[keyField], (grouped.get(row[keyField]) || 0) + Number(row[valueField] || 0)));
      return Array.from(grouped, ([key, value]) => ({ key, value })).sort((a, b) => b.value - a.value);
    }
    function monthStats(rows) {
      return sortedMonthLabels(rows).map(label => {
        const monthRows = rows.filter(row => row.month_year === label);
        const income = sum(monthRows, "deposit_amount");
        const expenses = sum(monthRows, "withdrawal_amount");
        return { month: label, income, expenses, net: income - expenses };
      });
    }
    function storyCard(title, text, type = "info") {
      return `<div class="story-card story-${type}"><div class="story-title">${title}</div><div class="story-text">${text}</div></div>`;
    }
    function currentRows() {
      const month = monthFilter.value;
      const category = categoryFilter.value;
      const q = searchFilter.value.trim().toLowerCase();
      return transactions.filter(row => {
        const monthMatch = month === "All" || row.month_year === month;
        const categoryMatch = category === "All" || row.category === category;
        const haystack = `${row.description} ${row.merchant} ${row.category} ${row.mode}`.toLowerCase();
        const searchMatch = !q || haystack.includes(q);
        return monthMatch && categoryMatch && searchMatch;
      });
    }
    function sortedMonthLabels(rows) {
      return Array.from(new Set(rows.map(row => row.month_year))).sort((a, b) => {
        const da = new Date(rows.find(row => row.month_year === a).month_start);
        const db = new Date(rows.find(row => row.month_year === b).month_start);
        return da - db;
      });
    }
    function initFilters() {
      const months = monthlySummary.map(row => row.month_year);
      monthFilter.innerHTML = `<option value="All">All Months</option>` + months.map(month => `<option value="${month}">${month}</option>`).join("");
      const categories = Array.from(new Set(transactions.map(row => row.category))).sort();
      categoryFilter.innerHTML = `<option value="All">All Categories</option>` + categories.map(category => `<option value="${category}">${category}</option>`).join("");
    }
    function renderKpis(rows) {
      const income = sum(rows, "deposit_amount");
      const expenses = sum(rows, "withdrawal_amount");
      const net = income - expenses;
      const months = Math.max(1, new Set(rows.map(row => row.month_year)).size);
      document.getElementById("incomeKpi").textContent = formatInr(income);
      document.getElementById("expenseKpi").textContent = formatInr(expenses);
      document.getElementById("savingsKpi").textContent = formatInr(net);
      document.getElementById("rateKpi").textContent = formatPct(income > 0 ? net / income : 0);
      document.getElementById("avgKpi").textContent = formatInr(expenses / months);
      document.getElementById("savingsCard").classList.toggle("kpi-negative", net < 0);
    }
    function renderMonthly(rows) {
      const labels = sortedMonthLabels(rows);
      const income = labels.map(label => sum(rows.filter(row => row.month_year === label), "deposit_amount"));
      const expense = labels.map(label => sum(rows.filter(row => row.month_year === label), "withdrawal_amount"));
      Plotly.react("monthlyChart", [
        { type: "bar", name: "Income", x: labels, y: income, marker: { color: "#22c55e" } },
        { type: "bar", name: "Expenses", x: labels, y: expense, marker: { color: "#fb7185" } }
      ], { ...layoutBase, barmode: "group" }, plotConfig);
    }
    function renderCategory(rows) {
      const expenseRows = rows.filter(row => Number(row.withdrawal_amount) > 0);
      const grouped = groupSum(expenseRows, "category", "withdrawal_amount");
      const total = grouped.reduce((value, row) => value + row.value, 0);
      const colors = grouped.map((_row, index) => palette[index % palette.length]);
      Plotly.react("categoryChart", [{
        type: "pie",
        labels: grouped.map(row => row.key),
        values: grouped.map(row => row.value),
        customdata: grouped.map(row => formatInr(row.value)),
        marker: { colors, line: { color: "rgba(7, 17, 31, 0.92)", width: 3 } },
        hole: 0.62,
        sort: false,
        direction: "clockwise",
        rotation: -30,
        textinfo: "percent",
        textposition: "inside",
        insidetextorientation: "radial",
        textfont: { color: "#ffffff", size: 12 },
        hovertemplate: "<b>%{label}</b><br>%{customdata}<br>%{percent}<extra></extra>"
      }], {
        ...layoutBase,
        margin: { l: 6, r: 6, t: 4, b: 4 },
        showlegend: false,
        annotations: [{
          text: `<b>${formatShortInr(total)}</b><br><span style="font-size:11px;color:#9aa7b6">Total Spend</span>`,
          showarrow: false,
          x: 0.5,
          y: 0.5,
          font: { size: 15, color: "#f8fafc" },
          align: "center"
        }]
      }, plotConfig);

      const legend = grouped.map((row, index) => {
        const percent = total > 0 ? row.value / total : 0;
        return `
          <div class="category-row" title="${escapeHtml(row.key)}: ${formatInr(row.value)}">
            <span class="category-swatch" style="background:${colors[index]}"></span>
            <div>
              <div class="category-name">${escapeHtml(row.key)}</div>
              <div class="category-meta">${formatPct(percent)} of expenses</div>
            </div>
            <div class="category-value">${formatShortInr(row.value)}</div>
          </div>`;
      }).join("");
      document.getElementById("categoryLegend").innerHTML = legend || '<div class="category-row"><div class="category-name">No expense data</div></div>';
    }
    function renderStory(rows) {
      const expenseRows = rows.filter(row => Number(row.withdrawal_amount) > 0);
      const income = sum(rows, "deposit_amount");
      const expenses = sum(rows, "withdrawal_amount");
      const net = income - expenses;
      const rate = income > 0 ? net / income : 0;
      const categories = groupSum(expenseRows, "category", "withdrawal_amount");
      const topCategory = categories[0] || { key: "No category", value: 0 };
      const nonTransfer = categories.filter(row => !["Transfers", "Investments/FD"].includes(row.key));
      const topLifestyle = nonTransfer[0] || topCategory;
      const cash = sum(expenseRows.filter(row => row.category === "Cash Withdrawal"), "withdrawal_amount");
      const cashShare = expenses > 0 ? cash / expenses : 0;
      const recurringRows = expenseRows.filter(row => Number(row.is_recurring) === 1);
      const recurringTotal = sum(recurringRows, "withdrawal_amount");
      const recurringMerchants = new Set(recurringRows.map(row => row.merchant)).size;
      const months = monthStats(rows);
      const worst = months.slice().sort((a, b) => a.net - b.net)[0];
      const best = months.slice().sort((a, b) => b.net - a.net)[0];

      const cards = [
        storyCard(
          net >= 0 ? "Savings Cushion" : "Savings Pressure",
          net >= 0
            ? `Income is ahead of expenses by ${formatInr(net)}, giving a ${formatPct(rate)} savings rate.`
            : `Expenses are higher than income by ${formatInr(Math.abs(net))}, creating a ${formatPct(rate)} savings rate.`,
          net >= 0 ? "good" : "risk"
        ),
        storyCard(
          "Main Spend Driver",
          nonTransfer.length
            ? `${topCategory.key} accounts for ${formatInr(topCategory.value)} of filtered expenses. Excluding money movement and FD transfers, the biggest controllable bucket is ${topLifestyle.key} at ${formatInr(topLifestyle.value)}.`
            : `${topCategory.key} accounts for ${formatInr(topCategory.value)} of filtered expenses. No non-transfer lifestyle bucket appears in this filter.`,
          "info"
        ),
        storyCard(
          "Recurring Baseline",
          `${recurringMerchants} recurring merchants create a visible baseline of ${formatInr(recurringTotal)}. This is the fixed-cost layer to review before cutting one-off spends.`,
          "watch"
        ),
        storyCard(
          "Cash Reliance",
          `Cash withdrawals total ${formatInr(cash)}, or ${formatPct(cashShare)} of expenses. A high share can hide the real category behind offline spending.`,
          cashShare > 0.12 ? "watch" : "info"
        ),
        storyCard(
          "Monthly Context",
          months.length > 1
            ? `${best.month} is the strongest month at ${formatInr(best.net)} net savings, while ${worst.month} is the weakest at ${formatInr(worst.net)}.`
            : months.length === 1
              ? `${months[0].month} ends at ${formatInr(months[0].net)} net savings after ${formatInr(months[0].expenses)} of expenses.`
              : "No transactions match the current filters.",
          "info"
        )
      ];
      document.getElementById("storyCards").innerHTML = cards.join("");
    }
    function renderTrend(rows) {
      const grouped = groupSum(rows.filter(row => Number(row.withdrawal_amount) > 0), "transaction_date", "withdrawal_amount")
        .sort((a, b) => new Date(a.key) - new Date(b.key));
      Plotly.react("trendChart", [{
        type: "scatter",
        mode: "lines",
        x: grouped.map(row => row.key),
        y: grouped.map(row => row.value),
        line: { color: "#60a5fa", width: 2 }
      }], layoutBase, plotConfig);
    }
    function renderCash(rows) {
      const cashRows = rows.filter(row => row.category === "Cash Withdrawal");
      const labels = sortedMonthLabels(rows);
      const values = labels.map(label => sum(cashRows.filter(row => row.month_year === label), "withdrawal_amount"));
      Plotly.react("cashChart", [{
        type: "bar",
        x: labels,
        y: values,
        marker: { color: "#f59e0b" }
      }], layoutBase, plotConfig);
    }
    function renderRecurring() {
      const rows = recurringPayments.slice(0, 80);
      const header = "<thead><tr><th>Merchant</th><th>Category</th><th>Count</th><th>Avg Amount</th><th>Total</th><th>Pattern</th></tr></thead>";
      const body = rows.map(row => `
        <tr>
          <td>${row.merchant}</td><td>${row.category}</td><td>${row.occurrence_count}</td>
          <td>${formatInr(row.avg_amount)}</td><td class="amount-debit">${formatInr(row.total_amount)}</td><td>${row.recurrence_pattern}</td>
        </tr>`).join("");
      document.getElementById("recurringTable").innerHTML = header + `<tbody>${body}</tbody>`;
    }
    function renderTransactions(rows) {
      const visible = rows.slice().sort((a, b) => new Date(b.transaction_date) - new Date(a.transaction_date)).slice(0, 250);
      const header = "<thead><tr><th>Date</th><th>Merchant</th><th>Category</th><th>Mode</th><th>Credit</th><th>Debit</th><th>Balance</th></tr></thead>";
      const body = visible.map(row => `
        <tr>
          <td>${row.transaction_date}</td><td>${row.merchant}</td><td>${row.category}</td><td>${row.mode}</td>
          <td class="amount-credit">${Number(row.deposit_amount) ? formatInr(row.deposit_amount) : ""}</td>
          <td class="amount-debit">${Number(row.withdrawal_amount) ? formatInr(row.withdrawal_amount) : ""}</td>
          <td>${formatInr(row.balance)}</td>
        </tr>`).join("");
      document.getElementById("transactionTable").innerHTML = header + `<tbody>${body}</tbody>`;
    }
    function render() {
      const rows = currentRows();
      renderKpis(rows);
      renderMonthly(rows);
      renderCategory(rows);
      renderStory(rows);
      renderTrend(rows);
      renderCash(rows);
      renderRecurring();
      renderTransactions(rows);
    }
    initFilters();
    [monthFilter, categoryFilter, searchFilter].forEach(element => element.addEventListener("input", render));
    render();
  </script>
</body>
</html>
"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build the optional HTML expense dashboard.")
    parser.add_argument("--processed-dir", type=Path, default=Path("data/processed"))
    parser.add_argument("--output", type=Path, default=Path("dashboard/index.html"))
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    build_dashboard(args.processed_dir, args.output)
    print(f"HTML dashboard created: {args.output}")


if __name__ == "__main__":
    main()

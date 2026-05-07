# Power BI Dashboard Build Guide

Use the processed CSV files from `data/processed/` as the Power BI data source.

## Data Sources

Load these files:

- `transactions_clean.csv`
- `monthly_summary.csv`
- `recurring_payments.csv`
- `merchant_summary.csv`
- `categories.csv`

Recommended model:

- `transactions[category]` to `categories[category]`
- Use `transactions` as the fact table.
- Use `monthly_summary` for month-level KPI validation.
- Use `recurring_payments` and `merchant_summary` as analytical summary tables.

## Dashboard Pages

Page 1: Executive Overview

- KPI cards: Total Income, Total Expenses, Net Savings, Savings Rate, Average Monthly Expense
- Clustered column chart: monthly income vs expenses
- Line chart: monthly expense trend
- Donut or bar chart: category-wise spending
- Data Story insight cards: savings pressure, controllable spend, recurring baseline, cash reliance
- Slicers: month, category

Page 2: Spending Deep Dive

- Category and sub-category matrix
- Highest spending days
- Spending by payment mode
- Cash withdrawal trend

Page 3: Recurring Payments

- Recurring payment table
- Merchant, category, occurrence count, average amount, total amount, recurrence pattern
- Trend by recurring merchant

Page 4: Transaction Explorer

- Searchable transaction table
- Filters for month, category, mode, merchant, transaction type

## Visual Style

- Use a light finance dashboard theme.
- Primary accent: teal or blue.
- Positive values: green.
- Expenses and negative savings: red.
- Keep visuals dense, readable, and business-oriented.

## Screenshot Placeholder

Add dashboard screenshots to `powerbi/screenshots/` before publishing the project on GitHub.

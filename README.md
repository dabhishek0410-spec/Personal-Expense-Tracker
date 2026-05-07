# Personal Expense Analytics

End-to-end finance analytics project built from an ICICI Bank savings account statement for Apr 2025 to Mar 2026. The project extracts raw PDF transactions with Python, cleans and categorizes expenses, loads a SQLite analytics database, provides SQL analysis queries, and includes a portfolio-ready HTML dashboard plus Power BI build documentation.

## Project Objective

Convert a raw bank statement PDF into a structured personal finance analytics workflow that can answer:

- How much money came in and went out each month?
- Which categories and merchants drive spending?
- What recurring payments are visible?
- How do cash withdrawals and savings rate trend over time?
- Which transactions need closer review?

## Tools Used

- Python: PDF extraction, cleaning, categorization, summaries
- SQL / SQLite: dimensional tables and analytical queries
- Power BI: dashboard design, KPI measures, reporting layer
- HTML / JavaScript: optional interactive dashboard
- Pandas, NumPy, Poppler `pdftotext`

## Folder Structure

```text
personal-expense-analytics/
  data/
    raw/
    processed/
  notebooks/
  scripts/
  sql/
  powerbi/
  dashboard/
  README.md
  requirements.txt
```

## Workflow

1. Extract PDF table text with coordinates using `pdftotext -tsv`.
2. Reconstruct wrapped transaction particulars across pages.
3. Clean dates, amounts, modes, merchants, categories, and sub-categories.
4. Detect recurring merchant payments.
5. Generate CSV summary tables.
6. Load SQLite tables for SQL analysis.
7. Build a standalone HTML dashboard.
8. Use the processed CSVs to build the Power BI dashboard.

## How To Run

Install Python dependencies:

```bash
pip install -r requirements.txt
```

Install Poppler if `pdftotext` is unavailable:

```bash
brew install poppler
```

Run the full pipeline:

```bash
python scripts/run_pipeline.py --pdf "data/raw/Financial_Statement_2025-26.pdf"
```

Outputs:

- `data/processed/transactions_clean.csv`
- `data/processed/monthly_summary.csv`
- `data/processed/recurring_payments.csv`
- `data/processed/merchant_summary.csv`
- `data/processed/categories.csv`
- `data/expense_analytics.sqlite`
- `dashboard/index.html`

## Generated Dataset

The ETL creates these transaction columns:

- `transaction_date`
- `month`
- `year`
- `description`
- `mode`
- `merchant`
- `deposit_amount`
- `withdrawal_amount`
- `balance`
- `transaction_type`
- `category`
- `sub_category`

Additional helper fields include `transaction_id`, `month_number`, `month_start`, `month_year`, `page`, and `is_recurring`.

## Key Insights From Current Statement

- Total transactions: 2,194
- Total income/deposits: INR 845,071.28
- Total expenses/withdrawals: INR 861,129.52
- Net savings: INR -16,058.24
- Savings rate: -1.90%
- Average monthly expense: INR 71,760.79
- Largest spending groups: Transfers, Cash Withdrawal, Food & Dining, Shopping, Investments/FD
- Notable recurring merchants: Zomato, Amazon, Swiggy, Indian Railways, Airtel, Netflix, Zepto, Delhi Metro
- Netflix appears as a monthly recurring subscription at INR 649 per month.

## Data Storytelling Insights

- The year is slightly cash-flow negative: expenses exceeded income by INR 16,058.24, so the dashboard should be read as a savings-rate recovery problem, not only a spending tracker.
- Transfers dominate the statement at INR 566,034.52. This suggests heavy money movement between people/accounts, so lifestyle analysis should focus on non-transfer categories.
- Cash withdrawals total INR 87,700.00. This is important because cash usage hides the final merchant/category, making offline spend less transparent.
- Food & Dining and Shopping together account for INR 103,924.77. These are the clearest controllable lifestyle buckets after excluding transfers, FD movement, and cash.
- Recurring payments create a baseline expense layer. Netflix is consistently monthly, while Zomato, Swiggy, Amazon, Airtel, Zepto, and Delhi Metro show frequent repeat behavior.
- March 2026 is the weakest month with INR -16,150.24 net savings, while September 2025 is the strongest month with INR 13,551.00 net savings.

## SQL Analysis

The SQL scripts include:

- Monthly income vs expenses
- Category-wise spending
- Highest spending days
- Recurring expenses
- Cash withdrawal trend
- Savings rate
- Average daily spend
- Month-on-month expense growth
- Spending by payment mode
- Data storytelling snapshot

Files:

- `sql/schema.sql`
- `sql/analysis_queries.sql`

## Power BI Dashboard

Power BI documentation is in `powerbi/`.

Recommended visuals:

- KPI cards: Total Income, Total Expenses, Net Savings, Savings Rate, Average Monthly Expense
- Monthly income vs expense chart
- Category-wise expense breakdown
- Data Story insight cards
- Recurring payments table
- Transaction explorer with filters
- Spending trend line chart
- Cash withdrawal analysis
- Month and category slicers

Dashboard screenshot placeholders:

- `powerbi/screenshots/overview.png`
- `powerbi/screenshots/recurring_payments.png`
- `powerbi/screenshots/transaction_explorer.png`

## Optional HTML Dashboard

Open:

```text
dashboard/index.html
```

It includes KPI cards, month and category filters, narrative insight cards, category breakdowns, recurring payments, cash withdrawal trends, and a transaction explorer.

## Premium KPI Layout Approach

- Make the outcome metric the anchor: Net Savings is shown as the widest KPI because it summarizes the financial position.
- Keep supporting metrics compact: Total Income, Total Expenses, Savings Rate, and Average Monthly Expense sit beside the anchor card.
- Use color by meaning, not decoration: green for income, red for expenses/negative savings, teal for savings, amber for rate signals, and blue for averages.
- Separate reading levels: label, value, and note are stacked consistently so the dashboard scans like an executive finance summary.
- Use dark glassmorphism subtly: translucent cards, soft borders, blur, and controlled contrast give a premium feel without reducing readability.

## Business Impact

This project turns unstructured bank statement data into a repeatable analytics pipeline. It helps identify spending concentration, recurring costs, savings rate movement, high cash usage, and merchant-level expense behavior. The same workflow can be adapted for budgeting, personal finance monitoring, or small-business bank statement analytics.

## Resume Bullets

- Built an end-to-end personal finance analytics pipeline using Python, SQL, and Power BI concepts to transform a 108-page bank statement PDF into structured transaction, merchant, recurring payment, and monthly summary datasets.
- Developed rule-based expense categorization and recurring payment detection across 2,194 transactions, enabling month-wise income, expense, savings rate, category, merchant, and cash withdrawal analysis.
- Created a SQLite analytics database, reusable SQL query library, and interactive HTML dashboard to demonstrate portfolio-ready financial reporting and dashboarding skills.

## Privacy Note

Raw bank statements and processed descriptions can contain sensitive personal information. Keep `data/raw/` private and anonymize processed data before publishing the project publicly.

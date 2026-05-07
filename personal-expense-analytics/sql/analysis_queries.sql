-- 1. Monthly income vs expenses
SELECT
    month_year,
    total_income,
    total_expenses,
    net_savings,
    ROUND(savings_rate * 100, 2) AS savings_rate_pct
FROM monthly_summary
ORDER BY year, month_number;

-- 2. Category-wise spending
SELECT
    category,
    ROUND(SUM(withdrawal_amount), 2) AS total_spend,
    COUNT(*) AS transaction_count,
    ROUND(AVG(NULLIF(withdrawal_amount, 0)), 2) AS avg_debit
FROM transactions
WHERE withdrawal_amount > 0
GROUP BY category
ORDER BY total_spend DESC;

-- 3. Highest spending days
SELECT
    transaction_date,
    ROUND(SUM(withdrawal_amount), 2) AS total_spend,
    COUNT(*) AS debit_transactions
FROM transactions
WHERE withdrawal_amount > 0
GROUP BY transaction_date
ORDER BY total_spend DESC
LIMIT 15;

-- 4. Recurring expenses
SELECT
    merchant,
    category,
    occurrence_count,
    active_months,
    avg_amount,
    total_amount,
    recurrence_pattern,
    first_payment_date,
    last_payment_date
FROM recurring_payments
ORDER BY total_amount DESC;

-- 5. Cash withdrawal trend
SELECT
    month_year,
    ROUND(SUM(withdrawal_amount), 2) AS cash_withdrawal_amount,
    COUNT(*) AS cash_withdrawal_count
FROM transactions
WHERE category = 'Cash Withdrawal'
GROUP BY year, month_number, month_year
ORDER BY year, month_number;

-- 6. Savings rate
SELECT
    month_year,
    total_income,
    total_expenses,
    net_savings,
    ROUND(100.0 * net_savings / NULLIF(total_income, 0), 2) AS savings_rate_pct
FROM monthly_summary
ORDER BY year, month_number;

-- 7. Average daily spend
SELECT
    month_year,
    total_expenses,
    avg_daily_spend
FROM monthly_summary
ORDER BY year, month_number;

-- 8. Month-on-month expense growth
WITH expense_growth AS (
    SELECT
        month_year,
        year,
        month_number,
        total_expenses,
        LAG(total_expenses) OVER (ORDER BY year, month_number) AS previous_month_expense
    FROM monthly_summary
)
SELECT
    month_year,
    total_expenses,
    previous_month_expense,
    ROUND(
        100.0 * (total_expenses - previous_month_expense) / NULLIF(previous_month_expense, 0),
        2
    ) AS mom_expense_growth_pct
FROM expense_growth
ORDER BY year, month_number;

-- 9. Spending by mode
SELECT
    mode,
    ROUND(SUM(withdrawal_amount), 2) AS total_spend,
    COUNT(*) AS transactions
FROM transactions
WHERE withdrawal_amount > 0
GROUP BY mode
ORDER BY total_spend DESC;

-- 10. Data storytelling snapshot
WITH totals AS (
    SELECT
        SUM(deposit_amount) AS income,
        SUM(withdrawal_amount) AS expenses,
        SUM(deposit_amount) - SUM(withdrawal_amount) AS net_savings
    FROM transactions
),
category_spend AS (
    SELECT
        category,
        SUM(withdrawal_amount) AS spend,
        RANK() OVER (ORDER BY SUM(withdrawal_amount) DESC) AS spend_rank
    FROM transactions
    WHERE withdrawal_amount > 0
    GROUP BY category
),
cash AS (
    SELECT SUM(withdrawal_amount) AS cash_withdrawal
    FROM transactions
    WHERE category = 'Cash Withdrawal'
),
recurring AS (
    SELECT SUM(total_amount) AS recurring_total
    FROM recurring_payments
)
SELECT
    ROUND(t.income, 2) AS total_income,
    ROUND(t.expenses, 2) AS total_expenses,
    ROUND(t.net_savings, 2) AS net_savings,
    ROUND(100.0 * t.net_savings / NULLIF(t.income, 0), 2) AS savings_rate_pct,
    c.category AS largest_spend_category,
    ROUND(c.spend, 2) AS largest_category_spend,
    ROUND(ca.cash_withdrawal, 2) AS cash_withdrawal,
    ROUND(100.0 * ca.cash_withdrawal / NULLIF(t.expenses, 0), 2) AS cash_withdrawal_share_pct,
    ROUND(r.recurring_total, 2) AS recurring_payment_total
FROM totals t
CROSS JOIN category_spend c
CROSS JOIN cash ca
CROSS JOIN recurring r
WHERE c.spend_rank = 1;

-- 11. Transaction explorer base query
SELECT
    transaction_date,
    month_year,
    mode,
    merchant,
    category,
    sub_category,
    deposit_amount,
    withdrawal_amount,
    balance,
    description
FROM transactions
ORDER BY transaction_date DESC, transaction_id DESC;

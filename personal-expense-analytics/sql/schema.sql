DROP TABLE IF EXISTS transactions;
DROP TABLE IF EXISTS categories;
DROP TABLE IF EXISTS monthly_summary;
DROP TABLE IF EXISTS recurring_payments;
DROP TABLE IF EXISTS merchant_summary;

CREATE TABLE transactions (
    transaction_id INTEGER PRIMARY KEY,
    transaction_date DATE NOT NULL,
    month TEXT NOT NULL,
    month_number INTEGER NOT NULL,
    year INTEGER NOT NULL,
    month_start DATE NOT NULL,
    month_year TEXT NOT NULL,
    description TEXT NOT NULL,
    mode TEXT,
    merchant TEXT,
    deposit_amount REAL DEFAULT 0,
    withdrawal_amount REAL DEFAULT 0,
    balance REAL,
    transaction_type TEXT CHECK (transaction_type IN ('Credit', 'Debit')),
    category TEXT,
    sub_category TEXT,
    page INTEGER,
    is_recurring INTEGER DEFAULT 0
);

CREATE TABLE categories (
    category_id INTEGER PRIMARY KEY,
    category TEXT NOT NULL,
    sub_category TEXT NOT NULL
);

CREATE TABLE monthly_summary (
    year INTEGER NOT NULL,
    month_number INTEGER NOT NULL,
    month TEXT NOT NULL,
    month_start DATE PRIMARY KEY,
    month_year TEXT NOT NULL,
    total_income REAL,
    total_expenses REAL,
    transaction_count INTEGER,
    cash_withdrawal REAL,
    net_savings REAL,
    savings_rate REAL,
    avg_daily_spend REAL,
    recurring_expense REAL,
    top_category TEXT
);

CREATE TABLE recurring_payments (
    merchant TEXT NOT NULL,
    category TEXT,
    sub_category TEXT,
    occurrence_count INTEGER,
    active_months INTEGER,
    avg_amount REAL,
    total_amount REAL,
    first_payment_date DATE,
    last_payment_date DATE,
    median_days_between REAL,
    recurrence_pattern TEXT,
    is_recurring INTEGER
);

CREATE TABLE merchant_summary (
    merchant TEXT NOT NULL,
    category TEXT,
    sub_category TEXT,
    transaction_count INTEGER,
    total_income REAL,
    total_spend REAL,
    avg_transaction_amount REAL,
    first_transaction_date DATE,
    last_transaction_date DATE,
    net_amount REAL
);

CREATE INDEX idx_transactions_date ON transactions (transaction_date);
CREATE INDEX idx_transactions_month ON transactions (year, month_number);
CREATE INDEX idx_transactions_category ON transactions (category);
CREATE INDEX idx_transactions_merchant ON transactions (merchant);

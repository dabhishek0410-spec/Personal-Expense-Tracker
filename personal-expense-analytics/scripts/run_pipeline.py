"""Run the full personal expense analytics pipeline."""

from __future__ import annotations

import argparse
from pathlib import Path

from build_html_dashboard import build_dashboard
from extract_transform import build_transactions, parse_statement, write_outputs
from load_sqlite import load_database


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run PDF extraction, CSV generation, SQLite load, and HTML build.")
    parser.add_argument("--pdf", required=True, type=Path, help="Path to the bank statement PDF.")
    parser.add_argument("--processed-dir", type=Path, default=Path("data/processed"))
    parser.add_argument("--db-path", type=Path, default=Path("data/expense_analytics.sqlite"))
    parser.add_argument("--schema", type=Path, default=Path("sql/schema.sql"))
    parser.add_argument("--dashboard", type=Path, default=Path("dashboard/index.html"))
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    raw = parse_statement(args.pdf)
    transactions = build_transactions(raw)
    write_outputs(transactions, args.processed_dir)
    load_database(args.processed_dir, args.db_path, args.schema)
    build_dashboard(args.processed_dir, args.dashboard)

    print("Pipeline complete")
    print(f"Transactions: {len(transactions):,}")
    print(f"Total income/deposits: {transactions['deposit_amount'].sum():,.2f}")
    print(f"Total expenses/withdrawals: {transactions['withdrawal_amount'].sum():,.2f}")
    print(f"Processed CSVs: {args.processed_dir}")
    print(f"SQLite database: {args.db_path}")
    print(f"HTML dashboard: {args.dashboard}")


if __name__ == "__main__":
    main()

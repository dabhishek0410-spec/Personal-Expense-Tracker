"""Load processed expense analytics CSV files into SQLite."""

from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path

import pandas as pd


TABLE_FILES = {
    "transactions": "transactions_clean.csv",
    "categories": "categories.csv",
    "monthly_summary": "monthly_summary.csv",
    "recurring_payments": "recurring_payments.csv",
    "merchant_summary": "merchant_summary.csv",
}


def load_database(processed_dir: Path, db_path: Path, schema_path: Path) -> None:
    missing = [file_name for file_name in TABLE_FILES.values() if not (processed_dir / file_name).exists()]
    if missing:
        raise FileNotFoundError(f"Missing processed CSV files: {', '.join(missing)}")

    db_path.parent.mkdir(parents=True, exist_ok=True)
    schema_sql = schema_path.read_text(encoding="utf-8")

    with sqlite3.connect(db_path) as conn:
        conn.executescript(schema_sql)
        for table, file_name in TABLE_FILES.items():
            df = pd.read_csv(processed_dir / file_name)
            df.to_sql(table, conn, if_exists="append", index=False)
        conn.commit()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Load processed CSV files into a SQLite analytics database.")
    parser.add_argument("--processed-dir", type=Path, default=Path("data/processed"))
    parser.add_argument("--db-path", type=Path, default=Path("data/expense_analytics.sqlite"))
    parser.add_argument("--schema", type=Path, default=Path("sql/schema.sql"))
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    load_database(args.processed_dir, args.db_path, args.schema)
    print(f"SQLite database created: {args.db_path}")


if __name__ == "__main__":
    main()

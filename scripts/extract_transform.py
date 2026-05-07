"""Extract, clean, and enrich ICICI bank statement transactions.

The ICICI PDF used for this project is text-based, but the transaction
particulars wrap across multiple PDF lines. This script uses Poppler's
``pdftotext -tsv`` output so it can use x/y coordinates instead of brittle
plain-text splitting.
"""

from __future__ import annotations

import argparse
import csv
import io
import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd


DATE_RE = re.compile(r"\d{2}-\d{2}-\d{4}")
MONEY_RE = re.compile(r"^\d{1,3}(?:,\d{3})*(?:\.\d{2})$|^\d+\.\d{2}$")

TRANSACTION_START_RE = re.compile(
    r"^(?:"
    r"B/F$|UPI/|NFS/|EBA/|BIL/|INF/|NEFT|RTGS|IMPS|ACH|NACH|"
    r"VPS/|IPS/|ATM/|CAM/|CashDep|Cash Dep|Cashdep|CASH|BY CASH|"
    r"BY TRANSFER|TO TRANSFER|[0-9]{10,}:Int\.Pd|.*:Int\.Pd:|"
    r"Interest|Int\.Pd|FD |Fixed Deposit|MMT/|MPS/|MIN/|MCD\b|"
    r"SMSChgs|TRF TO FD|DCARDFEE|POS/|CMS/|REV|REF|RETURN|Charges|Chgs"
    r")",
    re.IGNORECASE,
)

CATEGORY_ROWS = [
    ("Food & Dining", "Food delivery", r"swiggy|zomato|eternal|food|restaurant|cafe|pizza|burger|kfc|taco bell|mcd\b|mcdonald"),
    ("Travel", "Metro/Rail", r"dmrc|delhimetro|autope pay|metro|irctc|indianrailway|railway|uber|ola|redbus|makemytrip"),
    ("Shopping", "E-commerce", r"amazon|flipkart|myntra|nykaa|nobero|rawbare|kosher|zepto|blinkit|bigbasket|meesho|dailyobjects"),
    ("Subscriptions", "Streaming/App subscription", r"netflix|apple|spotify|prime|hotstar|sonyliv|subscription|mandaterequest|upi mandate"),
    ("Utilities", "Telecom/Bills", r"airtel(?! pay)|jio|vi\b|vodafone|recharge|electricity|billpay|broadband|gas|dth"),
    ("Cash Withdrawal", "ATM cash withdrawal", r"cash wdl|nfs/cash|atm"),
    ("Refunds", "Refund/Cashback", r"refund|cashback|reversal|bhimcashback|return"),
    ("Investments/FD", "Fixed deposit", r"trf to fd|fixed deposit|fd no\.|int\.pd"),
    ("Education", "Education fees", r"iquanta|ignou|student|exam|course|school|college|university|education"),
    ("Transfers", "Self/peer transfer", r"d abhishek|abhishek401|payment fr|payment from|pay by whatsapp|trf|upi/.*state bank"),
]

MERCHANT_ALIASES = [
    (r"netflix", "Netflix"),
    (r"swiggy", "Swiggy"),
    (r"zomato|eternal", "Zomato"),
    (r"dmrc|delhimetro|autope pay", "Delhi Metro"),
    (r"amazon|amazonrecha|www amazon|amazon pay", "Amazon"),
    (r"airtel(?! pay)", "Airtel"),
    (r"apple", "Apple Services"),
    (r"zepto", "Zepto"),
    (r"indianrailway|irctc", "Indian Railways"),
    (r"iquanta", "iQuanta"),
    (r"ignou", "IGNOU"),
    (r"taco bell", "Taco Bell"),
    (r"bookmyshow|bigtree", "BookMyShow"),
    (r"cred", "CRED"),
    (r"bhimcashback|npci", "NPCI/BHIM"),
    (r"cash wdl|nfs/cash", "ATM Cash Withdrawal"),
    (r"cash dep|cam/", "Cash Deposit"),
    (r"trf to fd|fd no\.", "Fixed Deposit"),
    (r"int\.pd", "ICICI Interest"),
    (r"smschgs|dcardfee|charges|chgs", "Bank Charges"),
]

GENERIC_UPI_TOKENS = {
    "",
    "upi",
    "payment",
    "payment fr",
    "payment from",
    "payment from ph",
    "payment from sl",
    "pay",
    "pay for",
    "no remarks",
    "collect transac",
    "mandaterequest",
    "upi mandate",
}


@dataclass
class Word:
    page: int
    line: int
    word: int
    left: float
    top: float
    text: str


@dataclass
class Line:
    page: int
    top: float
    words: list[Word]

    @property
    def text(self) -> str:
        return " ".join(word.text for word in self.words)


@dataclass
class Anchor:
    page: int
    top: float
    date_text: str


def money_to_float(value: str | float | int | None) -> float:
    if value in ("", None) or (isinstance(value, float) and np.isnan(value)):
        return 0.0
    return float(str(value).replace(",", ""))


def run_pdftotext(pdf_path: Path) -> str:
    if not shutil.which("pdftotext"):
        raise RuntimeError(
            "Poppler is required. Install it, then rerun: "
            "macOS `brew install poppler`, Ubuntu `sudo apt install poppler-utils`."
        )

    result = subprocess.run(
        ["pdftotext", "-tsv", str(pdf_path), "-"],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout


def parse_words(tsv_text: str) -> list[Word]:
    reader = csv.DictReader(io.StringIO(tsv_text), delimiter="\t")
    words: list[Word] = []
    for row in reader:
        if row.get("level") != "5":
            continue
        text = row.get("text", "").strip()
        if not text or text == "###PAGE###":
            continue
        words.append(
            Word(
                page=int(row["page_num"]),
                line=int(row["line_num"]),
                word=int(row["word_num"]),
                left=float(row["left"]),
                top=float(row["top"]),
                text=text,
            )
        )
    return words


def group_lines(words: Iterable[Word]) -> list[Line]:
    grouped: dict[tuple[int, int, float], list[Word]] = {}
    for word in words:
        key = (word.page, word.line, round(word.top, 1))
        grouped.setdefault(key, []).append(word)

    lines = []
    for (page, _line, top), line_words in grouped.items():
        lines.append(Line(page=page, top=top, words=sorted(line_words, key=lambda item: item.left)))
    return sorted(lines, key=lambda line: (line.page, line.top))


def find_anchors(lines: Iterable[Line]) -> list[Anchor]:
    anchors: list[Anchor] = []
    for line in lines:
        for word in line.words:
            if 20 <= word.left <= 70 and DATE_RE.fullmatch(word.text):
                anchors.append(Anchor(page=line.page, top=word.top, date_text=word.text))
    return sorted(anchors, key=lambda item: (item.page, item.top))


def extract_description_segments(page_lines: list[Line], anchors: list[Anchor]) -> list[str]:
    if not anchors:
        return []

    min_top = anchors[0].top - 20
    max_top = anchors[-1].top + 35
    description_lines: list[tuple[float, str]] = []

    for line in page_lines:
        if not (min_top <= line.top <= max_top):
            continue
        words = [word.text for word in line.words if 145 <= word.left < 370]
        if not words:
            continue
        text = " ".join(words).strip()
        if text == "PARTICULARS" or text.upper().startswith("TOTAL"):
            continue
        description_lines.append((line.top, text))

    segments: list[list[tuple[float, str]]] = []
    current: list[tuple[float, str]] = []
    for item in description_lines:
        if TRANSACTION_START_RE.search(item[1]) or not current:
            if current:
                segments.append(current)
            current = [item]
        else:
            current.append(item)
    if current:
        segments.append(current)

    if len(segments) == len(anchors):
        return [" ".join(text for _top, text in segment) for segment in segments]

    # Fallback for differently formatted statements: assign particulars by vertical midpoint.
    descriptions = []
    for idx, anchor in enumerate(anchors):
        previous_top = anchors[idx - 1].top if idx > 0 else None
        next_top = anchors[idx + 1].top if idx + 1 < len(anchors) else None
        start = (previous_top + anchor.top) / 2 if previous_top is not None else anchor.top - 20
        end = (anchor.top + next_top) / 2 if next_top is not None else anchor.top + 25
        parts = [text for top, text in description_lines if start <= top < end]
        descriptions.append(" ".join(parts))
    return descriptions


def collect_amounts_and_mode(page_lines: list[Line], anchors: list[Anchor], idx: int) -> tuple[str, str, str, str]:
    anchor = anchors[idx]
    previous_top = anchors[idx - 1].top if idx > 0 else None
    next_top = anchors[idx + 1].top if idx + 1 < len(anchors) else None
    start = (previous_top + anchor.top) / 2 if previous_top is not None else anchor.top - 20
    end = (anchor.top + next_top) / 2 if next_top is not None else anchor.top + 25

    mode_words: list[str] = []
    deposits: list[str] = []
    withdrawals: list[str] = []
    balances: list[str] = []

    for line in page_lines:
        if not (start <= line.top < end):
            continue
        if abs(line.top - anchor.top) < 2:
            mode_words.extend(word.text for word in line.words if 70 <= word.left < 145 and word.text != "MODE**")
        for word in line.words:
            if not MONEY_RE.fullmatch(word.text):
                continue
            if 365 <= word.left < 440:
                deposits.append(word.text)
            elif 440 <= word.left < 530:
                withdrawals.append(word.text)
            elif 530 <= word.left < 590:
                balances.append(word.text)

    return (
        " ".join(mode_words).strip(),
        deposits[-1] if deposits else "",
        withdrawals[-1] if withdrawals else "",
        balances[-1] if balances else "",
    )


def parse_statement(pdf_path: Path) -> pd.DataFrame:
    words = parse_words(run_pdftotext(pdf_path))
    lines = group_lines(words)
    anchors = find_anchors(lines)
    lines_by_page = {page: [line for line in lines if line.page == page] for page in sorted({line.page for line in lines})}
    anchors_by_page = {
        page: [anchor for anchor in anchors if anchor.page == page] for page in sorted({anchor.page for anchor in anchors})
    }

    records: list[dict[str, object]] = []
    for page, page_anchors in anchors_by_page.items():
        page_lines = lines_by_page.get(page, [])
        descriptions = extract_description_segments(page_lines, page_anchors)
        for idx, anchor in enumerate(page_anchors):
            mode, deposit, withdrawal, balance = collect_amounts_and_mode(page_lines, page_anchors, idx)
            records.append(
                {
                    "page": page,
                    "transaction_date": anchor.date_text,
                    "description": descriptions[idx] if idx < len(descriptions) else "",
                    "mode": mode,
                    "deposit_amount": money_to_float(deposit),
                    "withdrawal_amount": money_to_float(withdrawal),
                    "balance": money_to_float(balance),
                }
            )

    raw_df = pd.DataFrame(records)
    if raw_df.empty:
        raise ValueError("No transactions were extracted from the statement.")
    return raw_df


def normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", str(value)).strip()


def infer_mode(description: str, mode: str) -> str:
    if mode:
        return normalize_text(mode).title()

    desc = description.upper()
    if desc.startswith("UPI/"):
        return "UPI"
    if "CASH WDL" in desc or "NFS/CASH" in desc:
        return "ATM"
    if desc.startswith(("MPS/", "MIN/", "POS/")) or "DCARDFEE" in desc:
        return "Card"
    if "CASH DEP" in desc or desc.startswith("CAM/"):
        return "Cash Deposit"
    if "INT.PD" in desc:
        return "Interest"
    if "TRF TO FD" in desc:
        return "Internal Transfer"
    if "SMSCHGS" in desc or "CHGS" in desc or "CHARGES" in desc:
        return "Bank Charges"
    return "Other"


def clean_merchant_name(value: str) -> str:
    value = re.sub(r"[@_]+", " ", value)
    value = re.sub(r"\s+", " ", value)
    value = re.sub(r"[^A-Za-z0-9 .&/-]", "", value).strip(" /-")
    if not value:
        return "Unknown"
    return value[:55].title()


def extract_merchant(description: str) -> str:
    desc = normalize_text(description)
    desc_lower = desc.lower()

    for pattern, merchant in MERCHANT_ALIASES:
        if re.search(pattern, desc_lower):
            return merchant

    if desc_lower.startswith("upi/"):
        parts = [part.strip() for part in desc.split("/") if part.strip()]
        if len(parts) > 1:
            candidate = parts[1]
            candidate_lower = candidate.lower()
            if ("@" in candidate or re.fullmatch(r"q?\d{6,}.*", candidate_lower)) and len(parts) > 2:
                fallback = parts[2].strip()
                if fallback.lower() not in GENERIC_UPI_TOKENS:
                    candidate = fallback
            if candidate.lower() in GENERIC_UPI_TOKENS and len(parts) > 2:
                candidate = parts[2]
            return clean_merchant_name(candidate)

    if "/" in desc:
        return clean_merchant_name(desc.split("/")[0])
    return clean_merchant_name(desc[:45])


def categorize_transaction(description: str, merchant: str, deposit: float, withdrawal: float) -> tuple[str, str]:
    desc = normalize_text(description).lower()
    merchant_lower = merchant.lower()
    combined = f"{desc} {merchant_lower}"

    if deposit > 0 and re.search(r"refund|cashback|reversal|bhimcashback|return", combined):
        return "Refunds", "Refund/Cashback"
    if "int.pd" in combined and deposit > 0:
        return "Investments/FD", "Interest income"
    if deposit > 0:
        return "Transfers", "Incoming transfer"

    if "cash wdl" in combined or "nfs/cash" in combined or merchant == "ATM Cash Withdrawal":
        return "Cash Withdrawal", "ATM cash withdrawal"
    if "trf to fd" in combined or "fd no." in combined:
        return "Investments/FD", "Fixed deposit transfer"
    if re.search(r"smschgs|dcardfee|charges|chgs", combined):
        return "Miscellaneous", "Bank charges"

    for category, sub_category, pattern in CATEGORY_ROWS:
        if re.search(pattern, combined):
            return category, sub_category

    if desc.startswith("upi/") or "payment fr" in combined or "payment from" in combined:
        return "Transfers", "Peer/self transfer"
    return "Miscellaneous", "Uncategorized"


def build_transactions(raw_df: pd.DataFrame) -> pd.DataFrame:
    df = raw_df.copy()
    df["description"] = df["description"].map(normalize_text)
    df = df[df["description"].str.upper().ne("B/F")].copy()
    df = df[(df["deposit_amount"] > 0) | (df["withdrawal_amount"] > 0)].copy()

    parsed_dates = pd.to_datetime(df["transaction_date"], format="%d-%m-%Y", errors="coerce")
    if parsed_dates.isna().any():
        bad_rows = df.loc[parsed_dates.isna(), "transaction_date"].unique()
        raise ValueError(f"Unparseable transaction dates found: {bad_rows}")

    df["transaction_date"] = parsed_dates.dt.date.astype(str)
    df["year"] = parsed_dates.dt.year
    df["month_number"] = parsed_dates.dt.month
    df["month"] = parsed_dates.dt.month_name()
    df["month_start"] = parsed_dates.dt.to_period("M").dt.to_timestamp().dt.date.astype(str)
    df["month_year"] = parsed_dates.dt.strftime("%b %Y")
    df["mode"] = [infer_mode(desc, mode) for desc, mode in zip(df["description"], df["mode"], strict=False)]
    df["merchant"] = df["description"].map(extract_merchant)

    categories = [
        categorize_transaction(row.description, row.merchant, row.deposit_amount, row.withdrawal_amount)
        for row in df.itertuples(index=False)
    ]
    df["category"] = [item[0] for item in categories]
    df["sub_category"] = [item[1] for item in categories]
    df["transaction_type"] = np.where(df["deposit_amount"] > 0, "Credit", "Debit")
    df.insert(0, "transaction_id", range(1, len(df) + 1))

    ordered_columns = [
        "transaction_id",
        "transaction_date",
        "month",
        "month_number",
        "year",
        "month_start",
        "month_year",
        "description",
        "mode",
        "merchant",
        "deposit_amount",
        "withdrawal_amount",
        "balance",
        "transaction_type",
        "category",
        "sub_category",
        "page",
    ]
    return df[ordered_columns].sort_values(["transaction_date", "transaction_id"]).reset_index(drop=True)


def detect_recurring_payments(transactions: pd.DataFrame) -> pd.DataFrame:
    expenses = transactions[transactions["withdrawal_amount"] > 0].copy()
    expenses = expenses[
        ~expenses["category"].isin(["Transfers", "Cash Withdrawal", "Investments/FD", "Refunds"])
    ].copy()
    if expenses.empty:
        return pd.DataFrame()

    known_recurring = {
        "Netflix",
        "Airtel",
        "Amazon",
        "Swiggy",
        "Zomato",
        "Apple Services",
        "Delhi Metro",
        "Zepto",
        "CRED",
    }

    rows = []
    for (merchant, category, sub_category), group in expenses.groupby(["merchant", "category", "sub_category"]):
        group = group.sort_values("transaction_date")
        dates = pd.to_datetime(group["transaction_date"])
        active_months = group["month_start"].nunique()
        occurrence_count = len(group)
        day_gaps = dates.diff().dt.days.dropna()
        median_gap = float(day_gaps.median()) if not day_gaps.empty else np.nan
        recurring_flag = (occurrence_count >= 3 and active_months >= 2) or (
            merchant in known_recurring and occurrence_count >= 2
        )

        if not recurring_flag:
            continue
        if 20 <= median_gap <= 45:
            pattern = "Monthly"
        elif occurrence_count >= 8:
            pattern = "Frequent"
        else:
            pattern = "Repeating"

        rows.append(
            {
                "merchant": merchant,
                "category": category,
                "sub_category": sub_category,
                "occurrence_count": int(occurrence_count),
                "active_months": int(active_months),
                "avg_amount": round(float(group["withdrawal_amount"].mean()), 2),
                "total_amount": round(float(group["withdrawal_amount"].sum()), 2),
                "first_payment_date": dates.min().date().isoformat(),
                "last_payment_date": dates.max().date().isoformat(),
                "median_days_between": round(median_gap, 1) if not np.isnan(median_gap) else None,
                "recurrence_pattern": pattern,
                "is_recurring": 1,
            }
        )

    recurring = pd.DataFrame(rows)
    if recurring.empty:
        return recurring
    return recurring.sort_values(["total_amount", "occurrence_count"], ascending=[False, False]).reset_index(drop=True)


def build_monthly_summary(transactions: pd.DataFrame, recurring: pd.DataFrame) -> pd.DataFrame:
    tx = transactions.copy()
    tx["date"] = pd.to_datetime(tx["transaction_date"])
    monthly = (
        tx.groupby(["year", "month_number", "month", "month_start", "month_year"], as_index=False)
        .agg(
            total_income=("deposit_amount", "sum"),
            total_expenses=("withdrawal_amount", "sum"),
            transaction_count=("transaction_id", "count"),
            cash_withdrawal=("withdrawal_amount", lambda s: s[tx.loc[s.index, "category"].eq("Cash Withdrawal")].sum()),
        )
        .sort_values(["year", "month_number"])
    )
    monthly["net_savings"] = monthly["total_income"] - monthly["total_expenses"]
    monthly["savings_rate"] = np.where(
        monthly["total_income"] > 0,
        monthly["net_savings"] / monthly["total_income"],
        np.nan,
    )
    days_in_month = pd.to_datetime(monthly["month_start"]).dt.days_in_month
    monthly["avg_daily_spend"] = monthly["total_expenses"] / days_in_month

    recurring_merchants = set(recurring["merchant"]) if not recurring.empty else set()
    tx["is_recurring"] = tx["merchant"].isin(recurring_merchants)
    recurring_monthly = (
        tx[tx["is_recurring"] & (tx["withdrawal_amount"] > 0)]
        .groupby("month_start")["withdrawal_amount"]
        .sum()
        .rename("recurring_expense")
    )
    monthly = monthly.merge(recurring_monthly, on="month_start", how="left")
    monthly["recurring_expense"] = monthly["recurring_expense"].fillna(0)

    category_spend = (
        tx[tx["withdrawal_amount"] > 0]
        .groupby(["month_start", "category"])["withdrawal_amount"]
        .sum()
        .reset_index()
        .sort_values(["month_start", "withdrawal_amount"], ascending=[True, False])
    )
    top_category = category_spend.drop_duplicates("month_start").set_index("month_start")["category"]
    monthly["top_category"] = monthly["month_start"].map(top_category).fillna("No expenses")

    numeric_cols = [
        "total_income",
        "total_expenses",
        "cash_withdrawal",
        "net_savings",
        "savings_rate",
        "avg_daily_spend",
        "recurring_expense",
    ]
    monthly[numeric_cols] = monthly[numeric_cols].round(2)
    return monthly


def build_merchant_summary(transactions: pd.DataFrame) -> pd.DataFrame:
    summary = (
        transactions.groupby(["merchant", "category", "sub_category"], as_index=False)
        .agg(
            transaction_count=("transaction_id", "count"),
            total_income=("deposit_amount", "sum"),
            total_spend=("withdrawal_amount", "sum"),
            avg_transaction_amount=("withdrawal_amount", "mean"),
            first_transaction_date=("transaction_date", "min"),
            last_transaction_date=("transaction_date", "max"),
        )
        .sort_values("total_spend", ascending=False)
    )
    summary["net_amount"] = summary["total_income"] - summary["total_spend"]
    for column in ["total_income", "total_spend", "avg_transaction_amount", "net_amount"]:
        summary[column] = summary[column].fillna(0).round(2)
    return summary.reset_index(drop=True)


def build_categories(transactions: pd.DataFrame) -> pd.DataFrame:
    categories = (
        transactions[["category", "sub_category"]]
        .drop_duplicates()
        .sort_values(["category", "sub_category"])
        .reset_index(drop=True)
    )
    categories.insert(0, "category_id", range(1, len(categories) + 1))
    return categories


def write_outputs(transactions: pd.DataFrame, output_dir: Path) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    recurring = detect_recurring_payments(transactions)
    recurring_merchants = set(recurring["merchant"]) if not recurring.empty else set()
    transactions = transactions.copy()
    transactions["is_recurring"] = transactions["merchant"].isin(recurring_merchants).astype(int)

    monthly = build_monthly_summary(transactions, recurring)
    merchants = build_merchant_summary(transactions)
    categories = build_categories(transactions)

    outputs = {
        "transactions": output_dir / "transactions_clean.csv",
        "monthly_summary": output_dir / "monthly_summary.csv",
        "recurring_payments": output_dir / "recurring_payments.csv",
        "merchant_summary": output_dir / "merchant_summary.csv",
        "categories": output_dir / "categories.csv",
    }

    transactions.to_csv(outputs["transactions"], index=False)
    monthly.to_csv(outputs["monthly_summary"], index=False)
    recurring.to_csv(outputs["recurring_payments"], index=False)
    merchants.to_csv(outputs["merchant_summary"], index=False)
    categories.to_csv(outputs["categories"], index=False)
    return outputs


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Extract and transform ICICI bank statement transactions.")
    parser.add_argument("--pdf", required=True, type=Path, help="Path to the ICICI bank statement PDF.")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data/processed"),
        help="Directory where processed CSV files should be written.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    raw_df = parse_statement(args.pdf)
    transactions = build_transactions(raw_df)
    outputs = write_outputs(transactions, args.output_dir)

    total_income = transactions["deposit_amount"].sum()
    total_expenses = transactions["withdrawal_amount"].sum()
    print(f"Extracted transactions: {len(transactions):,}")
    print(f"Total income/deposits: {total_income:,.2f}")
    print(f"Total expenses/withdrawals: {total_expenses:,.2f}")
    for name, path in outputs.items():
        print(f"{name}: {path}")


if __name__ == "__main__":
    main()

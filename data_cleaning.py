"""
=============================================================================
 Bluestock Fintech Internship — Day 2
 File   : data_cleaning.py
 Purpose: Clean nav_history, investor_transactions, and scheme_performance;
          validate data quality; save cleaned CSVs to data/processed/.
=============================================================================
"""

import os
import warnings
import pandas as pd
import numpy as np
from datetime import datetime

warnings.filterwarnings("ignore")

RAW_DIR       = os.path.join("data", "raw")
PROCESSED_DIR = os.path.join("data", "processed")
os.makedirs(PROCESSED_DIR, exist_ok=True)

SEP = "=" * 72

# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _banner(msg: str) -> None:
    print(f"\n{SEP}\n  {msg}\n{SEP}")


def _section(msg: str) -> None:
    print(f"\n{'─'*60}\n  {msg}\n{'─'*60}")


def _save(df: pd.DataFrame, filename: str) -> str:
    path = os.path.join(PROCESSED_DIR, filename)
    df.to_csv(path, index=False)
    print(f"  💾  Saved → {path}  ({len(df):,} rows)")
    return path


def _quality_report(label: str, before: int, after: int, issues: list[str]) -> None:
    print(f"\n  Quality Report — {label}")
    print(f"    Rows before : {before:>8,}")
    print(f"    Rows after  : {after:>8,}")
    print(f"    Dropped     : {before - after:>8,}")
    for issue in issues:
        print(f"    {issue}")


# ─────────────────────────────────────────────────────────────────────────────
# 1. Clean nav_history.csv
# ─────────────────────────────────────────────────────────────────────────────

def clean_nav_history() -> pd.DataFrame:
    _section("Task 2.1 — Clean nav_history.csv")

    path = os.path.join(RAW_DIR, "nav_history.csv")
    if not os.path.exists(path):
        print(f"  ✖  {path} not found — skipping.")
        return pd.DataFrame()

    df = pd.read_csv(path)
    before = len(df)
    issues: list[str] = []

    # Parse dates
    for col in ["date", "nav_date"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], infer_datetime_format=True, errors="coerce")
            nat_count = df[col].isna().sum()
            if nat_count:
                issues.append(f"⚠  {nat_count} unparseable date(s) in '{col}' → set NaT")
            df.rename(columns={col: "nav_date"}, inplace=True, errors="ignore")
            break

    date_col = "nav_date" if "nav_date" in df.columns else df.columns[0]

    # Sort
    sort_cols = [c for c in ["amfi_code", date_col] if c in df.columns]
    if sort_cols:
        df.sort_values(sort_cols, inplace=True)
        df.reset_index(drop=True, inplace=True)

    # Remove duplicates
    dup_key = sort_cols if sort_cols else None
    dup_count = df.duplicated(subset=dup_key).sum()
    if dup_count:
        issues.append(f"⚠  Removed {dup_count} duplicate row(s)")
        df.drop_duplicates(subset=dup_key, inplace=True)

    # Validate NAV > 0
    if "nav" in df.columns or "nav_value" in df.columns:
        nav_col = "nav_value" if "nav_value" in df.columns else "nav"
        df[nav_col] = pd.to_numeric(df[nav_col], errors="coerce")
        invalid_nav = (df[nav_col] <= 0) | df[nav_col].isna()
        if invalid_nav.sum():
            issues.append(f"⚠  {invalid_nav.sum()} invalid NAV rows (≤ 0 or NaN) — dropped")
            df = df[~invalid_nav]

    # Forward-fill missing NAV for weekends/holidays (within each fund)
    if "amfi_code" in df.columns and date_col in df.columns:
        nav_col = "nav_value" if "nav_value" in df.columns else "nav"
        if nav_col in df.columns:
            # Reindex to daily calendar per fund
            all_dfs = []
            for code, grp in df.groupby("amfi_code"):
                grp = grp.set_index(date_col).sort_index()
                full_idx = pd.date_range(grp.index.min(), grp.index.max(), freq="D")
                grp = grp.reindex(full_idx)
                grp[nav_col] = grp[nav_col].ffill()
                grp.index.name = date_col
                grp.reset_index(inplace=True)
                all_dfs.append(grp)
            df = pd.concat(all_dfs, ignore_index=True)
            issues.append("✔  Forward-filled NAV for weekends/holidays (per fund)")

    _quality_report("nav_history", before, len(df), issues)
    _save(df, "nav_history_clean.csv")
    return df


# ─────────────────────────────────────────────────────────────────────────────
# 2. Clean investor_transactions.csv
# ─────────────────────────────────────────────────────────────────────────────

VALID_TXN_TYPES = {"SIP", "LUMPSUM", "REDEMPTION"}
TXN_TYPE_MAP    = {
    "sip"        : "SIP",
    "systematic" : "SIP",
    "lump sum"   : "LUMPSUM",
    "lumpsum"    : "LUMPSUM",
    "one time"   : "LUMPSUM",
    "onetime"    : "LUMPSUM",
    "redemption" : "REDEMPTION",
    "redeem"     : "REDEMPTION",
    "withdrawal" : "REDEMPTION",
}

KYC_VALID = {"VERIFIED", "PENDING", "REJECTED", "NOT_SUBMITTED"}


def clean_investor_transactions() -> pd.DataFrame:
    _section("Task 2.2 — Clean investor_transactions.csv")

    path = os.path.join(RAW_DIR, "investor_transactions.csv")
    if not os.path.exists(path):
        print(f"  ✖  {path} not found — skipping.")
        return pd.DataFrame()

    df = pd.read_csv(path)
    before = len(df)
    issues: list[str] = []

    # Standardise transaction_type
    if "transaction_type" in df.columns:
        original = df["transaction_type"].copy()
        df["transaction_type"] = (
            df["transaction_type"]
            .str.strip()
            .str.upper()
        )
        # map non-standard values
        df["transaction_type"] = df["transaction_type"].apply(
            lambda x: TXN_TYPE_MAP.get(x.lower() if isinstance(x, str) else x, x)
        )
        unknown = ~df["transaction_type"].isin(VALID_TXN_TYPES)
        if unknown.sum():
            issues.append(f"⚠  {unknown.sum()} unrecognised transaction_type(s) → flagged as 'UNKNOWN'")
            df.loc[unknown, "transaction_type"] = "UNKNOWN"
        changed = (original.str.upper() != df["transaction_type"]).sum()
        if changed:
            issues.append(f"✔  Standardised {changed} transaction_type value(s)")

    # Validate amount > 0
    if "amount" in df.columns:
        df["amount"] = pd.to_numeric(df["amount"], errors="coerce")
        bad_amt = (df["amount"] <= 0) | df["amount"].isna()
        if bad_amt.sum():
            issues.append(f"⚠  {bad_amt.sum()} rows with amount ≤ 0 or NaN — dropped")
            df = df[~bad_amt]

    # Fix date formats
    for col in ["transaction_date", "date"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], infer_datetime_format=True, errors="coerce")
            nat_c = df[col].isna().sum()
            if nat_c:
                issues.append(f"⚠  {nat_c} unparseable date(s) in '{col}'")

    # Validate KYC status enum
    if "kyc_status" in df.columns:
        df["kyc_status"] = df["kyc_status"].str.strip().str.upper()
        invalid_kyc = ~df["kyc_status"].isin(KYC_VALID)
        if invalid_kyc.sum():
            issues.append(f"⚠  {invalid_kyc.sum()} invalid kyc_status value(s) → set 'NOT_SUBMITTED'")
            df.loc[invalid_kyc, "kyc_status"] = "NOT_SUBMITTED"

    # Remove duplicates
    dup_count = df.duplicated().sum()
    if dup_count:
        issues.append(f"⚠  Removed {dup_count} duplicate row(s)")
        df.drop_duplicates(inplace=True)

    _quality_report("investor_transactions", before, len(df), issues)
    _save(df, "investor_transactions_clean.csv")
    return df


# ─────────────────────────────────────────────────────────────────────────────
# 3. Clean scheme_performance.csv
# ─────────────────────────────────────────────────────────────────────────────

RETURN_COLS   = ["return_1yr", "return_3yr", "return_5yr", "ytd_return",
                 "absolute_return", "cagr", "alpha", "beta", "sharpe_ratio"]
EXPENSE_RANGE = (0.1, 2.5)


def clean_scheme_performance() -> pd.DataFrame:
    _section("Task 2.3 — Clean scheme_performance.csv")

    path = os.path.join(RAW_DIR, "scheme_performance.csv")
    if not os.path.exists(path):
        print(f"  ✖  {path} not found — skipping.")
        return pd.DataFrame()

    df = pd.read_csv(path)
    before = len(df)
    issues: list[str] = []

    # Validate return columns are numeric
    existing_return_cols = [c for c in RETURN_COLS if c in df.columns]
    for col in existing_return_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")
        non_numeric = df[col].isna().sum()
        if non_numeric:
            issues.append(f"⚠  '{col}' : {non_numeric} non-numeric value(s) coerced to NaN")

    # Flag anomalous returns (> 200 % or < -100 % — likely data errors)
    for col in existing_return_cols:
        if col in df.columns:
            anomalies = (df[col] > 200) | (df[col] < -100)
            if anomalies.sum():
                issues.append(f"⚠  '{col}' : {anomalies.sum()} value(s) outside [-100, 200] % — flagged")
                df[f"{col}_anomaly_flag"] = anomalies.astype(int)

    # Validate expense_ratio
    if "expense_ratio" in df.columns:
        df["expense_ratio"] = pd.to_numeric(df["expense_ratio"], errors="coerce")
        out_rng = (df["expense_ratio"] < EXPENSE_RANGE[0]) | (df["expense_ratio"] > EXPENSE_RANGE[1])
        out_rng &= df["expense_ratio"].notna()
        if out_rng.sum():
            issues.append(f"⚠  {out_rng.sum()} expense_ratio value(s) outside [{EXPENSE_RANGE[0]} – {EXPENSE_RANGE[1]}]%")
            df["expense_ratio_flag"] = out_rng.astype(int)

    # Remove duplicates
    dup_count = df.duplicated().sum()
    if dup_count:
        issues.append(f"⚠  Removed {dup_count} duplicate row(s)")
        df.drop_duplicates(inplace=True)

    _quality_report("scheme_performance", before, len(df), issues)
    _save(df, "scheme_performance_clean.csv")
    return df


# ─────────────────────────────────────────────────────────────────────────────
# Generic cleaner for remaining 7 CSVs
# ─────────────────────────────────────────────────────────────────────────────

OTHER_FILES = {
    "fund_master"      : "fund_master_clean.csv",
    "aum_data"         : "aum_data_clean.csv",
    "sip_data"         : "sip_data_clean.csv",
    "risk_metrics"     : "risk_metrics_clean.csv",
    "benchmark_data"   : "benchmark_data_clean.csv",
    "distributor_data" : "distributor_data_clean.csv",
    "state_wise_data"  : "state_wise_data_clean.csv",
}


def clean_generic(base_name: str, out_name: str) -> pd.DataFrame:
    _section(f"Generic clean — {base_name}.csv")

    path = os.path.join(RAW_DIR, f"{base_name}.csv")
    if not os.path.exists(path):
        print(f"  ✖  {path} not found — skipping.")
        return pd.DataFrame()

    df = pd.read_csv(path)
    before = len(df)
    issues: list[str] = []

    # Parse obvious date columns
    for col in df.select_dtypes(include="object").columns:
        if "date" in col.lower():
            converted = pd.to_datetime(df[col], infer_datetime_format=True, errors="coerce")
            if converted.notna().sum() > 0:
                df[col] = converted

    # Strip whitespace from string columns
    str_cols = df.select_dtypes(include="object").columns.tolist()
    for col in str_cols:
        df[col] = df[col].str.strip()

    # Remove duplicates
    dup_count = df.duplicated().sum()
    if dup_count:
        issues.append(f"⚠  Removed {dup_count} duplicate row(s)")
        df.drop_duplicates(inplace=True)

    if not issues:
        issues.append("✔  No critical issues found")

    _quality_report(base_name, before, len(df), issues)
    _save(df, out_name)
    return df


# ─────────────────────────────────────────────────────────────────────────────
# AMFI Code Validation  (Task 2.7)
# ─────────────────────────────────────────────────────────────────────────────

def validate_amfi_codes() -> None:
    _section("Task 2.7 — AMFI Code Validation")

    fm_path  = os.path.join(PROCESSED_DIR, "fund_master_clean.csv")
    nav_path = os.path.join(PROCESSED_DIR, "nav_history_clean.csv")

    if not os.path.exists(fm_path) or not os.path.exists(nav_path):
        print("  ✖  Cleaned files missing — run cleaning steps first.")
        return

    fund_master  = pd.read_csv(fm_path)
    nav_history  = pd.read_csv(nav_path)

    fm_col  = next((c for c in fund_master.columns  if "amfi" in c.lower()), None)
    nav_col = next((c for c in nav_history.columns  if "amfi" in c.lower()), None)

    if not fm_col or not nav_col:
        print("  ⚠  Could not identify AMFI code columns — skipping.")
        return

    fm_codes  = set(fund_master[fm_col].dropna().astype(str))
    nav_codes = set(nav_history[nav_col].dropna().astype(str))

    in_both   = fm_codes & nav_codes
    only_fm   = fm_codes - nav_codes
    only_nav  = nav_codes - fm_codes

    print(f"\n  AMFI codes in fund_master              : {len(fm_codes):>6,}")
    print(f"  AMFI codes in nav_history              : {len(nav_codes):>6,}")
    print(f"  Codes present in BOTH                  : {len(in_both):>6,}")
    print(f"  Codes ONLY in fund_master (no NAV)     : {len(only_fm):>6,}")
    print(f"  Codes ONLY in nav_history (no master)  : {len(only_nav):>6,}")

    if only_fm:
        print(f"\n  ⚠  Orphaned fund_master codes (sample): {list(only_fm)[:10]}")
    if only_nav:
        print(f"\n  ⚠  Orphaned nav_history codes (sample): {list(only_nav)[:10]}")
    if not only_fm and not only_nav:
        print("\n  ✔  All AMFI codes match perfectly between fund_master and nav_history.")

    # Write quality summary
    summary_path = os.path.join("reports", "data_quality_summary.md")
    os.makedirs("reports", exist_ok=True)
    with open(summary_path, "w") as f:
        f.write("# Data Quality Summary — Day 2\n\n")
        f.write(f"Generated : {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n")
        f.write("## AMFI Code Cross-Validation\n\n")
        f.write(f"| Metric | Count |\n|---|---|\n")
        f.write(f"| Codes in fund_master | {len(fm_codes):,} |\n")
        f.write(f"| Codes in nav_history | {len(nav_codes):,} |\n")
        f.write(f"| Matched codes | {len(in_both):,} |\n")
        f.write(f"| Unmatched in fund_master | {len(only_fm):,} |\n")
        f.write(f"| Unmatched in nav_history | {len(only_nav):,} |\n\n")
        if only_fm:
            f.write(f"### Orphaned fund_master codes\n\n```\n{sorted(only_fm)}\n```\n\n")
        if only_nav:
            f.write(f"### Orphaned nav_history codes\n\n```\n{sorted(only_nav)}\n```\n\n")
    print(f"\n  📄  Quality summary saved → {summary_path}")


# ─────────────────────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────────────────────

def main() -> None:
    _banner("Bluestock Fintech — Day 2: Data Cleaning Pipeline")

    clean_nav_history()
    clean_investor_transactions()
    clean_scheme_performance()

    for base, out in OTHER_FILES.items():
        clean_generic(base, out)

    validate_amfi_codes()

    _banner("Cleaning Complete")
    cleaned = [f for f in os.listdir(PROCESSED_DIR) if f.endswith(".csv")]
    print(f"  Cleaned CSVs in {PROCESSED_DIR}/ : {len(cleaned)}")
    for f in sorted(cleaned):
        path = os.path.join(PROCESSED_DIR, f)
        rows = sum(1 for _ in open(path)) - 1
        print(f"    • {f:<45} {rows:>8,} rows")


if __name__ == "__main__":
    main()
    print("\n  ✔  data_cleaning.py finished successfully.\n")

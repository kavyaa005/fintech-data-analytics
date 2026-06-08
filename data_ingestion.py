"""
=============================================================================
 Bluestock Fintech Internship — Day 1
 File   : data_ingestion.py
 Purpose: Load all 10 CSV datasets, print diagnostics, note anomalies.
=============================================================================
"""

import os
import sys
import textwrap
import pandas as pd

# ── Paths ─────────────────────────────────────────────────────────────────────
RAW_DIR = os.path.join("data", "raw")

# ── Dataset catalogue ─────────────────────────────────────────────────────────
DATASETS = {
    "fund_master"           : "fund_master.csv",
    "nav_history"           : "nav_history.csv",
    "investor_transactions" : "investor_transactions.csv",
    "scheme_performance"    : "scheme_performance.csv",
    "aum_data"              : "aum_data.csv",
    "sip_data"              : "sip_data.csv",
    "risk_metrics"          : "risk_metrics.csv",
    "benchmark_data"        : "benchmark_data.csv",
    "distributor_data"      : "distributor_data.csv",
    "state_wise_data"       : "state_wise_data.csv",
}

# ── Helpers ───────────────────────────────────────────────────────────────────
SEP = "=" * 72

def _banner(title: str) -> None:
    print(f"\n{SEP}")
    print(f"  {title}")
    print(SEP)


def _section(label: str) -> None:
    print(f"\n{'─' * 60}")
    print(f"  {label}")
    print('─' * 60)


def _anomaly_check(name: str, df: pd.DataFrame) -> list[str]:
    """Return a list of anomaly notes for the given DataFrame."""
    notes: list[str] = []

    # Nulls
    null_cols = df.columns[df.isnull().any()].tolist()
    if null_cols:
        null_summary = ", ".join(
            f"{c}({df[c].isnull().sum()})" for c in null_cols
        )
        notes.append(f"⚠  Nulls found → {null_summary}")

    # Duplicated rows
    dup_count = df.duplicated().sum()
    if dup_count:
        notes.append(f"⚠  {dup_count} duplicate row(s) detected")

    # Dataset-specific checks
    if "nav" in df.columns:
        neg_nav = (df["nav"] <= 0).sum()
        if neg_nav:
            notes.append(f"⚠  {neg_nav} row(s) with NAV ≤ 0")

    if "amount" in df.columns:
        neg_amt = (df["amount"] <= 0).sum()
        if neg_amt:
            notes.append(f"⚠  {neg_amt} row(s) with amount ≤ 0")

    if "expense_ratio" in df.columns:
        out_of_range = ((df["expense_ratio"] < 0.1) | (df["expense_ratio"] > 2.5)).sum()
        if out_of_range:
            notes.append(f"⚠  {out_of_range} expense_ratio value(s) outside [0.1 – 2.5]%")

    if not notes:
        notes.append("✔  No anomalies detected")

    return notes


# ── Main ingestion loop ───────────────────────────────────────────────────────
def ingest_all() -> dict[str, pd.DataFrame]:
    _banner("Bluestock Fintech — Day 1: Data Ingestion")
    loaded: dict[str, pd.DataFrame] = {}

    for alias, filename in DATASETS.items():
        filepath = os.path.join(RAW_DIR, filename)
        _section(f"Dataset : {alias}  [{filename}]")

        if not os.path.exists(filepath):
            print(f"  ✖  File not found: {filepath}  (skipping)")
            continue

        df = pd.read_csv(filepath)
        loaded[alias] = df

        # --- shape ---
        print(f"\n  Shape   : {df.shape[0]} rows × {df.shape[1]} columns")

        # --- dtypes ---
        print("\n  dtypes  :")
        dtype_str = df.dtypes.to_string()
        for line in dtype_str.splitlines():
            print(f"    {line}")

        # --- head ---
        print("\n  head(3) :")
        head_str = df.head(3).to_string(index=False)
        for line in head_str.splitlines():
            print(f"    {line}")

        # --- anomalies ---
        print("\n  Anomaly check :")
        for note in _anomaly_check(alias, df):
            print(f"    {note}")

    _banner("Ingestion Summary")
    print(f"  Datasets loaded   : {len(loaded)} / {len(DATASETS)}")
    for alias, df in loaded.items():
        print(f"    • {alias:<28} {df.shape[0]:>8,} rows  {df.shape[1]:>3} cols")

    return loaded


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    dataframes = ingest_all()
    print("\n  ✔  data_ingestion.py finished successfully.\n")

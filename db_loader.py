"""
=============================================================================
 Bluestock Fintech Internship — Day 2
 File   : db_loader.py
 Purpose: Design SQLite star schema, create tables, load all cleaned CSVs.
=============================================================================
"""

import os
import pandas as pd
from sqlalchemy import create_engine, text

PROCESSED_DIR = os.path.join("data", "processed")
DB_PATH       = "bluestock_mf.db"
SQL_DIR       = "sql"
os.makedirs(SQL_DIR, exist_ok=True)

SEP = "=" * 72


# ─────────────────────────────────────────────────────────────────────────────
# Star Schema DDL
# ─────────────────────────────────────────────────────────────────────────────

SCHEMA_SQL = """
-- ============================================================
--  Bluestock MF Analytics — Star Schema DDL
--  Database : bluestock_mf.db (SQLite)
-- ============================================================

PRAGMA foreign_keys = ON;

-- ────────────────────────────────────────────
-- DIMENSION: dim_fund
-- ────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS dim_fund (
    amfi_code          INTEGER  PRIMARY KEY,
    scheme_name        TEXT     NOT NULL,
    fund_house         TEXT,
    scheme_type        TEXT,         -- Open-Ended / Close-Ended
    scheme_category    TEXT,         -- Equity / Debt / Hybrid ...
    scheme_sub_category TEXT,
    risk_grade         TEXT,         -- Low / Moderate / High / Very High
    benchmark_index    TEXT,
    launch_date        DATE,
    is_direct          INTEGER  DEFAULT 1   -- 1 = Direct, 0 = Regular
);

-- ────────────────────────────────────────────
-- DIMENSION: dim_date
-- ────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS dim_date (
    date_id      INTEGER  PRIMARY KEY,   -- YYYYMMDD integer key
    full_date    DATE     NOT NULL UNIQUE,
    day          INTEGER,
    month        INTEGER,
    month_name   TEXT,
    quarter      INTEGER,
    year         INTEGER,
    day_of_week  TEXT,
    is_weekday   INTEGER DEFAULT 1       -- 1 = weekday, 0 = weekend
);

-- ────────────────────────────────────────────
-- FACT: fact_nav
-- ────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS fact_nav (
    nav_id      INTEGER  PRIMARY KEY AUTOINCREMENT,
    amfi_code   INTEGER  NOT NULL,
    date_id     INTEGER  NOT NULL,
    nav_value   REAL     NOT NULL CHECK (nav_value > 0),
    FOREIGN KEY (amfi_code) REFERENCES dim_fund(amfi_code),
    FOREIGN KEY (date_id)   REFERENCES dim_date(date_id)
);

CREATE INDEX IF NOT EXISTS idx_fact_nav_amfi   ON fact_nav(amfi_code);
CREATE INDEX IF NOT EXISTS idx_fact_nav_date   ON fact_nav(date_id);

-- ────────────────────────────────────────────
-- FACT: fact_transactions
-- ────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS fact_transactions (
    txn_id           INTEGER PRIMARY KEY AUTOINCREMENT,
    investor_id      TEXT,
    amfi_code        INTEGER NOT NULL,
    date_id          INTEGER NOT NULL,
    transaction_type TEXT    NOT NULL CHECK (transaction_type IN ('SIP','LUMPSUM','REDEMPTION','UNKNOWN')),
    amount           REAL    NOT NULL CHECK (amount > 0),
    units            REAL,
    nav_at_txn       REAL,
    state            TEXT,
    kyc_status       TEXT,
    FOREIGN KEY (amfi_code) REFERENCES dim_fund(amfi_code),
    FOREIGN KEY (date_id)   REFERENCES dim_date(date_id)
);

CREATE INDEX IF NOT EXISTS idx_fact_txn_amfi ON fact_transactions(amfi_code);
CREATE INDEX IF NOT EXISTS idx_fact_txn_date ON fact_transactions(date_id);
CREATE INDEX IF NOT EXISTS idx_fact_txn_type ON fact_transactions(transaction_type);

-- ────────────────────────────────────────────
-- FACT: fact_performance
-- ────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS fact_performance (
    perf_id        INTEGER PRIMARY KEY AUTOINCREMENT,
    amfi_code      INTEGER NOT NULL,
    as_of_date_id  INTEGER,
    return_1yr     REAL,
    return_3yr     REAL,
    return_5yr     REAL,
    ytd_return     REAL,
    alpha          REAL,
    beta           REAL,
    sharpe_ratio   REAL,
    expense_ratio  REAL,
    FOREIGN KEY (amfi_code)     REFERENCES dim_fund(amfi_code),
    FOREIGN KEY (as_of_date_id) REFERENCES dim_date(date_id)
);

-- ────────────────────────────────────────────
-- FACT: fact_aum
-- ────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS fact_aum (
    aum_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    amfi_code  INTEGER NOT NULL,
    date_id    INTEGER NOT NULL,
    aum_crores REAL    NOT NULL CHECK (aum_crores >= 0),
    FOREIGN KEY (amfi_code) REFERENCES dim_fund(amfi_code),
    FOREIGN KEY (date_id)   REFERENCES dim_date(date_id)
);

CREATE INDEX IF NOT EXISTS idx_fact_aum_amfi ON fact_aum(amfi_code);
CREATE INDEX IF NOT EXISTS idx_fact_aum_date ON fact_aum(date_id);
"""


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _banner(msg: str) -> None:
    print(f"\n{SEP}\n  {msg}\n{SEP}")


def _section(msg: str) -> None:
    print(f"\n{'─'*60}\n  {msg}\n{'─'*60}")


def _safe_load(engine, df: pd.DataFrame, table: str, if_exists: str = "append") -> int:
    """Load DataFrame to SQLite; return rows inserted."""
    if df.empty:
        print(f"  ⚠  {table}: empty DataFrame, nothing loaded")
        return 0
    df.to_sql(table, engine, if_exists=if_exists, index=False, chunksize=5000)
    with engine.connect() as conn:
        count = conn.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
    return count


def _load_csv(name: str) -> pd.DataFrame:
    path = os.path.join(PROCESSED_DIR, name)
    if not os.path.exists(path):
        print(f"  ⚠  {path} not found")
        return pd.DataFrame()
    return pd.read_csv(path)


# ─────────────────────────────────────────────────────────────────────────────
# Date dimension builder
# ─────────────────────────────────────────────────────────────────────────────

def build_dim_date(engine) -> None:
    _section("Building dim_date")
    dates = pd.date_range("2015-01-01", "2026-12-31", freq="D")
    dim = pd.DataFrame({
        "date_id"    : dates.strftime("%Y%m%d").astype(int),
        "full_date"  : dates.strftime("%Y-%m-%d"),
        "day"        : dates.day,
        "month"      : dates.month,
        "month_name" : dates.strftime("%B"),
        "quarter"    : dates.quarter,
        "year"       : dates.year,
        "day_of_week": dates.strftime("%A"),
        "is_weekday" : (dates.dayofweek < 5).astype(int),
    })
    rows = _safe_load(engine, dim, "dim_date", if_exists="replace")
    print(f"  ✔  dim_date : {rows:,} rows loaded")


# ─────────────────────────────────────────────────────────────────────────────
# Load dim_fund
# ─────────────────────────────────────────────────────────────────────────────

def load_dim_fund(engine) -> None:
    _section("Loading dim_fund")
    df = _load_csv("fund_master_clean.csv")
    if df.empty:
        return
    col_map = {
        "amfi_code"          : "amfi_code",
        "scheme_name"        : "scheme_name",
        "fund_house"         : "fund_house",
        "scheme_type"        : "scheme_type",
        "scheme_category"    : "scheme_category",
        "scheme_sub_category": "scheme_sub_category",
        "risk_grade"         : "risk_grade",
        "benchmark_index"    : "benchmark_index",
        "launch_date"        : "launch_date",
    }
    existing = {c: col_map[c] for c in col_map if c in df.columns}
    df = df[list(existing.keys())].rename(columns=existing).drop_duplicates(subset=["amfi_code"])
    rows = _safe_load(engine, df, "dim_fund", if_exists="replace")
    print(f"  ✔  dim_fund : {rows:,} rows loaded")


# ─────────────────────────────────────────────────────────────────────────────
# Load fact_nav
# ─────────────────────────────────────────────────────────────────────────────

def load_fact_nav(engine) -> None:
    _section("Loading fact_nav")
    df = _load_csv("nav_history_clean.csv")
    if df.empty:
        return

    date_col = next((c for c in df.columns if "date" in c.lower()), None)
    nav_col  = next((c for c in df.columns if "nav" in c.lower()), None)
    amfi_col = next((c for c in df.columns if "amfi" in c.lower()), None)

    if not all([date_col, nav_col, amfi_col]):
        print("  ⚠  Could not identify required columns in nav_history")
        return

    df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
    df["date_id"] = df[date_col].dt.strftime("%Y%m%d").astype("Int64")
    fact = pd.DataFrame({
        "amfi_code" : df[amfi_col],
        "date_id"   : df["date_id"],
        "nav_value" : pd.to_numeric(df[nav_col], errors="coerce"),
    }).dropna()
    rows = _safe_load(engine, fact, "fact_nav", if_exists="replace")
    print(f"  ✔  fact_nav : {rows:,} rows loaded")


# ─────────────────────────────────────────────────────────────────────────────
# Load fact_transactions
# ─────────────────────────────────────────────────────────────────────────────

def load_fact_transactions(engine) -> None:
    _section("Loading fact_transactions")
    df = _load_csv("investor_transactions_clean.csv")
    if df.empty:
        return

    date_col = next((c for c in df.columns if "date" in c.lower()), None)
    if date_col:
        df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
        df["date_id"] = df[date_col].dt.strftime("%Y%m%d").astype("Int64")
    else:
        df["date_id"] = None

    keep = {
        "investor_id", "amfi_code", "date_id", "transaction_type",
        "amount", "units", "nav_at_txn", "state", "kyc_status"
    }
    fact = df[[c for c in keep if c in df.columns]]
    rows = _safe_load(engine, fact, "fact_transactions", if_exists="replace")
    print(f"  ✔  fact_transactions : {rows:,} rows loaded")


# ─────────────────────────────────────────────────────────────────────────────
# Load fact_performance
# ─────────────────────────────────────────────────────────────────────────────

def load_fact_performance(engine) -> None:
    _section("Loading fact_performance")
    df = _load_csv("scheme_performance_clean.csv")
    if df.empty:
        return

    keep = {
        "amfi_code", "as_of_date_id", "return_1yr", "return_3yr",
        "return_5yr", "ytd_return", "alpha", "beta",
        "sharpe_ratio", "expense_ratio"
    }
    fact = df[[c for c in keep if c in df.columns]]
    rows = _safe_load(engine, fact, "fact_performance", if_exists="replace")
    print(f"  ✔  fact_performance : {rows:,} rows loaded")


# ─────────────────────────────────────────────────────────────────────────────
# Load fact_aum
# ─────────────────────────────────────────────────────────────────────────────

def load_fact_aum(engine) -> None:
    _section("Loading fact_aum")
    df = _load_csv("aum_data_clean.csv")
    if df.empty:
        return

    date_col = next((c for c in df.columns if "date" in c.lower()), None)
    if date_col:
        df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
        df["date_id"] = df[date_col].dt.strftime("%Y%m%d").astype("Int64")
    else:
        df["date_id"] = None

    amfi_col = next((c for c in df.columns if "amfi" in c.lower()), None)
    aum_col  = next((c for c in df.columns if "aum" in c.lower()), None)

    if not amfi_col or not aum_col:
        print("  ⚠  amfi_code or aum column missing")
        return

    fact = pd.DataFrame({
        "amfi_code"  : df[amfi_col],
        "date_id"    : df["date_id"],
        "aum_crores" : pd.to_numeric(df[aum_col], errors="coerce"),
    }).dropna()
    rows = _safe_load(engine, fact, "fact_aum", if_exists="replace")
    print(f"  ✔  fact_aum : {rows:,} rows loaded")


# ─────────────────────────────────────────────────────────────────────────────
# Verify row counts
# ─────────────────────────────────────────────────────────────────────────────

def verify_counts(engine) -> None:
    _section("Row Count Verification")
    tables = ["dim_fund", "dim_date", "fact_nav",
              "fact_transactions", "fact_performance", "fact_aum"]
    with engine.connect() as conn:
        for t in tables:
            try:
                n = conn.execute(text(f"SELECT COUNT(*) FROM {t}")).scalar()
                print(f"  {t:<25} : {n:>10,} rows  ✔")
            except Exception as exc:
                print(f"  {t:<25} : ERROR — {exc}")


# ─────────────────────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────────────────────

def main() -> None:
    _banner("Bluestock Fintech — Day 2: SQLite Star Schema Loader")

    # 1. Write schema.sql
    schema_path = os.path.join(SQL_DIR, "schema.sql")
    with open(schema_path, "w") as f:
        f.write(SCHEMA_SQL)
    print(f"  📄  Schema written to {schema_path}")

    # 2. Create engine & tables
    engine = create_engine(f"sqlite:///{DB_PATH}", echo=False)
    with engine.connect() as conn:
        for stmt in SCHEMA_SQL.strip().split(";"):
            stmt = stmt.strip()
            if stmt:
                try:
                    conn.execute(text(stmt))
                except Exception:
                    pass
        conn.commit()
    print(f"  ✔  Database : {DB_PATH}")

    # 3. Load data
    build_dim_date(engine)
    load_dim_fund(engine)
    load_fact_nav(engine)
    load_fact_transactions(engine)
    load_fact_performance(engine)
    load_fact_aum(engine)

    # 4. Verify
    verify_counts(engine)

    _banner("db_loader.py complete")
    print(f"  Database saved at : {DB_PATH}\n")


if __name__ == "__main__":
    main()

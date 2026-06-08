# 📊 Bluestock Fintech — Mutual Fund Data Analytics

> Internship project: End-to-end data analytics platform for Indian mutual fund data using Python, SQLite, and Pandas.

[![Python](https://img.shields.io/badge/Python-3.11+-blue?logo=python)](https://python.org)
[![SQLite](https://img.shields.io/badge/Database-SQLite-green?logo=sqlite)](https://sqlite.org)
[![Pandas](https://img.shields.io/badge/Pandas-2.x-150458?logo=pandas)](https://pandas.pydata.org)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

---

## 🗂️ Project Structure

```
fintech-data-analytics/
├── data/
│   ├── raw/                    # Original CSVs + live API data
│   └── processed/              # Cleaned, validated CSVs (10 files)
├── notebooks/                  # Exploratory Jupyter notebooks
├── scripts/
│   ├── data_ingestion.py       # Day 1: Load & inspect all 10 CSVs
│   ├── live_nav_fetch.py       # Day 1: Fetch live NAV from mfapi.in
│   ├── data_cleaning.py        # Day 2: Clean & validate datasets
│   └── db_loader.py            # Day 2: Build SQLite star schema
├── sql/
│   ├── schema.sql              # CREATE TABLE DDL (star schema)
│   └── queries.sql             # 10 analytical SQL queries
├── dashboard/                  # Plotly/Dash visualisations
├── reports/
│   └── data_quality_summary.md # Automated data quality report
├── bluestock_mf.db             # SQLite database
├── data_dictionary.md          # Column definitions & business logic
├── requirements.txt
└── README.md
```

---

## 🚀 Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/kavyaa005/fintech-data-analytics.git
cd fintech-data-analytics

# 2. Create a virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Place raw CSVs in data/raw/

# 5. Run Day 1 pipeline
python scripts/data_ingestion.py
python scripts/live_nav_fetch.py

# 6. Run Day 2 pipeline
python scripts/data_cleaning.py
python scripts/db_loader.py
```

---

## 📅 Day 1 — Data Ingestion

### Tasks Completed
- ✅ Created project folder structure (`data/raw`, `data/processed`, `notebooks/`, `sql/`, `dashboard/`, `reports/`)
- ✅ Installed all dependencies and generated `requirements.txt`
- ✅ Loaded all 10 CSV datasets — printed `.shape`, `.dtypes`, `.head()`, anomaly notes
- ✅ Fetched live NAV from [mfapi.in](https://api.mfapi.in) for HDFC Top 100 Direct (code: 125497)
- ✅ Fetched NAV for 5 additional key large-cap schemes:

| AMFI Code | Scheme |
|---|---|
| 119551 | SBI Bluechip Direct Growth |
| 120503 | ICICI Prudential Bluechip Direct Growth |
| 118632 | Nippon India Large Cap Direct Growth |
| 119092 | Axis Bluechip Direct Growth |
| 120841 | Kotak Bluechip Direct Growth |

- ✅ Explored `fund_master` — printed unique fund houses, categories, sub-categories, risk grades
- ✅ Validated AMFI codes: confirmed cross-presence in `fund_master` and `nav_history`
- ✅ Git commit: `"Day 1: Data ingestion complete"`

### Deliverables
| File | Description |
|---|---|
| `scripts/data_ingestion.py` | Loads all 10 CSVs with shape/dtype/head/anomaly output |
| `scripts/live_nav_fetch.py` | Fetches live NAV for 6 schemes from mfapi.in |
| `requirements.txt` | All Python dependencies with pinned versions |
| `data/raw/nav_all_schemes.csv` | Consolidated NAV file for all 6 fetched schemes |

---

## 📅 Day 2 — Data Cleaning & Database

### Tasks Completed
- ✅ **Cleaned `nav_history.csv`**: parsed dates, sorted by `amfi_code + date`, forward-filled holiday/weekend NAV gaps, removed duplicates, validated `nav > 0`
- ✅ **Cleaned `investor_transactions.csv`**: standardised `transaction_type` (SIP/LUMPSUM/REDEMPTION), validated `amount > 0`, fixed date formats, validated KYC enum values
- ✅ **Cleaned `scheme_performance.csv`**: coerced return columns to numeric, flagged outliers, validated `expense_ratio ∈ [0.1%, 2.5%]`
- ✅ **Designed SQLite star schema**: `dim_fund`, `dim_date`, `fact_nav`, `fact_transactions`, `fact_performance`, `fact_aum`
- ✅ **Loaded all cleaned datasets** into SQLite via SQLAlchemy + `df.to_sql()`
- ✅ **Wrote 10 analytical SQL queries** (see `sql/queries.sql`)
- ✅ **Created `data_dictionary.md`** with column definitions, business logic, enums, and source references
- ✅ Git commit: `"Day 2: Cleaned data + SQLite DB loaded"`

### Star Schema Design

```
                    ┌───────────────┐
                    │   dim_date    │
                    │  (date_id PK) │
                    └───────┬───────┘
                            │
          ┌─────────────────┼──────────────────┐
          │                 │                  │
   ┌──────▼──────┐   ┌──────▼──────┐   ┌──────▼──────┐
   │  fact_nav   │   │fact_txn     │   │ fact_aum    │
   │  fact_perf  │   └─────────────┘   └─────────────┘
   └──────┬──────┘
          │
   ┌──────▼──────┐
   │  dim_fund   │
   │(amfi_code PK│
   └─────────────┘
```

### SQL Queries Implemented

| # | Query |
|---|---|
| 1 | Top 5 funds by AUM (most recent month) |
| 2 | Average NAV per month across all funds |
| 3 | SIP transaction YoY growth (count & amount with LAG) |
| 4 | Total transaction amount by investor state |
| 5 | Funds with expense_ratio < 1% |
| 6 | Best performing funds by 3-year CAGR |
| 7 | Monthly NAV trend for top 5 funds by AUM |
| 8 | Transaction breakdown (SIP/Lumpsum/Redemption) per fund house |
| 9 | Funds with Sharpe ratio > 1.0 and positive alpha |
| 10 | KYC compliance rate by state |

### Deliverables
| File | Description |
|---|---|
| `data/processed/` | 10 cleaned CSVs |
| `bluestock_mf.db` | SQLite star schema database |
| `sql/schema.sql` | Full DDL with PK/FK constraints |
| `sql/queries.sql` | 10 production-quality analytical queries |
| `data_dictionary.md` | Complete column/table documentation |
| `reports/data_quality_summary.md` | Auto-generated AMFI code validation report |

---

## 🗃️ Database Schema

```sql
dim_fund           -- Fund master (2,000+ schemes)
dim_date           -- Date dimension (2015–2026)
fact_nav           -- Daily NAV per scheme
fact_transactions  -- Investor buy/sell transactions
fact_performance   -- Risk-return metrics (alpha, beta, Sharpe, returns)
fact_aum           -- Monthly AUM per scheme
```

---

## 📡 Data Sources

| Source | URL | Description |
|---|---|---|
| AMFI mfapi.in | `https://api.mfapi.in/mf/{amfi_code}` | Free live NAV API |
| AMFI India | `https://www.amfiindia.com` | Official fund master & NAV data |
| SEBI | `https://www.sebi.gov.in` | Regulatory framework reference |

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3.11+ |
| Data Processing | Pandas, NumPy |
| Database | SQLite + SQLAlchemy |
| Visualisation | Matplotlib, Seaborn, Plotly |
| API | requests |
| Statistics | SciPy |
| Notebooks | Jupyter Lab |

---

## 👩‍💻 Author

**Kavya** — Data Analytics Intern @ Bluestock Fintech  
GitHub: [@kavyaa005](https://github.com/kavyaa005)

# Data Dictionary — Bluestock Fintech Analytics

> **Project**: Bluestock Fintech Internship — Mutual Fund Analytics Platform  
> **Database**: `bluestock_mf.db` (SQLite)  
> **Schema type**: Star Schema (2 dimensions, 4 fact tables)  
> **Last updated**: Day 2

---

## Table of Contents

1. [Dimension Tables](#dimension-tables)
   - [dim_fund](#dim_fund)
   - [dim_date](#dim_date)
2. [Fact Tables](#fact-tables)
   - [fact_nav](#fact_nav)
   - [fact_transactions](#fact_transactions)
   - [fact_performance](#fact_performance)
   - [fact_aum](#fact_aum)
3. [Source CSV Datasets](#source-csv-datasets)
4. [AMFI Code Structure](#amfi-code-structure)
5. [Enum Reference Values](#enum-reference-values)

---

## Dimension Tables

### `dim_fund`

Stores descriptive master data for every mutual fund scheme. This is the central dimension.

| Column | Data Type | Nullable | Description | Source |
|---|---|---|---|---|
| `amfi_code` | INTEGER | No — **PK** | AMFI (Association of Mutual Funds in India) unique scheme identifier. 6-digit numeric code assigned by AMFI. | `fund_master.csv` |
| `scheme_name` | TEXT | No | Full official scheme name as per AMFI scheme master. E.g., "HDFC Top 100 Direct Growth". | `fund_master.csv` |
| `fund_house` | TEXT | Yes | Asset Management Company (AMC) name. E.g., "HDFC Mutual Fund", "SBI Mutual Fund". | `fund_master.csv` |
| `scheme_type` | TEXT | Yes | Open-ended or Close-ended. Majority of equity funds are Open-Ended. | `fund_master.csv` |
| `scheme_category` | TEXT | Yes | SEBI-defined broad category: Equity, Debt, Hybrid, Solution-Oriented, Other. | `fund_master.csv` |
| `scheme_sub_category` | TEXT | Yes | Detailed SEBI sub-category. E.g., "Large Cap Fund", "Overnight Fund", "Balanced Advantage". | `fund_master.csv` |
| `risk_grade` | TEXT | Yes | SEBI risk-o-meter classification: Low / Low to Moderate / Moderate / Moderately High / High / Very High. | `fund_master.csv` |
| `benchmark_index` | TEXT | Yes | Primary benchmark index. E.g., "NIFTY 100 TRI", "NIFTY 50 TRI". | `fund_master.csv` |
| `launch_date` | DATE | Yes | Scheme NFO (New Fund Offer) launch date. Format: YYYY-MM-DD. | `fund_master.csv` |
| `is_direct` | INTEGER | Yes | Flag: 1 = Direct plan (lower expense ratio), 0 = Regular plan (distributor commission included). | Derived |

---

### `dim_date`

Date dimension covering the full analytics range (2015–2026). Pre-populated with all calendar dates.

| Column | Data Type | Nullable | Description |
|---|---|---|---|
| `date_id` | INTEGER | No — **PK** | Surrogate integer key in YYYYMMDD format. E.g., 20240115 for 15-Jan-2024. Used as FK in all fact tables. |
| `full_date` | DATE | No | ISO date string: YYYY-MM-DD. Unique. |
| `day` | INTEGER | Yes | Day of month (1–31). |
| `month` | INTEGER | Yes | Month number (1–12). |
| `month_name` | TEXT | Yes | Full month name. E.g., "January". |
| `quarter` | INTEGER | Yes | Fiscal/calendar quarter (1–4). |
| `year` | INTEGER | Yes | 4-digit year. |
| `day_of_week` | TEXT | Yes | Day name. E.g., "Monday". |
| `is_weekday` | INTEGER | Yes | 1 = Mon–Fri (trading day), 0 = Sat–Sun. Note: Indian market holidays are NOT excluded here. |

---

## Fact Tables

### `fact_nav`

Daily Net Asset Value (NAV) for each mutual fund scheme. Core pricing fact table.

| Column | Data Type | Nullable | Constraint | Description | Source |
|---|---|---|---|---|---|
| `nav_id` | INTEGER | No — **PK** | AUTOINCREMENT | Surrogate primary key. | Generated |
| `amfi_code` | INTEGER | No | FK → dim_fund | AMFI scheme identifier. | `nav_history.csv` / mfapi.in |
| `date_id` | INTEGER | No | FK → dim_date | Date of NAV publication (YYYYMMDD). | Derived from nav_date |
| `nav_value` | REAL | No | > 0 | NAV in Indian Rupees (₹). For direct growth plans, this represents per-unit value. | `nav_history.csv` / mfapi.in |

**Notes**:
- Missing NAVs for weekends and market holidays are forward-filled from the last available trading day (cleaning step).
- Source: AMFI publishes NAVs at end of each trading day.

---

### `fact_transactions`

Investor-level transaction records including SIP, lump-sum investments, and redemptions.

| Column | Data Type | Nullable | Constraint | Description | Source |
|---|---|---|---|---|---|
| `txn_id` | INTEGER | No — **PK** | AUTOINCREMENT | Surrogate primary key. | Generated |
| `investor_id` | TEXT | Yes | — | Anonymised investor identifier (PAN-based hash or internal ID). | `investor_transactions.csv` |
| `amfi_code` | INTEGER | No | FK → dim_fund | Target mutual fund scheme. | `investor_transactions.csv` |
| `date_id` | INTEGER | No | FK → dim_date | Transaction execution date (YYYYMMDD). | Derived |
| `transaction_type` | TEXT | No | IN ('SIP','LUMPSUM','REDEMPTION','UNKNOWN') | Standardised transaction type. SIP = monthly systematic investment; LUMPSUM = one-time investment; REDEMPTION = withdrawal/sell. | `investor_transactions.csv` |
| `amount` | REAL | No | > 0 | Transaction amount in INR (₹). Minimum SIP: ₹500. | `investor_transactions.csv` |
| `units` | REAL | Yes | — | Number of units allocated/redeemed. units = amount / nav_at_txn. | `investor_transactions.csv` |
| `nav_at_txn` | REAL | Yes | — | NAV applicable at time of transaction (₹ per unit). | `investor_transactions.csv` |
| `state` | TEXT | Yes | — | Investor's Indian state. Used for regional analysis. | `investor_transactions.csv` |
| `kyc_status` | TEXT | Yes | — | KYC compliance status: VERIFIED / PENDING / REJECTED / NOT_SUBMITTED. | `investor_transactions.csv` |

---

### `fact_performance`

Scheme-level risk-return metrics, typically published monthly or quarterly by AMCs/AMFI.

| Column | Data Type | Nullable | Description | Source |
|---|---|---|---|---|
| `perf_id` | INTEGER | No — **PK** | Surrogate primary key. | Generated |
| `amfi_code` | INTEGER | No | FK → dim_fund. AMFI scheme code. | `scheme_performance.csv` |
| `as_of_date_id` | INTEGER | Yes | FK → dim_date. Date as of which metrics are calculated. | `scheme_performance.csv` |
| `return_1yr` | REAL | Yes | Absolute return (%) over trailing 1 year. | `scheme_performance.csv` |
| `return_3yr` | REAL | Yes | CAGR (%) over trailing 3 years. | `scheme_performance.csv` |
| `return_5yr` | REAL | Yes | CAGR (%) over trailing 5 years. | `scheme_performance.csv` |
| `ytd_return` | REAL | Yes | Year-to-date return (%) from 1 Jan of current year. | `scheme_performance.csv` |
| `alpha` | REAL | Yes | Jensen's Alpha — excess return above benchmark. Positive = outperformance. | `scheme_performance.csv` |
| `beta` | REAL | Yes | Market sensitivity vs benchmark. Beta > 1 = more volatile than market. | `scheme_performance.csv` |
| `sharpe_ratio` | REAL | Yes | Risk-adjusted return: (return − risk-free rate) / std dev. Higher is better. | `scheme_performance.csv` |
| `expense_ratio` | REAL | Yes | Annual fund management cost as % of AUM. Valid range: 0.1% – 2.5% per SEBI limits. | `scheme_performance.csv` |

**Anomaly flags** (added during cleaning):
- `return_Xyr_anomaly_flag` — set to 1 when return value is outside [-100, 200]%.
- `expense_ratio_flag` — set to 1 when expense_ratio is outside [0.1, 2.5]%.

---

### `fact_aum`

Assets Under Management (AUM) per scheme per date. AUM is published monthly by AMFI.

| Column | Data Type | Nullable | Constraint | Description | Source |
|---|---|---|---|---|---|
| `aum_id` | INTEGER | No — **PK** | AUTOINCREMENT | Surrogate primary key. | Generated |
| `amfi_code` | INTEGER | No | FK → dim_fund | AMFI scheme identifier. | `aum_data.csv` |
| `date_id` | INTEGER | No | FK → dim_date | Month-end date of AUM publication (YYYYMMDD). | Derived |
| `aum_crores` | REAL | No | ≥ 0 | AUM in Indian Crore Rupees (1 Crore = 10 Million ₹). | `aum_data.csv` |

---

## Source CSV Datasets

| File | Cleaned File | Rows (approx.) | Description |
|---|---|---|---|
| `fund_master.csv` | `fund_master_clean.csv` | ~2,000 | AMFI scheme master list — one row per scheme |
| `nav_history.csv` | `nav_history_clean.csv` | ~2M+ | Daily NAV records per scheme (multi-year) |
| `investor_transactions.csv` | `investor_transactions_clean.csv` | varies | Individual investor transactions |
| `scheme_performance.csv` | `scheme_performance_clean.csv` | ~2,000 | Performance & risk metrics per scheme |
| `aum_data.csv` | `aum_data_clean.csv` | ~24,000 | Monthly AUM per scheme |
| `sip_data.csv` | `sip_data_clean.csv` | varies | SIP-specific aggregation data |
| `risk_metrics.csv` | `risk_metrics_clean.csv` | ~2,000 | Volatility, VaR, drawdown metrics |
| `benchmark_data.csv` | `benchmark_data_clean.csv` | varies | Index/benchmark daily prices |
| `distributor_data.csv` | `distributor_data_clean.csv` | varies | AMC-distributor relationship data |
| `state_wise_data.csv` | `state_wise_data_clean.csv` | ~700 | State-level AUM/investor distribution |

---

## AMFI Code Structure

AMFI scheme codes are 6-digit integers assigned sequentially by AMFI.

| Range | Description |
|---|---|
| 100000 – 109999 | Older / legacy debt and liquid schemes |
| 110000 – 119999 | Mid-vintage equity and hybrid schemes |
| 120000 – 129999 | Newer direct-plan equity schemes (post-2013 SEBI mandate) |
| 130000+ | Recently launched schemes (post-2018 SEBI rationalisation) |

**Key schemes used in this project**:

| AMFI Code | Scheme Name | Fund House |
|---|---|---|
| 125497 | HDFC Top 100 Direct Growth | HDFC Mutual Fund |
| 119551 | SBI Bluechip Direct Growth | SBI Mutual Fund |
| 120503 | ICICI Prudential Bluechip Direct Growth | ICICI Prudential |
| 118632 | Nippon India Large Cap Direct Growth | Nippon India |
| 119092 | Axis Bluechip Direct Growth | Axis Mutual Fund |
| 120841 | Kotak Bluechip Direct Growth | Kotak Mahindra |

---

## Enum Reference Values

### `transaction_type`
| Value | Description |
|---|---|
| `SIP` | Systematic Investment Plan — regular periodic investment |
| `LUMPSUM` | One-time bulk investment |
| `REDEMPTION` | Partial or full withdrawal / sale of units |
| `UNKNOWN` | Unrecognised value flagged during cleaning |

### `kyc_status`
| Value | Description |
|---|---|
| `VERIFIED` | KYC documents verified and approved |
| `PENDING` | Documents submitted, verification in progress |
| `REJECTED` | KYC rejected — investor must resubmit |
| `NOT_SUBMITTED` | KYC not started or documents not submitted |

### `risk_grade`
| Value | SEBI Risk-o-Meter Colour |
|---|---|
| `Low` | Blue |
| `Low to Moderate` | Yellow-Green |
| `Moderate` | Yellow |
| `Moderately High` | Orange |
| `High` | Orange-Red |
| `Very High` | Red |

---

*Data Dictionary maintained by Kavya — Bluestock Fintech Analytics Internship*

# Bluestock Mutual Fund Data Dictionary

## Dataset: 01_fund_master.csv

| Column | Data Type | Description |
|----------|------------|------------|
| amfi_code | Integer | Unique AMFI scheme code |
| fund_house | Text | Mutual fund company |
| scheme_name | Text | Name of scheme |
| category | Text | Fund category |
| sub_category | Text | Detailed category |
| plan | Text | Direct/Regular plan |
| launch_date | Date | Scheme launch date |
| benchmark | Text | Benchmark index |
| expense_ratio_pct | Float | Expense ratio percentage |
| exit_load_pct | Float | Exit load percentage |
| min_sip_amount | Float | Minimum SIP amount |
| min_lumpsum_amount | Float | Minimum lump sum amount |
| fund_manager | Text | Fund manager name |
| risk_category | Text | Risk classification |
| sebi_category_code | Text | SEBI category code |

---

## Dataset: 02_nav_history.csv

| Column | Data Type | Description |
|----------|------------|------------|
| amfi_code | Integer | Scheme code |
| date | Date | NAV date |
| nav | Float | Net Asset Value |

---

## Dataset: 08_investor_transactions.csv

| Column | Data Type | Description |
|----------|------------|------------|
| investor_id | Integer | Investor ID |
| transaction_date | Date | Transaction date |
| amfi_code | Integer | Fund scheme code |
| transaction_type | Text | SIP/Lumpsum/Redemption |
| amount_inr | Float | Transaction amount |
| state | Text | Investor state |
| city | Text | Investor city |
| city_tier | Text | Tier classification |
| age_group | Text | Investor age group |
| gender | Text | Investor gender |
| annual_income_lakh | Float | Annual income in lakhs |
| payment_mode | Text | Mode of payment |
| kyc_status | Text | KYC verification status |

---

## Dataset: 07_scheme_performance.csv

| Column | Data Type | Description |
|----------|------------|------------|
| amfi_code | Integer | Scheme code |
| return_1yr_pct | Float | 1-year return (%) |
| return_3yr_pct | Float | 3-year return (%) |
| return_5yr_pct | Float | 5-year return (%) |
| benchmark_3yr_pct | Float | Benchmark return |
| alpha | Float | Alpha measure |
| beta | Float | Beta measure |
| sharpe_ratio | Float | Sharpe Ratio |
| sortino_ratio | Float | Sortino Ratio |
| std_dev_ann_pct | Float | Annualized standard deviation |
| max_drawdown_pct | Float | Maximum drawdown |
| aum_crore | Float | Assets under management |
| expense_ratio_pct | Float | Expense ratio |
| morningstar_rating | Integer | Morningstar rating |
| risk_grade | Text | Risk grade |
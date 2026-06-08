-- =============================================================================
--  Bluestock Fintech Internship — Day 2
--  File   : queries.sql
--  Purpose: 10 analytical SQL queries on the bluestock_mf star schema
-- =============================================================================

-- ─────────────────────────────────────────────────────────────────────────────
-- Q1. Top 5 funds by AUM (most recent month)
-- ─────────────────────────────────────────────────────────────────────────────
SELECT
    f.amfi_code,
    f.scheme_name,
    f.fund_house,
    ROUND(a.aum_crores, 2)   AS aum_crores,
    d.full_date              AS as_of_date
FROM fact_aum  a
JOIN dim_fund  f ON a.amfi_code = f.amfi_code
JOIN dim_date  d ON a.date_id   = d.date_id
WHERE d.full_date = (SELECT MAX(full_date) FROM dim_date WHERE date_id IN (SELECT date_id FROM fact_aum))
ORDER BY a.aum_crores DESC
LIMIT 5;


-- ─────────────────────────────────────────────────────────────────────────────
-- Q2. Average NAV per month (across all funds)
-- ─────────────────────────────────────────────────────────────────────────────
SELECT
    d.year,
    d.month,
    d.month_name,
    ROUND(AVG(n.nav_value), 4) AS avg_nav
FROM fact_nav n
JOIN dim_date d ON n.date_id = d.date_id
GROUP BY d.year, d.month, d.month_name
ORDER BY d.year, d.month;


-- ─────────────────────────────────────────────────────────────────────────────
-- Q3. SIP transaction YoY growth (count & amount)
-- ─────────────────────────────────────────────────────────────────────────────
WITH sip_yearly AS (
    SELECT
        d.year,
        COUNT(*)            AS sip_count,
        ROUND(SUM(t.amount), 2) AS total_amount
    FROM fact_transactions t
    JOIN dim_date d ON t.date_id = d.date_id
    WHERE t.transaction_type = 'SIP'
    GROUP BY d.year
)
SELECT
    year,
    sip_count,
    total_amount,
    LAG(sip_count,   1) OVER (ORDER BY year)    AS prev_year_count,
    LAG(total_amount,1) OVER (ORDER BY year)    AS prev_year_amount,
    ROUND(
        100.0 * (sip_count - LAG(sip_count,1) OVER (ORDER BY year))
              / NULLIF(LAG(sip_count,1) OVER (ORDER BY year), 0),
        2
    )   AS count_growth_pct,
    ROUND(
        100.0 * (total_amount - LAG(total_amount,1) OVER (ORDER BY year))
              / NULLIF(LAG(total_amount,1) OVER (ORDER BY year), 0),
        2
    )   AS amount_growth_pct
FROM sip_yearly
ORDER BY year;


-- ─────────────────────────────────────────────────────────────────────────────
-- Q4. Total transaction amount by investor state
-- ─────────────────────────────────────────────────────────────────────────────
SELECT
    t.state,
    COUNT(*)                    AS txn_count,
    ROUND(SUM(t.amount), 2)     AS total_amount,
    ROUND(AVG(t.amount), 2)     AS avg_amount
FROM fact_transactions t
WHERE t.state IS NOT NULL
GROUP BY t.state
ORDER BY total_amount DESC;


-- ─────────────────────────────────────────────────────────────────────────────
-- Q5. Funds with expense_ratio < 1%
-- ─────────────────────────────────────────────────────────────────────────────
SELECT
    f.amfi_code,
    f.scheme_name,
    f.fund_house,
    f.scheme_category,
    ROUND(p.expense_ratio, 4) AS expense_ratio
FROM fact_performance p
JOIN dim_fund f ON p.amfi_code = f.amfi_code
WHERE p.expense_ratio < 1.0
  AND p.expense_ratio > 0
ORDER BY p.expense_ratio ASC;


-- ─────────────────────────────────────────────────────────────────────────────
-- Q6. Best performing funds by 3-year return
-- ─────────────────────────────────────────────────────────────────────────────
SELECT
    f.amfi_code,
    f.scheme_name,
    f.fund_house,
    f.scheme_category,
    ROUND(p.return_3yr, 2)    AS return_3yr_pct,
    ROUND(p.return_1yr, 2)    AS return_1yr_pct,
    ROUND(p.sharpe_ratio, 3)  AS sharpe_ratio
FROM fact_performance p
JOIN dim_fund f ON p.amfi_code = f.amfi_code
WHERE p.return_3yr IS NOT NULL
ORDER BY p.return_3yr DESC
LIMIT 10;


-- ─────────────────────────────────────────────────────────────────────────────
-- Q7. Fund-wise monthly NAV trend (latest 6 months, top 5 funds by AUM)
-- ─────────────────────────────────────────────────────────────────────────────
WITH top5 AS (
    SELECT amfi_code
    FROM fact_aum
    GROUP BY amfi_code
    ORDER BY SUM(aum_crores) DESC
    LIMIT 5
)
SELECT
    f.scheme_name,
    d.year,
    d.month,
    d.month_name,
    ROUND(AVG(n.nav_value), 4) AS avg_monthly_nav
FROM fact_nav n
JOIN dim_date d  ON n.date_id   = d.date_id
JOIN dim_fund f  ON n.amfi_code = f.amfi_code
JOIN top5 t      ON n.amfi_code = t.amfi_code
GROUP BY f.scheme_name, d.year, d.month, d.month_name
ORDER BY f.scheme_name, d.year DESC, d.month DESC
LIMIT 60;


-- ─────────────────────────────────────────────────────────────────────────────
-- Q8. Transaction breakdown: SIP vs Lumpsum vs Redemption per fund house
-- ─────────────────────────────────────────────────────────────────────────────
SELECT
    f.fund_house,
    t.transaction_type,
    COUNT(*)                AS txn_count,
    ROUND(SUM(t.amount), 2) AS total_amount
FROM fact_transactions t
JOIN dim_fund f ON t.amfi_code = f.amfi_code
GROUP BY f.fund_house, t.transaction_type
ORDER BY f.fund_house, t.transaction_type;


-- ─────────────────────────────────────────────────────────────────────────────
-- Q9. Funds with high Sharpe ratio (> 1.0) and positive alpha
-- ─────────────────────────────────────────────────────────────────────────────
SELECT
    f.amfi_code,
    f.scheme_name,
    f.fund_house,
    ROUND(p.sharpe_ratio, 3) AS sharpe_ratio,
    ROUND(p.alpha, 3)        AS alpha,
    ROUND(p.beta, 3)         AS beta,
    ROUND(p.return_1yr, 2)   AS return_1yr_pct
FROM fact_performance p
JOIN dim_fund f ON p.amfi_code = f.amfi_code
WHERE p.sharpe_ratio > 1.0
  AND p.alpha > 0
ORDER BY p.sharpe_ratio DESC;


-- ─────────────────────────────────────────────────────────────────────────────
-- Q10. KYC compliance rate by state
-- ─────────────────────────────────────────────────────────────────────────────
SELECT
    state,
    COUNT(*)                                                                AS total_investors,
    SUM(CASE WHEN kyc_status = 'VERIFIED' THEN 1 ELSE 0 END)              AS kyc_verified,
    SUM(CASE WHEN kyc_status = 'PENDING'  THEN 1 ELSE 0 END)              AS kyc_pending,
    ROUND(
        100.0 * SUM(CASE WHEN kyc_status = 'VERIFIED' THEN 1 ELSE 0 END)
              / NULLIF(COUNT(*), 0),
        2
    )   AS kyc_compliance_pct
FROM fact_transactions
WHERE state IS NOT NULL
GROUP BY state
ORDER BY kyc_compliance_pct DESC;

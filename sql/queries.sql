-- =====================================================
-- 1. Top 5 Funds by AUM
-- =====================================================

SELECT
    scheme_name,
    fund_house,
    aum_crore
FROM fact_performance
ORDER BY aum_crore DESC
LIMIT 5;


-- =====================================================
-- 2. Average NAV by Fund
-- =====================================================

SELECT
    amfi_code,
    ROUND(AVG(nav), 2) AS avg_nav
FROM fact_nav
GROUP BY amfi_code
ORDER BY avg_nav DESC;


-- =====================================================
-- 3. Average Monthly NAV
-- =====================================================

SELECT
    strftime('%Y-%m', date) AS month,
    ROUND(AVG(nav), 2) AS avg_monthly_nav
FROM fact_nav
GROUP BY month
ORDER BY month;


-- =====================================================
-- 4. SIP Transactions Count
-- =====================================================

SELECT
    COUNT(*) AS sip_transaction_count
FROM fact_transactions
WHERE transaction_type = 'SIP';


-- =====================================================
-- 5. Transactions by State
-- =====================================================

SELECT
    state,
    COUNT(*) AS total_transactions
FROM fact_transactions
GROUP BY state
ORDER BY total_transactions DESC;


-- =====================================================
-- 6. Top 10 Funds by 5-Year Return
-- =====================================================

SELECT
    scheme_name,
    return_5yr_pct
FROM fact_performance
ORDER BY return_5yr_pct DESC
LIMIT 10;


-- =====================================================
-- 7. Funds with Expense Ratio Below 1%
-- =====================================================

SELECT
    scheme_name,
    expense_ratio_pct
FROM fact_performance
WHERE expense_ratio_pct < 1
ORDER BY expense_ratio_pct;


-- =====================================================
-- 8. Average Transaction Amount
-- =====================================================

SELECT
    ROUND(AVG(amount_inr), 2) AS avg_transaction_amount
FROM fact_transactions;


-- =====================================================
-- 9. Fund Distribution by Risk Category
-- =====================================================

SELECT
    risk_category,
    COUNT(*) AS total_funds
FROM dim_fund
GROUP BY risk_category
ORDER BY total_funds DESC;


-- =====================================================
-- 10. Top 10 Funds by Alpha
-- =====================================================

SELECT
    scheme_name,
    alpha
FROM fact_performance
ORDER BY alpha DESC
LIMIT 10;
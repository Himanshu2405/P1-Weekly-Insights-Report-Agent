-- ============================================================================
-- weekly_cuts.sql
-- Orders and revenue per week x country x traffic source, for a short list of
-- weeks only (reporting week, prior week, same week last year).
-- Feeds the "Growth drivers" charts and the detail tables.
--
-- Region is NOT mapped here. Python maps country -> region using
-- config.REGION_BY_COUNTRY, so a new or misspelled country fails the
-- data-quality gate instead of silently dropping out of the totals.
--
-- Parameters (passed by bq.py):
--   @weeks         ARRAY<DATE>  Mondays to include
--   @data_through  TIMESTAMP    last instant of the reporting week
--
-- To run by hand in the BigQuery console, replace the parameters, e.g.:
--   @weeks        -> [DATE '2026-09-14', DATE '2026-09-07', DATE '2025-09-15']
--   @data_through -> TIMESTAMP '2026-09-20 23:59:59'
-- ============================================================================

-- CTE 1: orders
-- Orders placed in the requested weeks only, with the user_id needed to look up
-- the customer's country and traffic source.
--   * IN UNNEST(@weeks) keeps just the 3 weeks we compare, so the scan result
--     stays small.
--   * created_at <= @data_through is the same cutoff as weekly_kpis.sql, so the
--     totals here always add up to the KPI totals.
WITH orders AS (
  SELECT
    order_id,
    user_id,
    DATE_TRUNC(DATE(created_at), WEEK(MONDAY)) AS week_start
  FROM `bigquery-public-data.thelook_ecommerce.orders`
  WHERE DATE_TRUNC(DATE(created_at), WEEK(MONDAY)) IN UNNEST(@weeks)
    AND created_at <= @data_through
),

-- CTE 2: item_revenue
-- Same revenue rule as weekly_kpis.sql: sum of non-cancelled item prices per
-- order, attributed to the order's week. Keeping the rule identical means
-- segment revenue sums to the total Weekly Gross Revenue.
item_revenue AS (
  SELECT
    i.order_id,
    SUM(IF(i.status != 'Cancelled', i.sale_price, 0)) AS revenue
  FROM `bigquery-public-data.thelook_ecommerce.order_items` AS i
  JOIN orders AS o USING (order_id)
  GROUP BY i.order_id
)

-- Final SELECT
-- Attach each order's customer attributes from users, then aggregate.
--   * country:        mapped to a region in Python (APAC, North America, EMEA, LATAM)
--   * traffic_source: how the customer originally arrived (Search, Organic, ...)
--   * Inner JOIN on users is safe: every order has a matching user (verified,
--     0 orphan orders), so no orders are lost.
-- Output grain: one row per week_start x country x traffic_source.
SELECT
  o.week_start,
  u.country,
  u.traffic_source,
  COUNT(*) AS orders,
  ROUND(SUM(r.revenue), 2) AS revenue
FROM orders AS o
JOIN `bigquery-public-data.thelook_ecommerce.users` AS u ON u.id = o.user_id
JOIN item_revenue AS r USING (order_id)
GROUP BY o.week_start, u.country, u.traffic_source
ORDER BY o.week_start, u.country, u.traffic_source

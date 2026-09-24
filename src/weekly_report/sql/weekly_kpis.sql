-- ============================================================================
-- weekly_kpis.sql
-- One row per week (Monday week_start, UTC) with the raw counts and sums that
-- Python turns into the 6 core KPIs (rates and AOV are derived in brief.py).
--
-- Parameters (passed by bq.py):
--   @start_week    DATE       first Monday to include (about 120 weeks back,
--                             enough for 52-week history + same week last year)
--   @data_through  TIMESTAMP  last instant of the reporting week, e.g.
--                             2026-09-20 23:59:59.999999 UTC. Nothing after this
--                             is ever read.
--
-- To run by hand in the BigQuery console, replace the parameters, e.g.:
--   @start_week   -> DATE '2024-06-03'
--   @data_through -> TIMESTAMP '2026-09-20 23:59:59'
-- ============================================================================

-- CTE 1: orders
-- One row per order placed in the window, tagged with the Monday of its week.
--   * week_start: DATE_TRUNC(..., WEEK(MONDAY)) snaps any date to its Monday,
--     so every order lands in a Monday-to-Sunday bucket.
--   * The upper bound (created_at <= @data_through) drops the in-progress week,
--     so a partial week can never be reported.
--   * status and returned_at are kept for the cancellation and return counts.
WITH orders AS (
  SELECT
    order_id,
    DATE_TRUNC(DATE(created_at), WEEK(MONDAY)) AS week_start,
    status,
    created_at,
    returned_at
  FROM `bigquery-public-data.thelook_ecommerce.orders`
  WHERE created_at >= TIMESTAMP(@start_week)
    AND created_at <= @data_through
),

-- CTE 2: item_revenue
-- Revenue per order = sum of its items' sale_price, excluding cancelled items.
--   * Joined to CTE 1 so revenue is attributed to the week the ORDER was placed,
--     not the item's own timestamp (about 27k items fall in a different week than
--     their order). This keeps AOV = revenue / orders consistent.
--   * Returns are NOT subtracted: this is gross revenue. Returns are tracked
--     separately by the 14-Day Return Rate.
item_revenue AS (
  SELECT
    i.order_id,
    SUM(IF(i.status != 'Cancelled', i.sale_price, 0)) AS revenue
  FROM `bigquery-public-data.thelook_ecommerce.order_items` AS i
  JOIN orders AS o USING (order_id)
  GROUP BY i.order_id
),

-- CTE 3: order_kpis
-- Rolls orders up to one row per week and counts what each KPI needs.
--   * orders:               all orders placed that week, any status
--                           (Weekly Orders Placed)
--   * cancelled_orders:     numerator of the cancellation rate
--   * non_cancelled_orders: denominator of AOV
--   * returned_14d_orders:  orders the customer returned within 14 days of
--                           ordering. Two safety conditions:
--                             1. returned_at <= created_at + 14 days (the window)
--                             2. returned_at <= @data_through, because the source
--                                contains future-dated returns and we never use
--                                events after the report cutoff
--   * revenue:              sum of CTE 2 per week (Weekly Gross Revenue)
order_kpis AS (
  SELECT
    o.week_start,
    COUNT(*) AS orders,
    COUNTIF(o.status = 'Cancelled') AS cancelled_orders,
    COUNTIF(o.status != 'Cancelled') AS non_cancelled_orders,
    COUNTIF(
      o.returned_at IS NOT NULL
      AND o.returned_at <= TIMESTAMP_ADD(o.created_at, INTERVAL 14 DAY)
      AND o.returned_at <= @data_through
    ) AS returned_14d_orders,
    SUM(r.revenue) AS revenue
  FROM orders AS o
  JOIN item_revenue AS r USING (order_id)
  GROUP BY o.week_start
),

-- CTE 4: signups
-- New customer accounts per week (Weekly New Customer Signups), same weekly
-- bucketing and the same cutoff as orders.
signups AS (
  SELECT
    DATE_TRUNC(DATE(created_at), WEEK(MONDAY)) AS week_start,
    COUNT(*) AS new_signups
  FROM `bigquery-public-data.thelook_ecommerce.users`
  WHERE created_at >= TIMESTAMP(@start_week)
    AND created_at <= @data_through
  GROUP BY week_start
)

-- Final SELECT
-- Joins order KPIs with signups on week_start. LEFT JOIN + COALESCE so a week
-- with orders but zero signups still appears (with 0) instead of disappearing.
-- Python (brief.py) then derives:
--   AOV               = revenue / non_cancelled_orders
--   cancellation rate = 100 * cancelled_orders / orders
--   14-day return %   = 100 * returned_14d_orders / orders  (mature week only)
SELECT
  k.week_start,
  k.orders,
  k.cancelled_orders,
  k.non_cancelled_orders,
  k.returned_14d_orders,
  ROUND(k.revenue, 2) AS revenue,
  COALESCE(s.new_signups, 0) AS new_signups
FROM order_kpis AS k
LEFT JOIN signups AS s USING (week_start)
ORDER BY k.week_start

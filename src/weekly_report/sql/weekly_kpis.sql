-- Weekly KPIs, one row per week (Monday week_start, UTC).
-- Params: @start_week (DATE), @data_through (TIMESTAMP, last instant of the reporting week)
-- Rules:
--   * An order belongs to the week it was placed (orders.created_at).
--   * Revenue = items of that week's orders, excluding cancelled items (returns NOT subtracted).
--   * 14-day returns only count returns that happened on or before @data_through
--     (the source contains future-dated events; we never read past the report cutoff).

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
item_revenue AS (
  SELECT
    i.order_id,
    SUM(IF(i.status != 'Cancelled', i.sale_price, 0)) AS revenue
  FROM `bigquery-public-data.thelook_ecommerce.order_items` AS i
  JOIN orders AS o USING (order_id)
  GROUP BY i.order_id
),
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
signups AS (
  SELECT
    DATE_TRUNC(DATE(created_at), WEEK(MONDAY)) AS week_start,
    COUNT(*) AS new_signups
  FROM `bigquery-public-data.thelook_ecommerce.users`
  WHERE created_at >= TIMESTAMP(@start_week)
    AND created_at <= @data_through
  GROUP BY week_start
)
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

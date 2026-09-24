-- weekly_facts.sql: one row per week x country x traffic_source.
-- Python sums it into weekly KPIs, filters it for cuts, and maps country -> region.
-- Params: @start_week (DATE), @data_through (TIMESTAMP, end of the reporting week).

-- Orders in the window with week (Monday) and customer attributes.
-- The cutoff excludes the in-progress week.
WITH orders AS (
  SELECT
    o.order_id,
    DATE_TRUNC(DATE(o.created_at), WEEK(MONDAY)) AS week_start,
    u.country,
    u.traffic_source,
    o.status,
    o.created_at,
    o.returned_at
  FROM `bigquery-public-data.thelook_ecommerce.orders` AS o
  JOIN `bigquery-public-data.thelook_ecommerce.users` AS u ON u.id = o.user_id
  WHERE o.created_at >= TIMESTAMP(@start_week)
    AND o.created_at <= @data_through
),

-- Gross revenue per order (non-cancelled items), counted in the order's week.
item_revenue AS (
  SELECT
    i.order_id,
    SUM(IF(i.status != 'Cancelled', i.sale_price, 0)) AS revenue
  FROM `bigquery-public-data.thelook_ecommerce.order_items` AS i
  JOIN orders AS o USING (order_id)
  GROUP BY i.order_id
),

-- Order counts and revenue per week x country x traffic_source.
-- Returns count only within 14 days and never after the cutoff (source has future-dated events).
order_facts AS (
  SELECT
    o.week_start,
    o.country,
    o.traffic_source,
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
  GROUP BY o.week_start, o.country, o.traffic_source
),

-- New signups at the same grain.
signup_facts AS (
  SELECT
    DATE_TRUNC(DATE(created_at), WEEK(MONDAY)) AS week_start,
    country,
    traffic_source,
    COUNT(*) AS new_signups
  FROM `bigquery-public-data.thelook_ecommerce.users`
  WHERE created_at >= TIMESTAMP(@start_week)
    AND created_at <= @data_through
  GROUP BY week_start, country, traffic_source
)

-- Full outer join so rows with only orders or only signups are kept.
SELECT
  COALESCE(o.week_start, s.week_start) AS week_start,
  COALESCE(o.country, s.country) AS country,
  COALESCE(o.traffic_source, s.traffic_source) AS traffic_source,
  COALESCE(o.orders, 0) AS orders,
  COALESCE(o.cancelled_orders, 0) AS cancelled_orders,
  COALESCE(o.non_cancelled_orders, 0) AS non_cancelled_orders,
  COALESCE(o.returned_14d_orders, 0) AS returned_14d_orders,
  ROUND(COALESCE(o.revenue, 0), 2) AS revenue,
  COALESCE(s.new_signups, 0) AS new_signups
FROM order_facts AS o
FULL OUTER JOIN signup_facts AS s
  ON o.week_start = s.week_start
  AND o.country = s.country
  AND o.traffic_source = s.traffic_source
ORDER BY week_start, country, traffic_source

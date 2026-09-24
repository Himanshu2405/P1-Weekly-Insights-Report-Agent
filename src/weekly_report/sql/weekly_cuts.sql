-- Orders and revenue per week, country, and traffic source, for specific weeks only.
-- Region mapping is done in Python (config.REGION_BY_COUNTRY) so an unmapped country
-- can fail the data-quality gate instead of disappearing silently.
-- Params: @weeks (ARRAY<DATE>), @data_through (TIMESTAMP)

WITH orders AS (
  SELECT
    order_id,
    user_id,
    DATE_TRUNC(DATE(created_at), WEEK(MONDAY)) AS week_start
  FROM `bigquery-public-data.thelook_ecommerce.orders`
  WHERE DATE_TRUNC(DATE(created_at), WEEK(MONDAY)) IN UNNEST(@weeks)
    AND created_at <= @data_through
),
item_revenue AS (
  SELECT
    i.order_id,
    SUM(IF(i.status != 'Cancelled', i.sale_price, 0)) AS revenue
  FROM `bigquery-public-data.thelook_ecommerce.order_items` AS i
  JOIN orders AS o USING (order_id)
  GROUP BY i.order_id
)
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

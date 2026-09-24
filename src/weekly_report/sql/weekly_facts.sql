-- ============================================================================
-- weekly_facts.sql  (the only query the pipeline runs each week)
--
-- One row per week x country x traffic_source with the raw counts and sums
-- behind every KPI and every cut. Python (brief.py) then:
--   * sums across country and traffic_source -> weekly totals for the 6 KPIs
--   * filters to 3 weeks (reporting, prior, last year) -> region and traffic cuts
--   * derives rates and AOV (AOV, cancellation %, 14-day return %)
--   * maps country -> region (an unmapped country fails the data-quality gate)
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
-- One row per order placed in the window, with its week and the customer's
-- country and traffic source.
--   * week_start: DATE_TRUNC(..., WEEK(MONDAY)) snaps any date to its Monday,
--     so every order lands in a Monday-to-Sunday bucket.
--   * created_at <= @data_through drops the in-progress week, so a partial
--     week can never be reported.
--   * Inner JOIN to users is safe: every order has a matching user (verified,
--     0 orphan orders), so no orders are lost.
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

-- CTE 3: order_facts
-- Rolls orders up to week x country x traffic_source and counts what each KPI needs.
--   * orders:               all orders placed, any status (Weekly Orders Placed)
--   * cancelled_orders:     numerator of the cancellation rate
--   * non_cancelled_orders: denominator of AOV
--   * returned_14d_orders:  orders the customer returned within 14 days of
--                           ordering. Two safety conditions:
--                             1. returned_at <= created_at + 14 days (the window)
--                             2. returned_at <= @data_through, because the source
--                                contains future-dated returns and we never use
--                                events after the report cutoff
--   * revenue:              sum of CTE 2 (Weekly Gross Revenue)
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

-- CTE 4: signup_facts
-- New customer accounts at the same grain (week x country x traffic_source),
-- same weekly bucketing and the same cutoff as orders.
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

-- Final SELECT
-- FULL OUTER JOIN keeps a combination that has orders but no signups (or the
-- reverse) instead of dropping it; COALESCE turns the missing side into 0.
-- Output grain: one row per week_start x country x traffic_source
-- (about 120 weeks x 16 countries x 5 sources, under 10k rows).
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

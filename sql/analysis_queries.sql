-- SQLite analysis queries for Marketing Performance & Growth Intelligence.
-- Aggregate each fact table to the requested grain before joining fact tables.

-- 1. Executive KPI summary
SELECT
    (SELECT SUM(revenue) FROM conversions) AS total_revenue,
    (SELECT SUM(spend) FROM marketing_spend) AS total_spend,
    (SELECT COUNT(*) FROM conversions) AS total_conversions,
    (SELECT COUNT(DISTINCT customer_id) FROM conversions) AS acquired_customers;

-- 2. Monthly revenue and spend (each fact aggregated independently)
WITH revenue_by_month AS (
    SELECT strftime('%Y-%m', conversion_date) AS month, SUM(revenue) AS revenue
    FROM conversions GROUP BY strftime('%Y-%m', conversion_date)
),
spend_by_month AS (
    SELECT strftime('%Y-%m', activity_date) AS month, SUM(spend) AS spend
    FROM marketing_spend GROUP BY strftime('%Y-%m', activity_date)
),
months AS (
    SELECT month FROM revenue_by_month
    UNION
    SELECT month FROM spend_by_month
)
SELECT m.month, r.revenue, s.spend
FROM months m
LEFT JOIN revenue_by_month r USING (month)
LEFT JOIN spend_by_month s USING (month)
ORDER BY m.month;

-- 3. Campaign revenue, spend, conversions, and ROAS
WITH revenue AS (
    SELECT campaign_id, SUM(revenue) AS revenue, COUNT(*) AS conversions
    FROM conversions GROUP BY campaign_id
),
spend AS (
    SELECT campaign_id, SUM(spend) AS spend
    FROM marketing_spend GROUP BY campaign_id
)
SELECT c.campaign_name, ch.channel_name, COALESCE(r.revenue, 0) AS revenue,
       COALESCE(s.spend, 0) AS spend, COALESCE(r.conversions, 0) AS conversions,
       COALESCE(r.revenue / NULLIF(s.spend, 0), 0) AS roas
FROM campaigns c
JOIN channels ch USING (channel_id)
LEFT JOIN revenue r USING (campaign_id)
LEFT JOIN spend s USING (campaign_id)
ORDER BY revenue DESC;

-- 4. Channel revenue, spend, and ROAS
WITH revenue AS (
    SELECT c.channel_id, SUM(v.revenue) AS revenue, COUNT(*) AS conversions
    FROM conversions v JOIN campaigns c USING (campaign_id)
    GROUP BY c.channel_id
),
spend AS (
    SELECT c.channel_id, SUM(s.spend) AS spend, SUM(s.clicks) AS clicks,
           SUM(s.impressions) AS impressions
    FROM marketing_spend s JOIN campaigns c USING (campaign_id)
    GROUP BY c.channel_id
)
SELECT ch.channel_name, COALESCE(r.revenue, 0) AS revenue, COALESCE(s.spend, 0) AS spend,
       COALESCE(r.conversions, 0) AS conversions,
       COALESCE(r.revenue / NULLIF(s.spend, 0), 0) AS roas
FROM channels ch
LEFT JOIN revenue r USING (channel_id)
LEFT JOIN spend s USING (channel_id)
ORDER BY roas DESC;

-- 5. Campaign CTR, CPC, CPA, and conversion rate
WITH delivery AS (
    SELECT campaign_id, SUM(spend) AS spend, SUM(impressions) AS impressions, SUM(clicks) AS clicks
    FROM marketing_spend GROUP BY campaign_id
),
results AS (
    SELECT campaign_id, COUNT(*) AS conversions, SUM(revenue) AS revenue
    FROM conversions GROUP BY campaign_id
)
SELECT c.campaign_name,
       100.0 * d.clicks / NULLIF(d.impressions, 0) AS ctr_percent,
       d.spend / NULLIF(d.clicks, 0) AS cpc,
       d.spend / NULLIF(r.conversions, 0) AS cpa,
       100.0 * r.conversions / NULLIF(d.clicks, 0) AS conversion_rate_percent,
       r.revenue / NULLIF(d.spend, 0) AS roas
FROM campaigns c
LEFT JOIN delivery d USING (campaign_id)
LEFT JOIN results r USING (campaign_id)
ORDER BY roas DESC;

-- 6. Campaign budget utilization
SELECT c.campaign_name, c.budget, COALESCE(SUM(s.spend), 0) AS actual_spend,
       100.0 * COALESCE(SUM(s.spend), 0) / NULLIF(c.budget, 0) AS budget_used_percent
FROM campaigns c LEFT JOIN marketing_spend s USING (campaign_id)
GROUP BY c.campaign_id
ORDER BY budget_used_percent DESC;

-- 7. Acquired customers by channel
SELECT ch.channel_name, COUNT(DISTINCT v.customer_id) AS acquired_customers
FROM conversions v
JOIN campaigns c USING (campaign_id)
JOIN channels ch USING (channel_id)
GROUP BY ch.channel_name
ORDER BY acquired_customers DESC;

-- 8. Revenue and customers by customer segment
SELECT cu.segment, COUNT(DISTINCT v.customer_id) AS customers,
       COUNT(*) AS conversions, SUM(v.revenue) AS revenue
FROM conversions v JOIN customers cu USING (customer_id)
GROUP BY cu.segment
ORDER BY revenue DESC;

-- 9. Revenue and customers by region
SELECT cu.region, COUNT(DISTINCT v.customer_id) AS customers,
       COUNT(*) AS conversions, SUM(v.revenue) AS revenue
FROM conversions v JOIN customers cu USING (customer_id)
GROUP BY cu.region
ORDER BY revenue DESC;

-- 10. Repeat conversion rate
WITH customer_orders AS (
    SELECT customer_id, COUNT(*) AS conversion_count
    FROM conversions GROUP BY customer_id
)
SELECT COUNT(*) AS converting_customers,
       SUM(CASE WHEN conversion_count > 1 THEN 1 ELSE 0 END) AS repeat_customers,
       100.0 * SUM(CASE WHEN conversion_count > 1 THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0) AS repeat_rate_percent
FROM customer_orders;

-- 11. Overall conversion funnel
SELECT 'Impressions' AS stage, SUM(impressions) AS volume FROM marketing_spend
UNION ALL SELECT 'Clicks', SUM(clicks) FROM marketing_spend
UNION ALL SELECT 'Leads', COUNT(*) FROM leads
UNION ALL SELECT 'Conversions', COUNT(*) FROM conversions;

-- 12. Campaign-wise funnel and click-through rate
WITH delivery AS (
    SELECT campaign_id, SUM(impressions) AS impressions, SUM(clicks) AS clicks
    FROM marketing_spend GROUP BY campaign_id
),
lead_counts AS (
    SELECT campaign_id, COUNT(*) AS leads FROM leads GROUP BY campaign_id
),
conversion_counts AS (
    SELECT campaign_id, COUNT(*) AS conversions FROM conversions GROUP BY campaign_id
)
SELECT c.campaign_name, COALESCE(d.impressions, 0) AS impressions,
       COALESCE(d.clicks, 0) AS clicks, COALESCE(l.leads, 0) AS leads,
       COALESCE(v.conversions, 0) AS conversions,
       100.0 * d.clicks / NULLIF(d.impressions, 0) AS ctr_percent
FROM campaigns c
LEFT JOIN delivery d USING (campaign_id)
LEFT JOIN lead_counts l USING (campaign_id)
LEFT JOIN conversion_counts v USING (campaign_id)
ORDER BY conversions DESC;

-- 13. Campaigns with CPA above the portfolio average
WITH spend AS (
    SELECT campaign_id, SUM(spend) AS spend FROM marketing_spend GROUP BY campaign_id
),
conversion_counts AS (
    SELECT campaign_id, COUNT(*) AS conversions FROM conversions GROUP BY campaign_id
),
campaign_cpa AS (
    SELECT c.campaign_name, s.spend / NULLIF(v.conversions, 0) AS cpa
    FROM campaigns c JOIN spend s USING (campaign_id)
    JOIN conversion_counts v USING (campaign_id)
)
SELECT campaign_name, cpa
FROM campaign_cpa
WHERE cpa > (SELECT AVG(cpa) FROM campaign_cpa)
ORDER BY cpa DESC;

-- 14. Campaigns ranked by ROAS
WITH revenue AS (
    SELECT campaign_id, SUM(revenue) AS revenue FROM conversions GROUP BY campaign_id
),
spend AS (
    SELECT campaign_id, SUM(spend) AS spend FROM marketing_spend GROUP BY campaign_id
)
SELECT c.campaign_name, r.revenue / NULLIF(s.spend, 0) AS roas
FROM campaigns c JOIN revenue r USING (campaign_id) JOIN spend s USING (campaign_id)
ORDER BY roas DESC;

-- 15. Daily spend trend
SELECT activity_date, SUM(spend) AS spend, SUM(impressions) AS impressions,
       SUM(clicks) AS clicks
FROM marketing_spend
GROUP BY activity_date
ORDER BY activity_date;

-- 16. Daily attributed revenue
SELECT conversion_date, SUM(revenue) AS revenue, COUNT(*) AS conversions
FROM conversions
GROUP BY conversion_date
ORDER BY conversion_date;

-- 17. Revenue by product
SELECT p.product_name, p.category, SUM(t.amount) AS revenue,
       COUNT(*) AS transactions
FROM transactions t JOIN products p USING (product_id)
GROUP BY p.product_id
ORDER BY revenue DESC;

-- 18. Revenue and transaction count by product category
SELECT p.category, SUM(t.amount) AS revenue, COUNT(*) AS transactions
FROM transactions t JOIN products p USING (product_id)
GROUP BY p.category
ORDER BY revenue DESC;

-- 19. Lead-to-conversion rate by channel
WITH lead_counts AS (
    SELECT c.channel_id, COUNT(*) AS leads
    FROM leads l JOIN campaigns c USING (campaign_id)
    GROUP BY c.channel_id
),
conversion_counts AS (
    SELECT c.channel_id, COUNT(*) AS conversions
    FROM conversions v JOIN campaigns c USING (campaign_id)
    GROUP BY c.channel_id
)
SELECT ch.channel_name, COALESCE(l.leads, 0) AS leads,
       COALESCE(v.conversions, 0) AS conversions,
       100.0 * COALESCE(v.conversions, 0) / NULLIF(l.leads, 0) AS lead_conversion_percent
FROM channels ch LEFT JOIN lead_counts l USING (channel_id)
LEFT JOIN conversion_counts v USING (channel_id)
ORDER BY lead_conversion_percent DESC;

-- 20. Customer lifetime value to date (observed revenue, not a forecast)
SELECT cu.customer_id, cu.region, cu.segment,
       COUNT(v.conversion_id) AS conversions,
       COALESCE(SUM(v.revenue), 0) AS observed_revenue
FROM customers cu LEFT JOIN conversions v USING (customer_id)
GROUP BY cu.customer_id
ORDER BY observed_revenue DESC
LIMIT 100;

-- 21. Campaigns exceeding their approved budget
SELECT c.campaign_name, c.budget, SUM(s.spend) AS actual_spend,
       SUM(s.spend) - c.budget AS amount_over_budget
FROM campaigns c JOIN marketing_spend s USING (campaign_id)
GROUP BY c.campaign_id
HAVING SUM(s.spend) > c.budget
ORDER BY amount_over_budget DESC;

-- 22. New versus returning customer conversion revenue
WITH ordered_conversions AS (
    SELECT customer_id, conversion_date, conversion_id,
           ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY conversion_date, conversion_id) AS conversion_number
    FROM conversions
)
SELECT CASE WHEN o.conversion_number = 1 THEN 'First conversion' ELSE 'Repeat conversion' END AS customer_type,
       COUNT(*) AS conversions, SUM(v.revenue) AS revenue
FROM ordered_conversions o JOIN conversions v USING (conversion_id)
GROUP BY customer_type
ORDER BY revenue DESC;

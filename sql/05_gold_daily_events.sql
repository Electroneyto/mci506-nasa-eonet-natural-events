-- ============================================================
-- GOLD: Eventos por día
-- ============================================================

CREATE OR REPLACE TABLE `mci506-nasa-eonet.eonet_gold.gold_daily_events` AS

SELECT
  DATE(geometry_date) AS event_date,

  COUNT(DISTINCT event_id) AS total_events,
  COUNT(*) AS total_geometry_records,

  COUNT(DISTINCT IF(status = 'open', event_id, NULL)) AS open_events,
  COUNT(DISTINCT IF(status = 'closed', event_id, NULL)) AS closed_events,

  COUNT(DISTINCT category_titles) AS distinct_categories,

  AVG(magnitude_value) AS avg_magnitude_value,

  CURRENT_TIMESTAMP() AS gold_loaded_at

FROM `mci506-nasa-eonet.eonet_silver.events`
WHERE geometry_date IS NOT NULL
GROUP BY event_date
ORDER BY event_date DESC;
-- ============================================================
-- GOLD: Resumen por categoría
-- ============================================================

CREATE OR REPLACE TABLE `mci506-nasa-eonet.eonet_gold.gold_category_summary` AS

SELECT
  COALESCE(NULLIF(category_titles, ''), 'Unknown') AS category_titles,

  COUNT(DISTINCT event_id) AS total_events,
  COUNT(*) AS total_geometry_records,

  COUNT(DISTINCT IF(status = 'open', event_id, NULL)) AS open_events,
  COUNT(DISTINCT IF(status = 'closed', event_id, NULL)) AS closed_events,

  MIN(DATE(geometry_date)) AS first_geometry_date,
  MAX(DATE(geometry_date)) AS last_geometry_date,

  AVG(magnitude_value) AS avg_magnitude_value,

  CURRENT_TIMESTAMP() AS gold_loaded_at

FROM `mci506-nasa-eonet.eonet_silver.events`
GROUP BY category_titles
ORDER BY total_events DESC;
-- ============================================================
-- GOLD: Resumen por estado y categoría
-- Permite analizar eventos abiertos/cerrados filtrando por categoría,
-- por ejemplo Wildfires.
-- ============================================================

CREATE OR REPLACE TABLE `mci506-nasa-eonet.eonet_gold.gold_status_summary` AS

SELECT
  status,
  COALESCE(NULLIF(category_titles, ''), 'Unknown') AS category_titles,

  COUNT(DISTINCT event_id) AS total_events,
  COUNT(*) AS total_geometry_records,

  MIN(DATE(geometry_date)) AS first_geometry_date,
  MAX(DATE(geometry_date)) AS last_geometry_date,

  AVG(magnitude_value) AS avg_magnitude_value,

  CURRENT_TIMESTAMP() AS gold_loaded_at

FROM `mci506-nasa-eonet.eonet_silver.events`
GROUP BY status, category_titles
ORDER BY total_events DESC;
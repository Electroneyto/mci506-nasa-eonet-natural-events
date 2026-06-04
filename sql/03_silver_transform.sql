-- ============================================================
-- SILVER TRANSFORM
-- Une Bronze events + sources + geometry.
-- Deduplica Bronze antes del JOIN para evitar multiplicación de filas.
-- Aplica deduplicación incremental con WHERE NOT EXISTS.
-- ============================================================

INSERT INTO `mci506-nasa-eonet.eonet_silver.events`
(
  event_geometry_key,
  event_id,
  title,
  description,
  link,
  status,
  closed_at,
  category_ids,
  category_titles,
  source_ids,
  source_urls,
  geometry_date,
  geometry_type,
  longitude,
  latitude,
  magnitude_value,
  magnitude_unit,
  event_ingestion_timestamp,
  event_ingestion_date,
  geometry_ingestion_timestamp,
  geometry_ingestion_date,
  silver_loaded_at
)

WITH events_dedup AS (
  SELECT * EXCEPT(row_num)
  FROM (
    SELECT
      *,
      ROW_NUMBER() OVER (
        PARTITION BY event_id
        ORDER BY SAFE_CAST(ingestion_timestamp AS TIMESTAMP) DESC
      ) AS row_num
    FROM `mci506-nasa-eonet.eonet_bronze.events_external`
  )
  WHERE row_num = 1
),

geometry_dedup AS (
  SELECT * EXCEPT(row_num)
  FROM (
    SELECT
      *,
      ROW_NUMBER() OVER (
        PARTITION BY event_geometry_key
        ORDER BY SAFE_CAST(ingestion_timestamp AS TIMESTAMP) DESC
      ) AS row_num
    FROM `mci506-nasa-eonet.eonet_bronze.geometry_external`
  )
  WHERE row_num = 1
),

sources_dedup AS (
  SELECT DISTINCT
    event_id,
    source_id,
    source_url
  FROM `mci506-nasa-eonet.eonet_bronze.sources_external`
),

sources_agg AS (
  SELECT
    event_id,
    STRING_AGG(DISTINCT source_id, ', ') AS source_ids,
    STRING_AGG(DISTINCT source_url, ', ') AS source_urls
  FROM sources_dedup
  GROUP BY event_id
)

SELECT
  g.event_geometry_key,
  g.event_id,
  e.title,
  e.description,
  e.link,
  e.status,
  SAFE_CAST(e.closed_at AS TIMESTAMP) AS closed_at,

  e.category_ids,
  e.category_titles,

  s.source_ids,
  s.source_urls,

  SAFE_CAST(g.geometry_date AS TIMESTAMP) AS geometry_date,
  g.geometry_type,
  SAFE_CAST(g.longitude AS FLOAT64) AS longitude,
  SAFE_CAST(g.latitude AS FLOAT64) AS latitude,

  SAFE_CAST(g.magnitude_value AS FLOAT64) AS magnitude_value,
  g.magnitude_unit,

  SAFE_CAST(e.ingestion_timestamp AS TIMESTAMP) AS event_ingestion_timestamp,
  SAFE_CAST(e.ingestion_date AS DATE) AS event_ingestion_date,
  SAFE_CAST(g.ingestion_timestamp AS TIMESTAMP) AS geometry_ingestion_timestamp,
  SAFE_CAST(g.ingestion_date AS DATE) AS geometry_ingestion_date,

  CURRENT_TIMESTAMP() AS silver_loaded_at

FROM geometry_dedup g
LEFT JOIN events_dedup e
  ON g.event_id = e.event_id
LEFT JOIN sources_agg s
  ON g.event_id = s.event_id

WHERE g.event_geometry_key IS NOT NULL
  AND NOT EXISTS (
    SELECT 1
    FROM `mci506-nasa-eonet.eonet_silver.events` silver
    WHERE silver.event_geometry_key = g.event_geometry_key
  );
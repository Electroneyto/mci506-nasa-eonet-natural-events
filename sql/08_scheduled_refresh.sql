-- ============================================================
-- SCHEDULED REFRESH: Silver + Gold
-- Esta consulta está pensada para ejecutarse como Scheduled Query.
-- Actualiza Silver con nuevos eventos y recrea las tablas Gold.
-- ============================================================

-- ============================================================
-- 1. SILVER: Inserción incremental deduplicada
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

-- ============================================================
-- 2. GOLD: Resumen por categoría
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

-- ============================================================
-- 3. GOLD: Eventos por día y categoría
-- ============================================================

CREATE OR REPLACE TABLE `mci506-nasa-eonet.eonet_gold.gold_daily_events` AS

SELECT
  DATE(geometry_date) AS event_date,
  COALESCE(NULLIF(category_titles, ''), 'Unknown') AS category_titles,

  COUNT(DISTINCT event_id) AS total_events,
  COUNT(*) AS total_geometry_records,

  COUNT(DISTINCT IF(status = 'open', event_id, NULL)) AS open_events,
  COUNT(DISTINCT IF(status = 'closed', event_id, NULL)) AS closed_events,

  AVG(magnitude_value) AS avg_magnitude_value,

  CURRENT_TIMESTAMP() AS gold_loaded_at

FROM `mci506-nasa-eonet.eonet_silver.events`
WHERE geometry_date IS NOT NULL
GROUP BY event_date, category_titles
ORDER BY event_date DESC, total_events DESC;

-- ============================================================
-- 4. GOLD: Resumen por estado y categoría
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

-- ============================================================
-- 5. GOLD: Quality Checks
-- ============================================================

CREATE OR REPLACE TABLE `mci506-nasa-eonet.eonet_gold.quality_checks` AS

WITH base AS (
  SELECT *
  FROM `mci506-nasa-eonet.eonet_silver.events`
),

checks AS (

  SELECT
    'total_rows' AS check_name,
    CAST(COUNT(*) AS STRING) AS check_value,
    'Debe existir al menos una fila en Silver' AS check_description,
    IF(COUNT(*) > 0, 'PASS', 'FAIL') AS check_status,
    CURRENT_TIMESTAMP() AS checked_at
  FROM base

  UNION ALL

  SELECT
    'duplicate_event_geometry_key' AS check_name,
    CAST(COUNT(*) - COUNT(DISTINCT event_geometry_key) AS STRING) AS check_value,
    'No deberían existir llaves duplicadas en Silver' AS check_description,
    IF(COUNT(*) - COUNT(DISTINCT event_geometry_key) = 0, 'PASS', 'FAIL') AS check_status,
    CURRENT_TIMESTAMP() AS checked_at
  FROM base

  UNION ALL

  SELECT
    'null_event_id' AS check_name,
    CAST(COUNTIF(event_id IS NULL) AS STRING) AS check_value,
    'No deberían existir eventos sin event_id' AS check_description,
    IF(COUNTIF(event_id IS NULL) = 0, 'PASS', 'FAIL') AS check_status,
    CURRENT_TIMESTAMP() AS checked_at
  FROM base

  UNION ALL

  SELECT
    'null_coordinates' AS check_name,
    CAST(COUNTIF(latitude IS NULL OR longitude IS NULL) AS STRING) AS check_value,
    'Cantidad de registros sin coordenadas' AS check_description,
    IF(COUNTIF(latitude IS NULL OR longitude IS NULL) = 0, 'PASS', 'WARNING') AS check_status,
    CURRENT_TIMESTAMP() AS checked_at
  FROM base

  UNION ALL

  SELECT
    'future_geometry_dates' AS check_name,
    CAST(COUNTIF(DATE(geometry_date) > CURRENT_DATE()) AS STRING) AS check_value,
    'No deberían existir fechas de geometría futuras' AS check_description,
    IF(COUNTIF(DATE(geometry_date) > CURRENT_DATE()) = 0, 'PASS', 'FAIL') AS check_status,
    CURRENT_TIMESTAMP() AS checked_at
  FROM base
)

SELECT *
FROM checks;
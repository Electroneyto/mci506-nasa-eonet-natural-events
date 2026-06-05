-- ============================================================
-- GOLD: Quality Checks
-- Validaciones básicas de calidad de datos.
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
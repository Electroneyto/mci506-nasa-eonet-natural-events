-- ============================================================
-- SILVER: Native Table
-- Tabla limpia, tipada y preparada para análisis.
-- ============================================================

CREATE TABLE IF NOT EXISTS `mci506-nasa-eonet.eonet_silver.events`
(
  event_geometry_key STRING,
  event_id STRING,
  title STRING,
  description STRING,
  link STRING,
  status STRING,
  closed_at TIMESTAMP,

  category_ids STRING,
  category_titles STRING,

  source_ids STRING,
  source_urls STRING,

  geometry_date TIMESTAMP,
  geometry_type STRING,
  longitude FLOAT64,
  latitude FLOAT64,

  magnitude_value FLOAT64,
  magnitude_unit STRING,

  event_ingestion_timestamp TIMESTAMP,
  event_ingestion_date DATE,
  geometry_ingestion_timestamp TIMESTAMP,
  geometry_ingestion_date DATE,

  silver_loaded_at TIMESTAMP
)
PARTITION BY event_ingestion_date
CLUSTER BY status, category_titles;
-- ============================================================
-- BRONZE: External Tables
-- Lee archivos Parquet desde Google Cloud Storage.
-- ============================================================

CREATE OR REPLACE EXTERNAL TABLE `mci506-nasa-eonet.eonet_bronze.events_external`
OPTIONS (
  format = 'PARQUET',
  uris = ['gs://mci506-nasa-eonet-bucket/bronze/eonet/events/*']
);

CREATE OR REPLACE EXTERNAL TABLE `mci506-nasa-eonet.eonet_bronze.sources_external`
OPTIONS (
  format = 'PARQUET',
  uris = ['gs://mci506-nasa-eonet-bucket/bronze/eonet/sources/*']
);

CREATE OR REPLACE EXTERNAL TABLE `mci506-nasa-eonet.eonet_bronze.geometry_external`
OPTIONS (
  format = 'PARQUET',
  uris = ['gs://mci506-nasa-eonet-bucket/bronze/eonet/geometry/*']
)
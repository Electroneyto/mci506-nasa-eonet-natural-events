# Arquitectura del Pipeline NASA EONET

Este proyecto usa la API pública NASA EONET para extraer eventos naturales globales y construir un pipeline de datos automatizado.

## Flujo general

NASA EONET API  
→ `scripts/extract.py`  
→ 3 archivos Parquet locales  
→ `scripts/load.py`  
→ Google Cloud Storage - Bronze  
→ BigQuery Bronze / Silver / Gold  
→ Looker Studio

## Estado actual

Hasta este momento el proyecto ya tiene implementada la capa Bronze.

Se extraen datos desde NASA EONET y se generan 3 archivos Parquet:

- `events`
- `sources`
- `geometry`

Luego esos archivos se suben a Google Cloud Storage en las siguientes rutas:

- `bronze/eonet/events/`
- `bronze/eonet/sources/`
- `bronze/eonet/geometry/`

## Próximas fases

Después se trabajará con BigQuery:

- Bronze: tablas externas leyendo desde GCS.
- Silver: tabla limpia y deduplicada.
- Gold: tablas agregadas para análisis.
- Looker Studio: dashboard final.
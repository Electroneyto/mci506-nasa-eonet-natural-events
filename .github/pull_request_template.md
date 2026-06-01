## Descripción del cambio

En este Pull Request se agrega la estructura inicial del proyecto **NASA EONET Natural Events Data Pipeline**.

El objetivo de este primer cambio es dejar preparado el repositorio base para desarrollar el pipeline de datos automatizado usando Python, Google Cloud Storage, BigQuery, GitHub Actions y Looker Studio.

## Parte del proyecto trabajada

- [x] Estructura inicial del proyecto
- [x] Archivos base para scripts Python
- [x] Archivos base para consultas SQL de BigQuery
- [x] Carpeta para documentación y evidencias
- [x] Carpeta para GitHub Actions
- [x] Archivo `.env.example`
- [x] Archivo `requirements.txt`
- [x] Plantilla de Pull Request

## Cambios realizados

Se crearon las carpetas principales del proyecto:

- `scripts/`
- `sql/`
- `docs/`
- `docs/evidence/`
- `docs/dashboard_screenshots/`
- `.github/`
- `.github/workflows/`

También se agregaron los archivos base:

- `scripts/extract.py`
- `scripts/load.py`
- `scripts/utils.py`
- `sql/01_create_external_table.sql`
- `sql/02_create_silver_table.sql`
- `sql/03_silver_transform.sql`
- `sql/04_gold_category_summary.sql`
- `sql/05_gold_daily_events.sql`
- `sql/06_gold_status_summary.sql`
- `sql/07_quality_checks.sql`
- `.github/workflows/pipeline.yml`
- `.github/pull_request_template.md`
- `.env.example`
- `requirements.txt`

## Evidencia de prueba

Se verificó localmente que la estructura del repositorio fue creada correctamente desde VS Code y la terminal.

También se revisó que los archivos base estén organizados según la arquitectura del proyecto:

```text
NASA EONET API
→ Python scripts
→ Google Cloud Storage
→ BigQuery Bronze / Silver / Gold
→ Looker Studio
```

## Checklist antes de hacer merge

- [x] No se subieron credenciales ni archivos JSON de Google Cloud.
- [x] No se subieron archivos `.env`.
- [x] Se agregó `.env.example` con las variables necesarias.
- [x] Se agregó `requirements.txt` con las librerías base del proyecto.
- [x] Se creó la estructura inicial para Python, SQL, documentación y GitHub Actions.
- [x] El cambio deja preparado el repositorio para continuar con la extracción de datos desde NASA EONET.

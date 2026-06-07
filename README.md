# 🌍 NASA EONET Natural Events - Events Data Pipeline

## Descripción del proyecto

Este proyecto implementa un pipeline de datos automatizado y documentado utilizando la API pública NASA EONET como fuente principal.

NASA EONET proporciona información sobre eventos naturales globales, como incendios forestales, tormentas severas, volcanes, inundaciones, hielo, polvo y otros fenómenos ambientales.

El objetivo del proyecto es extraer datos desde una fuente pública, almacenarlos en Google Cloud Storage, procesarlos en BigQuery usando arquitectura Bronze, Silver y Gold, automatizar el flujo con GitHub Actions y BigQuery Scheduled Queries, y visualizar los resultados en Looker Studio.

---

## 📋 Tabla de Contenidos

1. [¿Qué datos extrae?](#-qué-datos-extrae)
2. [¿De dónde los trae?](#-de-dónde-los-trae)
3. [¿A dónde los guarda?](#-a-dónde-los-guarda)
4. [¿Cuándo se ejecuta?](#-cuándo-se-ejecuta)
5. [¿Cómo funciona?](#-cómo-funciona)
6. [¿Cuánta calidad tienen?](#-cuánta-calidad-tienen)
7. [Si falla, qué hacer?](#-si-falla-qué-hacer)
8. [Stack utilizado](#-stack-utilizado)
9. [Estructura del Proyecto](#-estructura-del-proyecto)
10. [Ejecución Local](#-ejecución-local)
11. [Consultas BigQuery](#-consultas-bigquery)
12. [Dashboard Looker Studio](#-dashboard-looker-studio)
13. [Evidencias](#-evidencias)
14. [Accesos requeridos para revisión](#-accesos-requeridos-para-revisión)
15. [Estado final del proyecto](#-estado-final-del-proyecto)
16. [Conclusión](#-conclusión)
17. [Referencias](#-referencias)
18. [Notas Académicas](#-notas-académicas)

---

## 1️⃣ ¿QUÉ datos extrae?

### Dataset: Eventos Naturales Globales

El pipeline extrae información sobre **eventos naturales ocurridos en el planeta** desde la API pública de NASA EONET.

#### Contenido del Dataset

| Característica | Descripción |
|---|---|
| **Fuente** | NASA Earth Observation Natural Event Tracking (EONET) |
| **Eventos incluidos** | Incendios, huracanes, tormentas, inundaciones, erupciones volcánicas, sequías, etc. |
| **Período** | Últimos 365 días (configurable) |
| **Alcance geográfico** | Cobertura global |




#### Entidades Extraídas (3 tablas)

##### 📌 **EVENTS** (Eventos principales)
```
- event_id: Identificador único del evento
- event_name: Nombre descriptivo (ej: "Hurricane Ian")
- category_ids: Categorías del evento (separadas por coma)
- category_titles: Nombres de categorías
- event_status: Estado (Open/Closed)
- event_date: Fecha de inicio
- updated_date: Última actualización
- ingestion_timestamp: Cuándo se extrajo el dato
- ingestion_date: Fecha de ingesta
```

**Ejemplo de registros**: ~2,000-5,000 eventos activos/cerrados según período

---

##### 🗺️ **GEOMETRY** (Ubicaciones espaciales)
```
- geometry_id: ID único de la geometría
- event_id: Referencia al evento
- geometry_type: Point o Polygon
- longitude: Coordenada X
- latitude: Coordenada Y
- geometry_date: Fecha de la observación
- geometry_key: Hash único (evento + fecha + coords) para deduplicación
- source_url: Fuente de la observación
```

**Registros múltiples por evento**: Un evento puede tener varias geometrías según evoluciona temporalmente.

---

##### 📚 **SOURCES** (Proveedores de datos)
```
- source_id: Identificador de la fuente
- event_id: Referencia al evento
- source_url: URL de la fuente
- source_key: Hash único (evento + fuente + URL)
```

**Ejemplo de fuentes**: NASA, NOAA, MODIS, FIRMS, USGS, etc.

---

#### Tipos de Datos
- **Strings**: Nombres, IDs, URLs
- **Timestamps**: Fechas con zona horaria UTC
- **Floats**: Coordenadas geográficas
- **Enums**: Status (Open/Closed), tipos de geometría

---

## 2️⃣ ¿DE DÓNDE los trae?

### Fuente: API Pública NASA EONET v3

#### Endpoint Principal
```
https://eonet.gsfc.nasa.gov/api/v3/events
```

#### Parámetros de Configuración

| Parámetro | Valor por defecto | Descripción |
|---|---|---|
| `status` | `all` | Filtro: `open`, `closed` o `all` |
| `days` | `365` | Últimos N días a consultar |
| `limit` | `5000` | Máximo de registros por request |

**Variables de entorno requeridas**:
```bash
EONET_API_URL=https://eonet.gsfc.nasa.gov/api/v3/events
EONET_STATUS=all
EONET_DAYS=365
EONET_LIMIT=5000
```

#### Características de la API
- ✅ **Pública**: Sin autenticación requerida
- ✅ **Gratuita**: Sin límite de requests
- ✅ **Real-time**: Actualizada diariamente
- ⚠️ **Rate limit handling**: Si recibe 503, espera 15s e reintenta automáticamente

#### Respuesta JSON
La API devuelve:
```json
{
  "events": [
    {
      "id": "EONET_4920",
      "title": "Hurricane Ian",
      "categories": [{"id": "8", "title": "Hurricanes"}],
      "sources": [{"id": "1", "url": "..."}],
      "geometry": [
        {"type": "Point", "date": "2024-01-15T12:00:00Z", "coordinates": [-80.5, 26.1]}
      ]
    }
  ]
}
```

---

## 3️⃣ ¿A DÓNDE los guarda?

### Arquitectura de Almacenamiento

```
┌─────────────────────────────────────────────────────────┐
│  Local (scripts/extract.py)                             │
│  ├─ data/bronze/eonet/events/                           │
│  ├─ data/bronze/eonet/sources/                          │
│  └─ data/bronze/eonet/geometry/                         │
│     └─ eonet_events_YYYYMMDD_HHMMSS.parquet (Parquet)  │
└─────────────────────────────────────────────────────────┘
                        ↓ (Upload)
┌─────────────────────────────────────────────────────────┐
│  Google Cloud Storage (GCS) - BRONZE                    │
│  ├─ gs://YOUR_BUCKET/bronze/eonet/events/              │
│  ├─ gs://YOUR_BUCKET/bronze/eonet/sources/             │
│  └─ gs://YOUR_BUCKET/bronze/eonet/geometry/            │
└─────────────────────────────────────────────────────────┘
                        ↓ (External Tables)
┌─────────────────────────────────────────────────────────┐
│  BigQuery - BRONZE (Tablas Externas)                    │
│  └─ bq-project.eonet.bronze_events                      │
│     bq-project.eonet.bronze_sources                     │
│     bq-project.eonet.bronze_geometry                    │
└─────────────────────────────────────────────────────────┘
```

#### Variables de Entorno Necesarias

```bash
# Google Cloud Platform
GCP_PROJECT_ID=your-project-id
GCS_BUCKET_NAME=your-bucket-name

# BigQuery
BIGQUERY_DATASET=eonet
BIGQUERY_LOCATION=US

# Autenticación (local)
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account-key.json
```

#### Estructura en GCS

```
gs://your-bucket/
└── bronze/eonet/
    ├── events/
    │   ├── eonet_events_20250101_120000.parquet
    │   ├── eonet_events_20250102_120000.parquet
    │   └── ...
    ├── sources/
    │   ├── eonet_sources_20250101_120000.parquet
    │   └── ...
    └── geometry/
        ├── eonet_geometry_20250101_120000.parquet
        └── ...
```

**Características de almacenamiento**:
- 📦 **Formato**: Apache Parquet (comprimido)
- 📅 **Timestamp**: Cada ejecución genera nuevos archivos con timestamp
- 🔄 **Versionado**: Se mantienen históricos para auditoría
- ⚡ **Compresión**: Reduce espacio ~80% vs CSV

---

## 4️⃣ ¿CUÁNDO se ejecuta?

### Ejecución: GitHub Actions (En desarrollo)

#### Schedule Planeado

```yaml
# .github/workflows/eonet-pipeline.yml
schedule:
  - cron: '0 3 * * *'  # Todos los días a las 3 AM UTC
timezone: Etc/UTC
```

**Frecuencia**: Diariamente

**Horario**: 3:00 AM UTC (Equivale a):
- 🇲🇽 10:00 PM día anterior (México)
- 🇪🇸 4:00 AM (España)
- 🇦🇷 12:00 AM (Argentina)

---

#### Fases de Ejecución

```
┌─────────────────────────────────────────────────────────┐
│  1. EXTRACT (scripts/extract.py)                        │
│     ├─ Consultar API NASA EONET                         │
│     ├─ Procesar JSON (flatten, normalizar)              │
│     └─ Generar 3 archivos Parquet locales               │
│     ⏱️ Duración: ~2-5 minutos                            │
│                                                         │
│  2. LOAD (scripts/load.py)                              │
│     ├─ Cargar Parquets a Google Cloud Storage           │
│     └─ Crear/actualizar tablas externas en BigQuery     │
│     ⏱️ Duración: ~1-2 minutos                            │
│                                                         │
│  3. TRANSFORM (BigQuery - SQL)                          │
│     ├─ Silver: Deduplicar y limpiar                     │
│     └─ Gold: Agregar y analizar                         │
│     ⏱️ Duración: ~3-5 minutos                            │
│                                                         │
│  4. VALIDATE (BigQuery - SQL)                           │
│     ├─ Ejecutar quality checks                          │
│     └─ Generar reporte de validación                    │
│     ⏱️ Duración: ~1 minuto                               │
└─────────────────────────────────────────────────────────┘
Total: ~7-13 minutos por ejecución
```

---

#### Ejecución Manual

**Local**:
```bash
# 1. Extract
python scripts/extract.py

# 2. Load
python scripts/load.py
```

**BigQuery** (ejecutar queries en orden):
```bash
# En bq:
bq query --use_legacy_sql=false < sql/01_create_external_table.sql
bq query --use_legacy_sql=false < sql/02_create_silver_table.sql
bq query --use_legacy_sql=false < sql/03_silver_transform.sql
bq query --use_legacy_sql=false < sql/07_quality_checks.sql
```

---

## 5️⃣ ¿CÓMO funciona?

### Arquitectura Medallion: Bronze → Silver → Gold

```
┌────────────────────────────────────────────────────────────────┐
│                    CAPA BRONZE (Raw Data)                      │
│  Datos sin procesar directamente desde NASA EONET              │
│  ├─ Sin deduplicación                                          │
│  ├─ Sin validaciones                                           │
│  ├─ Tipos de datos nativos de la API                           │
│  └─ Tablas externas en GCS                                     │
└────────────────────────────────────────────────────────────────┘
                            ↓ (Transformación)
┌────────────────────────────────────────────────────────────────┐
│                    CAPA SILVER (Clean Data)                    │
│  Datos limpios, validados y deduplicados                       │
│  ├─ Eliminar duplicados (por geometry_key, source_key)         │
│  ├─ Validar tipos de datos                                     │
│  ├─ Normalizar campos                                          │
│  ├─ Calcular campos derivados (ej: centroide de polígonos)     │
│  └─ Tabla consolidada en BigQuery                              │
└────────────────────────────────────────────────────────────────┘
                            ↓ (Agregación)
┌────────────────────────────────────────────────────────────────┐
│                    CAPA GOLD (Analytics)                       │
│  Datos agregados y listo para análisis/dashboards              │
│  ├─ gold_category_summary: Eventos por categoría               │
│  ├─ gold_daily_events: Eventos por día                         │
│  ├─ gold_status_summary: Resumen por estado                    │
│  └─ Optimizado para Looker Studio                              │
└────────────────────────────────────────────────────────────────┘
```

---

### Flujo Detallado

#### 📥 **EXTRACT** - `scripts/extract.py`

**Entrada**: API NASA EONET
**Salida**: 3 DataFrames Parquet

```python
# Paso 1: Consultar API
events_json = requests.get(
    "https://eonet.gsfc.nasa.gov/api/v3/events",
    params={"status": "all", "days": 365}
)

# Paso 2: Normalizar eventos
for event in events_json['events']:
    - Extraer: ID, título, categorías, status, fechas
    - Transformar arrays de categorías en strings (comma-separated)
    - Crear geometry_key y source_key (MD5 hash para dedup)

# Paso 3: Separar entidades (normalización)
events_df = pd.DataFrame([...])      # 1 fila por evento
geometry_df = pd.DataFrame([...])    # N filas si un evento tiene múltiples geometrías
sources_df = pd.DataFrame([...])     # M filas si un evento tiene múltiples fuentes

# Paso 4: Guardar como Parquet
events_df.to_parquet("data/bronze/eonet/events/eonet_events_20250101_120000.parquet")
```

---

#### 🔄 **LOAD** - `scripts/load.py`

**Entrada**: Parquets locales
**Salida**: Tablas en BigQuery (externas desde GCS)

```python
# Paso 1: Buscar últimos Parquets generados
latest_files = find_latest_parquet_by_entity()

# Paso 2: Subir a GCS
for entity in ['events', 'sources', 'geometry']:
    blob = storage.Blob(
        name=f"bronze/eonet/{entity}/eonet_{entity}_20250101_120000.parquet",
        bucket=bucket
    )
    blob.upload_from_filename(f"data/bronze/eonet/{entity}/...")

# Paso 3: Crear tablas externas en BigQuery
CREATE OR REPLACE EXTERNAL TABLE eonet.bronze_events
OPTIONS (
    format = 'PARQUET',
    uris = ['gs://bucket/bronze/eonet/events/*.parquet']
)
```

---

#### 🧹 **TRANSFORM Silver** - `sql/02_create_silver_table.sql` + `sql/03_silver_transform.sql`

**Entrada**: Tablas externas Bronze
**Salida**: Tabla consolidada Silver

**Transformaciones aplicadas**:

1. **Deduplicación**:
   ```sql
   -- Por geometry_key (misma geometría no se repite)
   ROW_NUMBER() OVER (PARTITION BY geometry_key ORDER BY ingestion_timestamp DESC) = 1
   
   -- Por source_key (misma fuente de evento no se repite)
   ROW_NUMBER() OVER (PARTITION BY source_key ORDER BY ingestion_timestamp DESC) = 1
   ```

2. **Normalización**:
   ```sql
   -- Convertir timestamps a TIMESTAMP
   CAST(event_date AS TIMESTAMP) as event_date_clean
   
   -- Validar coordenadas
   WHERE latitude BETWEEN -90 AND 90 
     AND longitude BETWEEN -180 AND 180
   ```

3. **Campos derivados**:
   ```sql
   -- Centroide para polígonos
   ST_CENTROID(ST_GEOGFROMTEXT(geometry)) as geometry_centroid
   
   -- Edad del evento
   DATE_DIFF(CURRENT_DATE(), DATE(event_date), DAY) as event_age_days
   ```

---

#### 📊 **TRANSFORM Gold** - `sql/04_*.sql`

**Entrada**: Silver
**Salida**: Tablas analíticas (gold_*)

**Tablas Gold**:

1. **`gold_category_summary`** - Análisis por categoría
   ```sql
   SELECT
       category_id,
       category_title,
       COUNT(DISTINCT event_id) as num_events,
       COUNT(DISTINCT event_id) FILTER (WHERE event_status = 'Open') as open_events,
       MIN(event_date) as earliest_event,
       MAX(event_date) as latest_event
   FROM silver_events
   GROUP BY category_id, category_title
   ```

2. **`gold_daily_events`** - Serie temporal
   ```sql
   SELECT
       DATE(event_date) as event_day,
       COUNT(DISTINCT event_id) as num_events,
       ARRAY_AGG(DISTINCT event_name) as event_names
   FROM silver_events
   GROUP BY DATE(event_date)
   ORDER BY event_day DESC
   ```

3. **`gold_status_summary`** - Resumen por estado
   ```sql
   SELECT
       event_status,
       COUNT(*) as num_records,
       COUNT(DISTINCT event_id) as num_events
   FROM silver_events
   GROUP BY event_status
   ```

---

## 6️⃣ ¿CUÁNTA CALIDAD tienen?

### Validaciones de Datos - `sql/07_quality_checks.sql`

#### ✅ Checks Implementados

| ID | Validación | Query | Regla |
|---|---|---|---|
| **QC1** | Duplicados en Geometry | `SELECT COUNT(*) - COUNT(DISTINCT geometry_key)` | = 0 |
| **QC2** | Duplicados en Sources | `SELECT COUNT(*) - COUNT(DISTINCT source_key)` | = 0 |
| **QC3** | Valores nulos en IDs | `SELECT COUNT(*) WHERE event_id IS NULL` | = 0 |
| **QC4** | Coordenadas válidas | `WHERE latitude NOT BETWEEN -90 AND 90` | = 0 |
| **QC5** | Rangos de fechas | `WHERE event_date > CURRENT_DATE()` | = 0 |
| **QC6** | Timestamps futuros | `WHERE ingestion_timestamp > CURRENT_TIMESTAMP()` | = 0 |
| **QC7** | Registro de geometrías | `SELECT COUNT(*) FROM silver_events WHERE geometry_id IS NULL` | Revisar |
| **QC8** | Consistency: Events ⊆ Geometry | `SELECT COUNT(DISTINCT event_id) FROM geometry NOT IN (SELECT event_id FROM events)` | = 0 |

---

#### 📈 Ejemplo de Reporte de Calidad

```sql
-- Ejecutar después de cada transformación
SELECT
    'QC1_geometry_duplicates' as check_name,
    COUNT(*) - COUNT(DISTINCT geometry_key) as issue_count,
    CASE 
        WHEN COUNT(*) - COUNT(DISTINCT geometry_key) = 0 THEN 'PASS' 
        ELSE 'FAIL' 
    END as status
FROM silver_geometry
UNION ALL
SELECT
    'QC3_null_event_ids',
    COUNTIF(event_id IS NULL),
    CASE WHEN COUNTIF(event_id IS NULL) = 0 THEN 'PASS' ELSE 'FAIL' END
FROM silver_events
-- ... más checks
```

---

#### 🔍 Métodos de Detección

**Durante EXTRACT**:
```python
# Validar respuesta API antes de crear Parquet
if not response.ok:
    raise APIError(f"API returned {response.status_code}")

# Verificar geometrías válidas
valid_coords = all(
    -90 <= lat <= 90 and -180 <= lng <= 180 
    for lng, lat in geometry['coordinates']
)
```

**Durante LOAD**:
```python
# Verificar que se subieron todos los archivos
assert len(uploaded_blobs) == len(local_files), "Mismatch in uploaded files"
```

**Durante TRANSFORM**:
```sql
-- Silver verifica integridad referencial
SELECT event_id 
FROM geometry_silver 
WHERE event_id NOT IN (SELECT event_id FROM events_silver)
-- Debe devolver 0 registros
```

---

### La calidad de datos se valida mediante la tabla:

```text
eonet_gold.quality_checks
```

Esta tabla contiene validaciones básicas del pipeline.

Validaciones incluidas:

| Validación                     | Descripción                                       |
| ------------------------------ | ------------------------------------------------- |
| `total_rows`                   | Verifica que la tabla Silver tenga datos          |
| `duplicate_event_geometry_key` | Verifica que no existan llaves duplicadas         |
| `null_event_id`                | Verifica que no existan eventos sin identificador |
| `null_coordinates`             | Identifica registros sin latitud o longitud       |
| `future_geometry_dates`        | Verifica que no existan fechas futuras inválidas  |

Los estados posibles son:

```text
PASS
WARNING
FAIL
```

Un estado `PASS` indica que la validación fue superada.
Un estado `WARNING` indica que existe una observación, pero no necesariamente detiene el pipeline.
Un estado `FAIL` indica un problema que debe revisarse.

---


## 7️⃣ ¿SI FALLA qué hacer?

### Plan de Recuperación

#### 🔴 **Tipo 1: Error en EXTRACT (API no responde)**

**Síntomas**:
- `requests.exceptions.ConnectionError`
- `API returned 503 Service Unavailable`

Revisar:

```text
scripts/extract.py
```

Posibles causas:

* La API NASA EONET no responde.
* Error temporal de conexión.
* Cambio en la estructura del JSON.
* Parámetros inválidos.

Acciones:

* Revisar logs de GitHub Actions.
* Ejecutar localmente `python scripts/extract.py`.
* Verificar el endpoint de NASA EONET.
* Confirmar que se generen archivos Parquet.

**Debugging**:
```bash
# 1. Verificar conexión a internet
ping eonet.gsfc.nasa.gov

# 2. Revisar el log de la ejecución
cat github_actions_log.txt

# 3. Verificar status de NASA API
curl -I https://eonet.gsfc.nasa.gov/api/v3/events
```

**Solución**:
- ✅ El código tiene `retry automático` con wait de 15s
- ✅ Si persiste, GitHub Actions reintenta en 1 hora
- ❌ Si falla 3 veces: revisar estado del servidor NASA en https://api.nasa.gov

---

#### 🔴 **Tipo 2: Error en LOAD (Permiso en GCS)**

**Síntomas**:
- `google.auth.exceptions.DefaultCredentialsError`
- `Permission denied: gs://bucket/bronze/...`

Revisar:

```text
scripts/load.py
```

Posibles causas:

* El bucket no existe.
* La Service Account no tiene permisos.
* El secret `GCP_SA_KEY` está mal configurado.
* La variable `GCS_BUCKET_NAME` es incorrecta.

Acciones:

* Revisar GitHub Secrets.
* Verificar permisos de la Service Account.
* Ejecutar localmente `python scripts/load.py`.
* Confirmar que existan archivos en `data/bronze/eonet/`.


**Debugging**:
```bash
# 1. Verificar credenciales
echo $GOOGLE_APPLICATION_CREDENTIALS
cat $GOOGLE_APPLICATION_CREDENTIALS | head -5

# 2. Probar acceso a bucket
gsutil ls gs://your-bucket/

# 3. Revisar permisos del service account
gcloud projects get-iam-policy YOUR_PROJECT \
  --flatten="bindings[].members" \
  --filter="bindings.members:serviceAccount@iam.gserviceaccount.com"
```

**Solución**:
```bash
# Renovar credenciales
gcloud auth application-default login

# O usar service account en GitHub Secrets
echo ${{ secrets.GCP_SA_KEY }} > key.json
export GOOGLE_APPLICATION_CREDENTIALS=key.json
```

---

#### 🔴 **Tipo 3: Error en TRANSFORM (Datos inválidos en BigQuery)**

**Síntomas**:
- `Invalid field type: geometry expected STRING got INT64`
- Queries SQL tardan > 10 minutos
- `Quota exceeded: 1000 concurrent queries`

Revisar los archivos SQL:

```text
sql/01_create_external_table.sql
sql/02_create_silver_table.sql
sql/03_silver_transform.sql
sql/04_gold_category_summary.sql
sql/05_gold_daily_events.sql
sql/06_gold_status_summary.sql
sql/07_quality_checks.sql
sql/08_scheduled_refresh.sql
```

Posibles causas:

* Error en rutas de GCS.
* External Tables sin acceso a archivos.
* Cambios en el esquema de los Parquet.
* Problemas de permisos en BigQuery.
* Scheduled Query desactivada o con errores.

Acciones:

* Ejecutar manualmente el SQL con error.
* Revisar el historial de ejecuciones de la Scheduled Query.
* Validar conteos de Bronze, Silver y Gold.
* Revisar la tabla `quality_checks`.


**Debugging**:
```bash
# 1. Inspeccionar esquema de tablas
bq show --schema eonet.bronze_events

# 2. Ejecutar quality check
bq query --use_legacy_sql=false < sql/07_quality_checks.sql

# 3. Ver últimos errores
bq ls -j -a | head -10
bq wait JOB_ID
```

**Solución**:
```sql
-- Recrear tabla bronze con tipos correctos
DROP TABLE IF EXISTS eonet.bronze_events;

CREATE OR REPLACE EXTERNAL TABLE eonet.bronze_events (
    event_id STRING,
    event_name STRING,
    event_date TIMESTAMP,
    longitude FLOAT64,
    latitude FLOAT64
)
OPTIONS (
    format = 'PARQUET',
    uris = ['gs://bucket/bronze/eonet/events/*.parquet']
);
```

---

#### 🔴 **Tipo 4: Datos inconsistentes (Validation FAIL)**

**Síntomas**:
```
QC1_geometry_duplicates: FAIL (500 duplicates found)
QC4_invalid_coordinates: FAIL (25 records outside range)
```

**Debugging**:
```sql
-- Identificar duplicados
SELECT 
    geometry_key, 
    COUNT(*) as cnt
FROM silver_geometry
GROUP BY geometry_key
HAVING cnt > 1
ORDER BY cnt DESC;

-- Identificar coords inválidas
SELECT *
FROM silver_geometry
WHERE latitude NOT BETWEEN -90 AND 90
   OR longitude NOT BETWEEN -180 AND 180;
```

**Solución**:
```sql
-- Opción 1: Descartar duplicados (RECOMENDADO)
CREATE OR REPLACE TABLE eonet.silver_geometry AS
SELECT 
    * EXCEPT(rn)
FROM (
    SELECT *,
        ROW_NUMBER() OVER (PARTITION BY geometry_key ORDER BY ingestion_timestamp DESC) as rn
    FROM eonet.silver_geometry
)
WHERE rn = 1;

-- Opción 2: Investigar fuente de duplicados
SELECT event_id, ingestion_timestamp, COUNT(*)
FROM silver_geometry
WHERE geometry_key IN (...)
GROUP BY event_id, ingestion_timestamp;
```

---

#### 📋 **Checklist de Recuperación**

```markdown
## Si el pipeline falla:

- [ ] ¿Cuál es el error exacto? (revisar GitHub Actions log)
- [ ] ¿En qué fase falló? (Extract / Load / Transform)
- [ ] ¿Cuándo fue la última ejecución exitosa?
- [ ] ¿Hay datos parciales en GCS?

## Acciones:

- [ ] 1. Revisar logs en: GitHub → Actions → Pipeline run
- [ ] 2. Ejecutar manualmente: `python scripts/extract.py`
- [ ] 3. Si extract OK → probar `python scripts/load.py`
- [ ] 4. Si load OK → ejecutar quality checks en BigQuery
- [ ] 5. Si quality checks fallan → ejecutar Tipo 4 (arriba)
- [ ] 6. Si todo OK pero dashboard vacío → revisar tabla GOLD

## Contacto

- 📧 Para errores de API NASA: support@nasa.gov
- 🔧 Para errores de GCP: revisar IAM del service account
- 📊 Para errores de BigQuery: revisar limites de API (quota)
```

---


#### 🔴 **Tipo 5: Fallo en Looker Studio (Dashboard vacío)**

**Síntomas**:
- Dashboard sin datos o tarjetas vacías
- Conexión a fuente de datos mostrada como "Desconectada"
- Errores de permisos al intentar refrescar campos

Revisar:

```text
Looker Studio → Dashboard → Fuente de datos → Estado
```

Posibles causas:

* Tablas Gold vacías o sin datos.
* Campos nuevos no actualizados en Looker Studio.
* Permisos insuficientes para acceder a BigQuery.
* Fuente de datos desconectada.
* Queries Gold retornando 0 registros.

Acciones:

* Refrescar campos en Looker Studio (Fuente de datos → Actualizar campos).
* Revisar permisos de acceso en BigQuery IAM.
* Confirmar que las tablas Gold tengan datos ejecutando:
  ```sql
  SELECT COUNT(*) as num_records FROM eonet.gold_category_summary;
  SELECT COUNT(*) as num_records FROM eonet.gold_daily_events;
  SELECT COUNT(*) as num_records FROM eonet.gold_status_summary;
  ```
* Validar que el dashboard use las tablas Gold correctas.
* Ejecutar Scheduled Query manualmente en BigQuery.

**Debugging**:
```bash
# 1. Verificar que las tablas existen
bq ls -t eonet

# 2. Contar registros en Gold
bq query --use_legacy_sql=false 'SELECT COUNT(*) FROM eonet.gold_category_summary'

# 3. Revisar permisos de usuario en Looker Studio
# (Dashboard → Compartir → Verificar que tengas Editor o Propietario)

# 4. Revisar logs de Scheduled Query
bq ls -j -a | grep scheduled
```

**Solución**:
```sql
-- Si las tablas Gold están vacías, regenerarlas
BEGIN
  CREATE OR REPLACE TABLE eonet.gold_category_summary AS
  SELECT category_id, category_title, COUNT(*) as num_events
  FROM eonet.silver_events
  GROUP BY category_id, category_title;
  
  CREATE OR REPLACE TABLE eonet.gold_daily_events AS
  SELECT DATE(event_date) as event_day, COUNT(*) as num_events
  FROM eonet.silver_events
  GROUP BY DATE(event_date)
  ORDER BY event_day DESC;
  
  CREATE OR REPLACE TABLE eonet.gold_status_summary AS
  SELECT event_status, COUNT(*) as num_records
  FROM eonet.silver_events
  GROUP BY event_status;
END;

-- Luego en Looker Studio: Fuente de datos → "Actualizar campos"
```

---



### 🛠️ Monitoreo Proactivo

#### Logs Importantes

```bash
# GitHub Actions
https://github.com/YOUR_REPO/actions

# Cloud Logging (GCP)
gcloud logging read "resource.type=bigquery_project" --limit 50

# Local logs
tail -f logs/extract_*.log
tail -f logs/load_*.log
```

#### Alertas Recomendadas

```yaml
# En Cloud Monitoring (GCP)
- Alerta si Query BigQuery tarda > 5 minutos
- Alerta si GCS upload falla
- Alerta si quality check retorna FAIL
```



## 📁 Estructura del Proyecto

```
mci506-nasa-eonet-natural-events/
├── README.md                          # Este archivo
├── requirements.txt                   # Dependencias Python
├── utils.py                          # Funciones compartidas
│
├── scripts/                          # Scripts de ejecución
│   ├── extract.py                    # Extraer desde API NASA
│   ├── load.py                       # Cargar a GCS/BigQuery
│   └── utils.py                      # Helpers (keys, centroides)
│
├── sql/                              # Queries BigQuery
│   ├── 01_create_external_table.sql  # Tablas externas (Bronze)
│   ├── 02_create_silver_table.sql    # Crear tabla Silver
│   ├── 03_silver_transform.sql       # Transformaciones Silver
│   ├── 04_gold_category_summary.sql  # Vista Gold 1
│   ├── 05_gold_daily_events.sql      # Vista Gold 2
│   ├── 06_gold_status_summary.sql    # Vista Gold 3
│   └── 07_quality_checks.sql         # Validaciones
│
├── docs/                             # Documentación
│   ├── architecture.md               # Diagramas arquitectura
│   └── evidence/                     # Screenshots/evidencia
│
└── data/                             # (Local, no commiteado)
    └── bronze/eonet/
        ├── events/
        ├── sources/
        └── geometry/
```

---

## 8️⃣ STACK utilizado

El proyecto utiliza el stack obligatorio del módulo:

| Herramienta          | Uso                                 | Versión/Detalles |
| -------------------- | ----------------------------------- | ------ |
| **Python**           | Extracción y carga de datos         | 3.9+ |
| **Google Cloud Storage** | Almacenamiento Bronze (Raw data) | GCS Buckets |
| **BigQuery**         | Procesamiento Bronze, Silver y Gold | Dataset: eonet |
| **GitHub Actions**   | Orquestación de extracción y carga  | Workflow + Scheduled Queries |
| **Looker Studio**    | Visualización interactiva           | Dashboards conectadas a Gold |
| **GitHub**           | Control de versiones y colaboración | Repositorio mci506 |
| **Apache Parquet**   | Formato de serialización           | Compresión snappy |
| **Pandas**           | Transformación de DataFrames       | Python library |
| **Google Cloud SDK** | CLI para GCP                       | gcloud + bq CLI |

---

## 📁 Estructura del Proyecto

```
mci506-nasa-eonet-natural-events/
├── README.md                          # Este archivo
├── requirements.txt                   # Dependencias Python
├── utils.py                          # Funciones compartidas
│
├── scripts/                          # Scripts de ejecución
│   ├── extract.py                    # Extraer desde API NASA
│   ├── load.py                       # Cargar a GCS/BigQuery
│   └── utils.py                      # Helpers (keys, centroides)
│
├── sql/                              # Queries BigQuery
│   ├── 01_create_external_table.sql  # Tablas externas (Bronze)
│   ├── 02_create_silver_table.sql    # Crear tabla Silver
│   ├── 03_silver_transform.sql       # Transformaciones Silver
│   ├── 04_gold_category_summary.sql  # Vista Gold 1
│   ├── 05_gold_daily_events.sql      # Vista Gold 2
│   ├── 06_gold_status_summary.sql    # Vista Gold 3
│   └── 07_quality_checks.sql         # Validaciones
│
├── docs/                             # Documentación
│   ├── architecture.md               # Diagramas arquitectura
│   └── evidence/                     # Screenshots/evidencia
│
└── data/                             # (Local, no commiteado)
    └── bronze/eonet/
        ├── events/
        ├── sources/
        └── geometry/
```

---

## 💻 Ejecución Local

### Prerequisitos

Asegurar que tienes configuradas las variables de entorno:

```bash
# Google Cloud Platform
export GCP_PROJECT_ID="your-project-id"
export GCS_BUCKET_NAME="your-bucket-name"
export BIGQUERY_DATASET="eonet"
export BIGQUERY_LOCATION="US"

# Autenticación
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account-key.json"
```

### Ejecutar Pipeline Localmente (DEPRECATED - Ver Sección 10 Ejecución Local)

## � Ejecución Local

### 1️⃣ Crear entorno virtual

```bash
python -m venv .venv
```

Activar entorno virtual en Windows:

```bash
.venv\Scripts\activate
```

En Linux/Mac:

```bash
source .venv/bin/activate
```

### 2️⃣ Instalar dependencias

```bash
pip install -r requirements.txt
```

### 3️⃣ Ejecutar extracción

Extrae datos desde la API NASA EONET y genera archivos Parquet locales:

```bash
python scripts/extract.py
```

**Salida esperada:**
```
data/bronze/eonet/events/eonet_events_20250101_120000.parquet
data/bronze/eonet/sources/eonet_sources_20250101_120000.parquet
data/bronze/eonet/geometry/eonet_geometry_20250101_120000.parquet
```

### 4️⃣ Ejecutar carga a GCS/BigQuery

Carga los Parquets a Google Cloud Storage y crea tablas externas en BigQuery:

```bash
python scripts/load.py
```

### 5️⃣ Ejecutar transformaciones en BigQuery

Ejecutar los SQL en el orden especificado (ver sección siguiente)

---

## 🔍 Consultas BigQuery

### Ejecución manual de transformaciones

Los SQL deben ejecutarse en el siguiente orden para crear la arquitectura completa:

```bash
bq query --use_legacy_sql=false < sql/01_create_external_table.sql
bq query --use_legacy_sql=false < sql/02_create_silver_table.sql
bq query --use_legacy_sql=false < sql/03_silver_transform.sql
bq query --use_legacy_sql=false < sql/04_gold_category_summary.sql
bq query --use_legacy_sql=false < sql/05_gold_daily_events.sql
bq query --use_legacy_sql=false < sql/06_gold_status_summary.sql
bq query --use_legacy_sql=false < sql/07_quality_checks.sql
```

### Descripción de cada paso

| # | Script | Propósito |
|---|--------|----------|
| 1 | `01_create_external_table.sql` | Crear tablas externas en BigQuery que leen desde GCS (Bronze) |
| 2 | `02_create_silver_table.sql` | Crear estructura de tabla Silver (datos limpios) |
| 3 | `03_silver_transform.sql` | Ejecutar transformaciones y deduplicación (Bronze → Silver) |
| 4 | `04_gold_category_summary.sql` | Crear tabla agregada por categoría |
| 5 | `05_gold_daily_events.sql` | Crear serie temporal diaria |
| 6 | `06_gold_status_summary.sql` | Crear resumen por estado del evento |
| 7 | `07_quality_checks.sql` | Ejecutar validaciones de calidad |

---

## 📊 Dashboard Looker Studio

El dashboard fue desarrollado en Looker Studio usando las tablas Gold de BigQuery.

### Fuentes utilizadas

```text
eonet_gold.gold_category_summary
eonet_gold.gold_daily_events
eonet_gold.gold_status_summary
eonet_gold.quality_checks
```

### Visualizaciones incluidas

* Eventos naturales por categoría.
* Eventos naturales por día.
* Eventos abiertos y cerrados.
* Filtro por categoría (ej: Wildfires).
* Validaciones de calidad de datos.

### Link del dashboard

```text
https://datastudio.google.com/reporting/4548d662-e099-4494-bc01-2bb8290ee4ad
```

Las evidencias del dashboard se encuentran en:

```text
docs/dashboard_screenshots/
```

---

## 📸 Evidencias

El repositorio contiene evidencias del proyecto en:

```text
docs/evidence/
docs/dashboard_screenshots/
```

Estas evidencias incluyen:

* Carga de archivos en Google Cloud Storage.
* Estructura Bronze en GCS.
* Datasets y tablas en BigQuery.
* Pull Requests del equipo.
* GitHub Actions.
* Scheduled Query.
* Dashboard en Looker Studio.

---

## 🔐 Accesos requeridos para revisión

El repositorio debe estar configurado como público.

### Acceso GitHub

```text
Usuario: auzaluis
Rol: Collaborator
```

### Acceso Google Cloud

```text
Correo: luis.auza@gmail.com
Rol: Editor
```

---

## ✅ Estado final del proyecto

El proyecto cuenta con un pipeline funcional que:

1. Extrae datos desde la API pública NASA EONET.
2. Genera archivos Parquet separados en `events`, `sources` y `geometry`.
3. Sube los archivos a Google Cloud Storage en la capa Bronze.
4. Crea tablas externas en BigQuery para leer los archivos desde GCS.
5. Procesa y deduplica los datos en la capa Silver.
6. Genera tablas Gold para análisis y visualización.
7. Automatiza la extracción y carga mediante GitHub Actions.
8. Automatiza la actualización de Silver y Gold mediante BigQuery Scheduled Query.
9. Visualiza los resultados en Looker Studio mediante tablas Gold.

---

## 🎯 Conclusión

El proyecto implementa una arquitectura de datos completa usando Python, Google Cloud Storage, BigQuery, GitHub Actions, BigQuery Scheduled Queries y Looker Studio.

La solución permite extraer eventos naturales desde NASA EONET, almacenarlos en una capa Bronze, transformarlos en Silver, generar tablas Gold para análisis y presentar los resultados en un dashboard interactivo.

---

## �📚 Referencias

- 🌍 [NASA EONET API Docs](https://eonet.gsfc.nasa.gov/docs/v3)
- 🔧 [Google Cloud Storage Docs](https://cloud.google.com/storage/docs)
- 📊 [BigQuery Docs](https://cloud.google.com/bigquery/docs)
- 📦 [Apache Parquet Format](https://parquet.apache.org/)
- 📊 [Looker Studio Docs](https://support.google.com/looker-studio)
- 🔄 [GitHub Actions Documentation](https://docs.github.com/en/actions)

---

## 👨‍🎓 Notas Académicas

Este proyecto demuestra:
- ✅ Integración con APIs públicas
- ✅ ETL automated con Python
- ✅ Data warehouse design (medallion architecture)
- ✅ Quality assurance en datos
- ✅ IaC y CI/CD con GitHub Actions
- ✅ Cloud infrastructure (GCS + BigQuery)
- ✅ Visualización de datos en tiempo real
- ✅ Monitoreo y troubleshooting de pipelines



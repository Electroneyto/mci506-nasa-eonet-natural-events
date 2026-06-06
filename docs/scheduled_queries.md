# Scheduled Query - BigQuery

Este documento describe la consulta programada utilizada para actualizar automáticamente las capas Silver y Gold del proyecto NASA EONET.

## Objetivo

La consulta programada permite que BigQuery actualice las tablas procesadas después de que GitHub Actions cargue nuevos archivos Parquet en Google Cloud Storage.

El flujo automatizado queda de la siguiente forma:

```text
GitHub Actions
→ Extrae datos desde NASA EONET
→ Genera archivos Parquet
→ Sube los archivos a Google Cloud Storage

BigQuery Scheduled Query
→ Lee las External Tables de Bronze
→ Actualiza la tabla Silver
→ Regenera las tablas Gold
→ Actualiza los quality checks

Looker Studio
→ Consume las tablas Gold actualizadas
```

## Archivo SQL utilizado

La consulta programada utiliza el siguiente archivo del repositorio:

```text
sql/08_scheduled_refresh.sql
```

## Nombre de la consulta programada

```text
refresh_eonet_silver_gold
```

## Frecuencia de ejecución

La consulta fue configurada para ejecutarse diariamente.

```text
Frecuencia: diaria
Hora: 03:30 UTC
Finalización: sin fecha de finalización programada
```

## Tablas actualizadas

La Scheduled Query actualiza las siguientes tablas:

```text
eonet_silver.events
eonet_gold.gold_category_summary
eonet_gold.gold_daily_events
eonet_gold.gold_status_summary
eonet_gold.quality_checks
```

## Descripción del proceso

Primero, la consulta inserta nuevos registros en la tabla Silver:

```text
eonet_silver.events
```

La inserción es incremental y evita duplicados usando la llave:

```text
event_geometry_key
```

Luego, la consulta regenera las tablas Gold con `CREATE OR REPLACE TABLE`, asegurando que el dashboard siempre consuma datos actualizados.

## Relación con GitHub Actions

GitHub Actions se encarga de ejecutar:

```text
scripts/extract.py
scripts/load.py
```

Eso permite extraer datos desde NASA EONET y subir los archivos Parquet a Google Cloud Storage.

Después, la Scheduled Query toma esos datos desde BigQuery Bronze y actualiza Silver y Gold.

## Relación con Looker Studio

Looker Studio no ejecuta Python ni SQL directamente. El dashboard consume las tablas Gold de BigQuery:

```text
eonet_gold.gold_category_summary
eonet_gold.gold_daily_events
eonet_gold.gold_status_summary
eonet_gold.quality_checks
```

Cuando la Scheduled Query actualiza las tablas Gold, el dashboard puede mostrar los datos actualizados.

## Evidencia

La consulta programada fue creada en BigQuery con la siguiente configuración:

```text
Nombre: refresh_eonet_silver_gold
Frecuencia: diaria
Hora: 03:30 UTC
Sin fecha de finalización programada
Sin tabla destino adicional
```

No se configuró una tabla destino adicional porque el propio SQL ya define las tablas de destino mediante:

```text
INSERT INTO
CREATE OR REPLACE TABLE
```

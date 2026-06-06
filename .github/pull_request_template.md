## 📊 Descripción del cambio
Creación de dashboard analítico en Looker Studio con visualizaciones y evidencias de los datos Gold de BigQuery.

## 🎯 Objetivo
Desarrollar un dashboard interactivo que visualice los datos procesados del pipeline NASA EONET desde las tablas Gold.

## ✨ Cambios Realizados en carpeta `docs/dashboard_screenshots/`

### 1. Dashboard Looker Studio
- Dashboard interactivo conectado a tablas Gold de BigQuery:
  - `eonet_gold.gold_category_summary`
  - `eonet_gold.gold_daily_events`
  - `eonet_gold.gold_status_summary`
  - `eonet_gold.quality_checks`

### 2. Visualizaciones Incluidas
- **Eventos por categoría** - Resumen de eventos naturales agrupados por tipo (Wildfires, Huracanes, etc.)
- **Eventos por día** - Serie temporal de eventos desde tabla Gold
- **Estado de eventos** - Conteo de eventos abiertos vs cerrados
- **Filtros interactivos** - Filtro dinámico por categoría para análisis detallado
- **Validaciones de calidad** - Tabla con status de quality checks

### 3. Evidencias Documentadas
- `01_looker_dashboard_general.png` - Vista general del dashboard
- `02_looker_category_filter.png` - Filtro por categoría aplicado
- `03_looker_daily_events.png` - Gráfico de eventos por día
- `04_looker_status_summary.png` - Eventos abiertos y cerrados
- `05_looker_quality_checks.png` - Tabla de validaciones de datos

### 4. Documentación
- `readme_dashboard.md` - Explicación técnica del dashboard y fuentes de datos
- Link al dashboard: https://datastudio.google.com/s/v_kGf_RZJyo

## � Impacto
- **Visualización**: Dashboard interactivo para análisis de eventos naturales en tiempo real
- **Trazabilidad**: Evidencia visual de la capa Gold del data warehouse
- **Insights**: Análisis rápido de eventos por categoría, fecha y estado
- **Documentación**: Referencias claras a las fuentes de datos en BigQuery

## ✅ Validación
- [x] README válido en Markdown
- [x] Links internos funcionan
- [x] Variables de entorno documentadas
- [x] Estructura de carpetas clara
- [x] Ejemplos de código correctos
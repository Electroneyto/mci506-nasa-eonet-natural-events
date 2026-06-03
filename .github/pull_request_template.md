## Descripcion del cambio

## 🎯 Objetivo
Generar documentación completa y educativa del pipeline de datos NASA EONET 
que responda a las 7 preguntas clave de ingeniería de datos.

## ✨ Cambios Realizados

### 1. README.md Expandido (+823 líneas)
Se reescribió completamente el README con:

#### Secciones Principales (7 preguntas):
- **¿QUÉ datos extrae?** 
  - 3 entidades: EVENTS (~2-5k registros), GEOMETRY (coords), SOURCES (proveedores)
  - Especificación de campos, tipos de datos, ejemplos

- **¿DE DÓNDE los trae?**
  - Endpoint NASA EONET v3 con parámetros configurables
  - Manejo de rate limits y reintentos automáticos

- **¿A DÓNDE los guarda?**
  - Arquitectura GCS → BigQuery con estructura de carpetas
  - Variables de entorno requeridas (GCP_PROJECT_ID, GCS_BUCKET_NAME, etc.)

- **¿CUÁNDO se ejecuta?**
  - Schedule GitHub Actions: Diariamente a las 3 AM UTC
  - Fases: Extract (2-5 min) → Load (1-2 min) → Transform (3-5 min)

- **¿CÓMO funciona?**
  - Arquitectura Medallion completa (Bronze → Silver → Gold)
  - Flujo detallado de EXTRACT, LOAD, TRANSFORM con código de ejemplo
  - Deduplicación con geometry_key y source_key (hashes MD5)

- **¿CUÁNTA CALIDAD tienen?**
  - 8 quality checks: duplicados, nulos, rangos, integridad referencial
  - Queries SQL de ejemplo para detección de problemas

- **¿SI FALLA qué hacer?**
  - Plan de recuperación para 4 tipos de errores (API, Permisos, BigQuery, Datos)
  - Debugging steps y checklist de recuperación

#### Características Adicionales:
- Tabla de contenidos con links internos
- Diagramas ASCII del flujo de datos
- Ejemplos de código Python y SQL
- Estructura del proyecto documentada
- Guía de inicio rápido
- Referencias a documentación oficial

### 2. .env.example
- Creado archivo de template para variables de entorno
- Facilita setup inicial para nuevos desarrolladores

### 3. Formato de Archivos
- `docs/architecture.md.txt` → `docs/architecture.md` (formato correcto)
- `docs/evidence/README.md.txt` → `docs/evidence/README.md` (formato correcto)

## 🎓 Contexto Académico
Este proyecto es del Módulo 5 - Ingeniería de Datos de la Maestría en Ciencia de Datos.
La documentación demuestra:
- ✅ Integración con APIs públicas
- ✅ ETL automatizado con Python
- ✅ Diseño de data warehouse (medallion architecture)
- ✅ Quality assurance en datos
- ✅ Infrastructure as Code con GitHub Actions
- ✅ Cloud infrastructure (GCS + BigQuery)

## 📊 Impacto
- **Onboarding**: Nueva documentación facilita que otros estudiantes entiendan el proyecto
- **Mantenibilidad**: Especificación clara de arquitectura y flujos
- **Debugging**: Plan de recuperación detallado para casos de falla
- **Educativo**: Ejemplos prácticos de cada componente del pipeline

## ✅ Validación
- [x] README válido en Markdown
- [x] Links internos funcionan
- [x] Variables de entorno documentadas
- [x] Estructura de carpetas clara
- [x] Ejemplos de código correctos
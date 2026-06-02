import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List

from dotenv import load_dotenv
from google.cloud import storage


load_dotenv()


LOCAL_BRONZE_PATH = Path("data/bronze/eonet")
GCS_BRONZE_PREFIX = "bronze/eonet"
EXPECTED_ENTITIES = ["events", "sources", "geometry"]


def get_bucket_name() -> str:
    """
    Obtiene el nombre del bucket desde la variable de entorno GCS_BUCKET_NAME.
    """
    bucket_name = os.getenv("GCS_BUCKET_NAME")

    if not bucket_name:
        raise ValueError("La variable de entorno GCS_BUCKET_NAME no está configurada.")

    return bucket_name


def get_project_id() -> str:
    """
    Obtiene el ID del proyecto GCP desde la variable de entorno GCP_PROJECT_ID.
    """
    project_id = os.getenv("GCP_PROJECT_ID")

    if not project_id:
        raise ValueError("La variable de entorno GCP_PROJECT_ID no está configurada.")

    return project_id


def find_latest_parquet_by_entity() -> Dict[str, Path]:
    """
    Busca el archivo Parquet más reciente para cada entidad esperada.

    Entidades esperadas:
    - events
    - sources
    - geometry

    Ejemplo de estructura local:
    data/bronze/eonet/events/eonet_events_YYYYMMDD_HHMMSS.parquet
    data/bronze/eonet/sources/eonet_sources_YYYYMMDD_HHMMSS.parquet
    data/bronze/eonet/geometry/eonet_geometry_YYYYMMDD_HHMMSS.parquet
    """
    if not LOCAL_BRONZE_PATH.exists():
        raise FileNotFoundError(
            f"No existe la carpeta {LOCAL_BRONZE_PATH}. "
            "Ejecuta primero scripts/extract.py."
        )

    latest_files: Dict[str, Path] = {}

    for entity in EXPECTED_ENTITIES:
        entity_path = LOCAL_BRONZE_PATH / entity

        if not entity_path.exists():
            raise FileNotFoundError(
                f"No existe la carpeta {entity_path}. "
                "Verifica que extract.py haya generado los Parquets correctamente."
            )

        parquet_files = list(entity_path.glob("*.parquet"))

        if not parquet_files:
            raise FileNotFoundError(
                f"No se encontraron archivos Parquet en {entity_path}."
            )

        latest_file = max(parquet_files, key=lambda file_path: file_path.stat().st_mtime)
        latest_files[entity] = latest_file

    return latest_files


def build_gcs_destination_path(entity: str, local_file_path: Path) -> str:
    """
    Construye la ruta destino en Google Cloud Storage.

    Ejemplo:
    bronze/eonet/events/ingestion_date=2026-06-01/eonet_events_20260601_030000.parquet
    """
    ingestion_date = datetime.now(timezone.utc).date().isoformat()

    destination_path = (
        f"{GCS_BRONZE_PREFIX}/{entity}/"
        f"ingestion_date={ingestion_date}/"
        f"{local_file_path.name}"
    )

    return destination_path


def upload_file_to_gcs(
    bucket: storage.Bucket,
    entity: str,
    local_file_path: Path,
) -> str:
    """
    Sube un archivo Parquet local a Google Cloud Storage.
    """
    destination_path = build_gcs_destination_path(entity, local_file_path)

    blob = bucket.blob(destination_path)
    blob.upload_from_filename(str(local_file_path))

    return destination_path


def upload_latest_parquets_to_gcs() -> None:
    """
    Sube a GCS los últimos archivos Parquet generados para events, sources y geometry.
    """
    bucket_name = get_bucket_name()
    project_id = get_project_id()
    latest_files = find_latest_parquet_by_entity()

    client = storage.Client(project=project_id)
    bucket = client.bucket(bucket_name)

    print(f"Proyecto GCP: {project_id}")
    print(f"Bucket destino: gs://{bucket_name}")
    print(f"Entidades encontradas: {list(latest_files.keys())}")

    for entity, local_file_path in latest_files.items():
        destination_path = upload_file_to_gcs(
            bucket=bucket,
            entity=entity,
            local_file_path=local_file_path,
        )

        print(
            f"Archivo subido correctamente: "
            f"{local_file_path} -> gs://{bucket_name}/{destination_path}"
        )


def main() -> None:
    """
    Ejecuta la carga de archivos Parquet a Google Cloud Storage.
    """
    upload_latest_parquets_to_gcs()
    print("Carga a Google Cloud Storage finalizada correctamente.")


if __name__ == "__main__":
    main()
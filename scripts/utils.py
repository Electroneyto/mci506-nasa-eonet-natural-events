import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional, Tuple

import pandas as pd


def build_event_geometry_key(
    event_id: str,
    geometry_date: str,
    longitude: Any,
    latitude: Any,
) -> str:
    """
    Construye una llave única para identificar cada combinación de evento,
    fecha de geometría y coordenadas.

    Esta llave se usará después en BigQuery para evitar duplicados en Silver.
    """
    raw_key = f"{event_id}|{geometry_date}|{longitude}|{latitude}"
    return hashlib.md5(raw_key.encode("utf-8")).hexdigest()


def build_event_source_key(
    event_id: str,
    source_id: str,
    source_url: str,
) -> str:
    """
    Construye una llave única para identificar la relación entre un evento
    y una fuente de información.
    """
    raw_key = f"{event_id}|{source_id}|{source_url}"
    return hashlib.md5(raw_key.encode("utf-8")).hexdigest()


def get_polygon_centroid(coordinates: Any) -> Tuple[Optional[float], Optional[float]]:
    """
    Calcula un centroide simple para geometrías Polygon.

    NASA EONET puede devolver geometrías tipo Point o Polygon.
    Para el dashboard, necesitamos una longitud y latitud representativa.
    """
    try:
        points = coordinates[0]

        longitudes = [point[0] for point in points if isinstance(point, list) and len(point) >= 2]
        latitudes = [point[1] for point in points if isinstance(point, list) and len(point) >= 2]

        if not longitudes or not latitudes:
            return None, None

        longitude = sum(longitudes) / len(longitudes)
        latitude = sum(latitudes) / len(latitudes)

        return longitude, latitude

    except Exception:
        return None, None


def save_to_parquet(df: pd.DataFrame, entity_name: str) -> Path:
    """
    Guarda un DataFrame como archivo Parquet local en la capa Bronze.

    Cada entidad se guarda en su propia carpeta:

    - data/bronze/eonet/events/
    - data/bronze/eonet/sources/
    - data/bronze/eonet/geometry/

    Esta estructura luego se replica en Google Cloud Storage.
    """
    output_dir = Path(f"data/bronze/eonet/{entity_name}")
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    output_path = output_dir / f"eonet_{entity_name}_{timestamp}.parquet"

    df.to_parquet(output_path, index=False)

    return output_path
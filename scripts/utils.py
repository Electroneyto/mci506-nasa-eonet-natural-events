
import hashlib
from typing import Any, Optional, Tuple
import pandas as pd
from pathlib import Path
from datetime import datetime, timezone

def build_event_geometry_key(
    event_id: str,
    geometry_date: str,
    longitude: Any,
    latitude: Any,
) -> str:
    """
    Construye una llave única para identificar cada combinación de evento,
    categoría, fecha de geometría y coordenadas.

    Esta llave se usará después en BigQuery para evitar duplicados en Silver.
    """
    raw_key = f"{event_id}|{geometry_date}|{longitude}|{latitude}"
    return hashlib.md5(raw_key.encode("utf-8")).hexdigest()


def get_polygon_centroid(coordinates: Any) -> Tuple[Optional[float], Optional[float]]:
    """
    Calcula un centroide simple para geometrías Polygon.

    NASA EONET puede devolver geometrías tipo Point o Polygon.
    Para el dashboard, necesitamos una latitud y longitud representativa.
    """
    try:
        points = coordinates[0]

        longitudes = [point[0] for point in points if len(point) >= 2]
        latitudes = [point[1] for point in points if len(point) >= 2]

        if not longitudes or not latitudes:
            return None, None

        longitude = sum(longitudes) / len(longitudes)
        latitude = sum(latitudes) / len(latitudes)

        return longitude, latitude

    except Exception:
        return None, None


def save_to_parquet(df: pd.DataFrame, name: str) -> Path:
    """
    Guarda el DataFrame extraído como archivo Parquet local.

    El archivo se guarda en la ruta data/bronze/eonet/events, simulando
    la estructura que luego será cargada a Google Cloud Storage.
    """
    output_dir = Path("data/bronze/eonet/events")
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    output_path = output_dir / f"eonet_{name}_{timestamp}.parquet"

    df.to_parquet(output_path, index=False)

    return output_path
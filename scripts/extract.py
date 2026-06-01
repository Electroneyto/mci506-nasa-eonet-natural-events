import json
import os
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Tuple

import pandas as pd
import requests
from dotenv import load_dotenv

from utils import (
    build_event_geometry_key,
    build_event_source_key,
    get_polygon_centroid,
    save_to_parquet,
)


load_dotenv()


def extract_eonet_events() -> dict:
    """
    Extrae eventos naturales desde NASA EONET API v3.

    Se consulta la API pública de NASA EONET usando parámetros configurables
    por variables de entorno. Por defecto se extraen eventos abiertos y cerrados
    de los últimos 365 días.
    """
    api_url = os.getenv("EONET_API_URL", "https://eonet.gsfc.nasa.gov/api/v3/events")

    params = {
        "status": os.getenv("EONET_STATUS", "all"),
        "days": int(os.getenv("EONET_DAYS", "365")),
        "limit": int(os.getenv("EONET_LIMIT", "5000")),
    }

    print("Consultando NASA EONET API...")
    print(f"URL: {api_url}")
    print(f"Parámetros: {params}")

    response = requests.get(api_url, params=params, timeout=60)

    if response.status_code == 503:
        print("NASA EONET respondió 503. Esperando 15 segundos para reintentar...")
        time.sleep(15)
        response = requests.get(api_url, params=params, timeout=60)

    response.raise_for_status()

    return response.json()


def extract_categories(event: Dict[str, Any]) -> Tuple[str, str]:
    """
    Extrae las categorías de un evento.

    NASA EONET puede devolver una o más categorías por evento.
    Para mantener una estructura simple en Bronze, se concatenan los IDs
    y títulos de categorías separados por coma.
    """
    categories = event.get("categories", [])

    category_ids = ",".join(
        [category.get("id", "") for category in categories if category.get("id")]
    )

    category_titles = ",".join(
        [category.get("title", "") for category in categories if category.get("title")]
    )

    return category_ids, category_titles


def make_event_record(
    event: Dict[str, Any],
    ingestion_timestamp: str,
    ingestion_date: str,
) -> Dict[str, Any]:
    """
    Construye el registro principal de un evento.

    Este DataFrame será guardado como events.parquet en la capa Bronze.
    """
    category_ids, category_titles = extract_categories(event)

    closed_at = event.get("closed")
    status = "closed" if closed_at else "open"

    return {
        "event_id": event.get("id"),
        "title": event.get("title"),
        "description": event.get("description"),
        "link": event.get("link"),
        "status": status,
        "closed_at": closed_at,
        "category_ids": category_ids,
        "category_titles": category_titles,
        "raw_event_json": json.dumps(event, ensure_ascii=False),
        "ingestion_timestamp": ingestion_timestamp,
        "ingestion_date": ingestion_date,
    }


def make_source_records(
    event: Dict[str, Any],
    ingestion_timestamp: str,
    ingestion_date: str,
) -> List[Dict[str, Any]]:
    """
    Construye los registros de fuentes asociadas a cada evento.

    Este DataFrame será guardado como sources.parquet en la capa Bronze.
    """
    event_id = event.get("id")
    sources = event.get("sources", [])

    source_records = []

    for source in sources:
        source_id = source.get("id")
        source_url = source.get("url")

        event_source_key = build_event_source_key(
            event_id=event_id,
            source_id=source_id,
            source_url=source_url,
        )

        source_records.append(
            {
                "event_source_key": event_source_key,
                "event_id": event_id,
                "source_id": source_id,
                "source_url": source_url,
                "ingestion_timestamp": ingestion_timestamp,
                "ingestion_date": ingestion_date,
            }
        )

    return source_records


def make_geometry_record(
    geometry_data: Dict[str, Any],
    event_id: str,
    ingestion_timestamp: str,
    ingestion_date: str,
) -> Dict[str, Any]:
    """
    Procesa la geometría de un evento.

    NASA EONET puede devolver geometrías tipo Point o Polygon.
    Para Polygon se calcula un centroide simple.
    """
    geometry_date = geometry_data.get("date")
    geometry_type = geometry_data.get("type")
    coordinates = geometry_data.get("coordinates")

    longitude = None
    latitude = None

    if geometry_type == "Point" and isinstance(coordinates, list):
        if len(coordinates) >= 2:
            longitude = coordinates[0]
            latitude = coordinates[1]

    elif geometry_type == "Polygon" and isinstance(coordinates, list):
        longitude, latitude = get_polygon_centroid(coordinates)

    event_geometry_key = build_event_geometry_key(
        event_id=event_id,
        geometry_date=geometry_date,
        longitude=longitude,
        latitude=latitude,
    )

    return {
        "event_geometry_key": event_geometry_key,
        "event_id": event_id,
        "geometry_date": geometry_date,
        "geometry_type": geometry_type,
        "longitude": longitude,
        "latitude": latitude,
        "magnitude_value": geometry_data.get("magnitudeValue"),
        "magnitude_unit": geometry_data.get("magnitudeUnit"),
        "ingestion_timestamp": ingestion_timestamp,
        "ingestion_date": ingestion_date,
    }


def make_geometry_records(
    event: Dict[str, Any],
    ingestion_timestamp: str,
    ingestion_date: str,
) -> List[Dict[str, Any]]:
    """
    Construye los registros de geometría asociados a cada evento.

    Este DataFrame será guardado como geometry.parquet en la capa Bronze.
    """
    event_id = event.get("id")
    geometries = event.get("geometry", [])

    geometry_records = []

    for geometry_data in geometries:
        geometry_records.append(
            make_geometry_record(
                geometry_data=geometry_data,
                event_id=event_id,
                ingestion_timestamp=ingestion_timestamp,
                ingestion_date=ingestion_date,
            )
        )

    return geometry_records


def extract_events_sources_geometry(payload: dict) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Extrae y normaliza la respuesta JSON de NASA EONET en tres DataFrames:

    1. events: información principal del evento.
    2. sources: fuentes asociadas al evento.
    3. geometry: fechas, coordenadas y magnitudes del evento.
    """
    ingestion_timestamp = datetime.now(timezone.utc).isoformat()
    ingestion_date = datetime.now(timezone.utc).date().isoformat()

    event_records = []
    source_records = []
    geometry_records = []

    events_json = payload.get("events", [])

    for event in events_json:
        event_records.append(
            make_event_record(
                event=event,
                ingestion_timestamp=ingestion_timestamp,
                ingestion_date=ingestion_date,
            )
        )

        source_records.extend(
            make_source_records(
                event=event,
                ingestion_timestamp=ingestion_timestamp,
                ingestion_date=ingestion_date,
            )
        )

        geometry_records.extend(
            make_geometry_records(
                event=event,
                ingestion_timestamp=ingestion_timestamp,
                ingestion_date=ingestion_date,
            )
        )

    df_events = pd.DataFrame(event_records)
    df_sources = pd.DataFrame(source_records)
    df_geometry = pd.DataFrame(geometry_records)

    return df_events, df_sources, df_geometry


def print_info(name: str, df: pd.DataFrame, output_path) -> None:
    """
    Imprime información básica de cada DataFrame generado.
    """
    print(name)
    print(f"\tFilas generadas: {len(df)}")
    print(f"\tColumnas generadas: {len(df.columns)}")
    print(f"\tArchivo Parquet generado: {output_path}")


def main() -> None:
    """
    Ejecuta el proceso de extracción completo:
    1. Consulta NASA EONET API.
    2. Extrae eventos, fuentes y geometrías.
    3. Valida que existan datos.
    4. Guarda tres archivos Parquet en la capa Bronze local.
    """
    payload = extract_eonet_events()

    df_events, df_sources, df_geometry = extract_events_sources_geometry(payload)

    if df_events.empty:
        raise ValueError("No se extrajeron eventos desde NASA EONET.")

    if df_sources.empty:
        print("Advertencia: no se extrajeron fuentes desde NASA EONET.")

    if df_geometry.empty:
        print("Advertencia: no se extrajeron geometrías desde NASA EONET.")

    output_path_events = save_to_parquet(df_events, "events")
    output_path_sources = save_to_parquet(df_sources, "sources")
    output_path_geometry = save_to_parquet(df_geometry, "geometry")

    print("Extracción finalizada correctamente.")
    print_info("Events", df_events, output_path_events)
    print_info("Sources", df_sources, output_path_sources)
    print_info("Geometry", df_geometry, output_path_geometry)


if __name__ == "__main__":
    main()
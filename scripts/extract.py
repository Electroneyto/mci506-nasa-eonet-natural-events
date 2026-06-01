import os
import time

import pandas as pd
import requests
from dotenv import load_dotenv

from utils import build_event_geometry_key, get_polygon_centroid,  save_to_parquet


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
    if response.status_code == 200:
        return response.json()

    # En caso de que el servidor este ocupado esperar 15 segundos para volver a realizar la peitcion 
    if response.status_code == 503:
        print('El servidor esta ocupado, esperando 15 segundos para volver a realziar la peticion')
        print(response.json())

        time.sleep(15) 
        response = requests.get(api_url, params=params, timeout=60)

        if response.status_code == 200:
            return response.json()
        response.raise_for_status()



def make_geometry(geometry_data, id_event):
    """Procesa los datos geográficos de un evento (Punto o Polígono) para 
    calcular sus coordenadas, generar una clave única y estructurar 
    el diccionario de geometría."""
    geometry = {
        'magnitudeValue': geometry_data['magnitudeValue'],
        'magnitudeUnit': geometry_data['magnitudeUnit'],
        'date': geometry_data['date'],
        'type': geometry_data['type'],
        'id_event': id_event
    }
    coordinates = geometry_data['coordinates']
    if geometry['type'] == "Point" and isinstance(coordinates, list):
        if len(coordinates) >= 2:
            longitude = coordinates[0]
            latitude = coordinates[1]

    elif geometry['type'] == "Polygon" and isinstance(coordinates, list):
        longitude, latitude = get_polygon_centroid(coordinates)
    geometry['longitude'] = longitude 
    geometry['latitude'] = latitude

    event_geometry_key = build_event_geometry_key(
        event_id=id_event,
        geometry_date=geometry['date'],
        longitude=longitude,
        latitude=latitude,
    )

    geometry['geometry_key'] = event_geometry_key
    return geometry


def extraer_eventos_sources_geometries(events_json):
    """Extrae y normaliza los datos de eventos, fuentes y geometrías a 
    partir de un JSON para transformarlos en tres DataFrames de Pandas separados."""

    events = []
    events = []
    sources = []
    geometries = []

    for ev in events_json:
        event = {
            'id': ev['id'],
            'title':ev['title'],
            'description':ev['description'],
            'link':ev['link'],
            'closed':ev['closed'],
        }

        event['id_category'] = ev['categories'][0]['id']
        event['title_category'] =  ev['categories'][0]['title']
        events.append(event)

        for src in ev['sources']:
            event_source = {
                'id': src['id'],
                'url': src['url'],
                'id_event': ev['id']
            }
            sources.append(event_source)

        if 'geometry' in ev:
            for geo in ev['geometry']:
                geometry =  make_geometry(geo, ev['id'])
                geometries.append(geometry)

    
    df_events =  pd.DataFrame(events)
    df_sources = pd.DataFrame(sources)
    df_geometries = pd.DataFrame(geometries)
    return df_events, df_sources, df_geometries



def print_info(nombre: str, df, output_path):
    print(nombre)
    print(f"\tFilas generadas: {len(df)}")
    print(f"\tColumnas generadas: {len(df.columns)}")
    print(f"\tArchivo Parquet generado: {output_path}")

def main() -> None:
    """
    Ejecuta el proceso de extracción completo:
    1. Consulta NASA EONET API.
    2. Extrate eventos, sources, geometrias
    3. Valida que existan datos.
    4. Guarda el resultado como Parquet.
    """
    payload = extract_eonet_events()

    df_events, df_sources, df_geometries = extraer_eventos_sources_geometries(payload['events'])

    if df_events.empty or df_sources.empty or df_geometries.empty :
        raise ValueError("No se extrajeron eventos desde NASA EONET.")

    output_path_events = save_to_parquet(df_events, 'events')
    output_path_sources = save_to_parquet(df_sources, 'sources')
    output_path_geometrias = save_to_parquet(df_events, 'geometrias')

    print("Extracción finalizada correctamente.")
    print_info('Event', df_events, output_path_events)
    print_info('Sources', df_sources, output_path_sources)
    print_info('Geometries', df_geometries, output_path_geometrias)


if __name__ == "__main__":
    main()
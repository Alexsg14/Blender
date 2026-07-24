"""
core/osm.py — Descarga y parseo de datos de OpenStreetMap.

Usa la API pública de Overpass para obtener vías (calles, tren, agua)
dentro de un bounding box dado.
"""

import urllib.request
import urllib.parse
import json


# ─────────────────────────────────────────────────────────────────────────────
# Descarga
# ─────────────────────────────────────────────────────────────────────────────

def download_osm(bbox: tuple, highway_filter: str) -> dict:
    """
    Descarga datos de OpenStreetMap usando la API Overpass.

    Args:
        bbox: (south, west, north, east) en grados decimales.
        highway_filter: expresión regular para tipos de carretera.

    Returns:
        Diccionario JSON con los elementos OSM descargados.

    Raises:
        Exception si hay error de red o timeout.
    """
    south, west, north, east = bbox
    bbox_str = f"{south},{west},{north},{east}"

    query = f"""
[out:json][timeout:180];
(
  way["highway"~"{highway_filter}"]({bbox_str});
  way["railway"~"rail|tram|light_rail"]({bbox_str});
  way["waterway"~"river|canal|stream"]({bbox_str});
  way["natural"="water"]({bbox_str});
  way["water"]({bbox_str});
);
out body;
>;
out skel qt;
"""

    url  = "https://overpass-api.de/api/interpreter"
    data = urllib.parse.urlencode({"data": query}).encode("utf-8")
    req  = urllib.request.Request(
        url, data=data,
        headers={"User-Agent": "Blender Map Poster Generator 1.0"},
    )

    print(f"[OSM] Descargando datos (BBOX: {south:.4f},{west:.4f},{north:.4f},{east:.4f})...")

    with urllib.request.urlopen(req, timeout=180) as response:
        raw = response.read().decode("utf-8")

    return json.loads(raw)


# ─────────────────────────────────────────────────────────────────────────────
# Parseo
# ─────────────────────────────────────────────────────────────────────────────

def parse_osm(osm_data: dict) -> tuple:
    """
    Separa los elementos OSM en nodos (id → (lon, lat)) y vías (list).

    Returns:
        (nodes: dict, ways: list)
    """
    nodes = {}
    ways  = []

    for el in osm_data.get("elements", []):
        if el["type"] == "node":
            nodes[el["id"]] = (el["lon"], el["lat"])
        elif el["type"] == "way":
            ways.append(el)

    print(f"[OSM] Nodos: {len(nodes)}  |  Vías: {len(ways)}")
    return nodes, ways

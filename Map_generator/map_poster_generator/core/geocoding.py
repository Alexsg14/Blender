"""
core/geocoding.py — Geocodificación y cálculo de bounding boxes.

Usa la API pública de Nominatim (OpenStreetMap) para buscar ciudades
y calcular el BBOX correspondiente sin necesidad de clave de API.
"""

import urllib.request
import urllib.parse
import json
import math


# ─────────────────────────────────────────────────────────────────────────────
# Nominatim
# ─────────────────────────────────────────────────────────────────────────────

def geocode_city(city_name: str):
    """
    Busca una ciudad en Nominatim y devuelve su posición y bounding box.

    Retorna:
        (lat: float, lon: float, display_name: str)
        o None si no se encuentra o hay error de red.
    """
    encoded = urllib.parse.urlencode({
        "q": city_name,
        "format": "json",
        "limit": "1",
    })
    url = f"https://nominatim.openstreetmap.org/search?{encoded}"
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Blender Map Poster Generator 1.0"},
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            results = json.loads(resp.read().decode("utf-8"))

        if not results:
            print(f"[GEO] No se encontró: '{city_name}'")
            return None

        r = results[0]
        lat = float(r["lat"])
        lon = float(r["lon"])
        display_name = r.get("display_name", city_name)
        print(f"[GEO] Encontrado: {display_name}")
        print(f"[GEO] Centro: ({lat:.5f}, {lon:.5f})")
        return lat, lon, display_name

    except Exception as e:
        print(f"[GEO] Error en geocodificación: {e}")
        return None


# ─────────────────────────────────────────────────────────────────────────────
# Cálculo de BBOX desde radio
# ─────────────────────────────────────────────────────────────────────────────

def bbox_from_center_radius(lat: float, lon: float, radius_km: float):
    """
    Calcula el bounding box (south, west, north, east) a partir de un
    centro geográfico y un radio en kilómetros.
    """
    earth_km = 6371.0
    delta_lat = math.degrees(radius_km / earth_km)
    delta_lon = math.degrees(
        radius_km / (earth_km * math.cos(math.radians(lat)))
    )
    return (
        lat - delta_lat,   # south
        lon - delta_lon,   # west
        lat + delta_lat,   # north
        lon + delta_lon,   # east
    )


# ─────────────────────────────────────────────────────────────────────────────
# Resolver ubicación completa desde las propiedades del addon
# ─────────────────────────────────────────────────────────────────────────────

def resolve_location(props):
    """
    Resuelve el BBOX final y las etiquetas de ciudad/país
    según el LOCATION_MODE configurado en las propiedades.

    Retorna:
        (bbox, city_label, country_label, center_lat, center_lon)
        donde bbox = (south, west, north, east)
    """
    mode = props.location_mode

    # ── BBOX manual ───────────────────────────────────────────────────────────
    if mode == "MANUAL_BBOX":
        bbox = (props.bbox_south, props.bbox_west, props.bbox_north, props.bbox_east)
        c_lat = (bbox[0] + bbox[2]) / 2
        c_lon = (bbox[1] + bbox[3]) / 2
        print(f"[LOCATION] Modo: BBOX manual → {bbox}")
        return bbox, "", "", c_lat, c_lon

    # ── Coordenadas + radio ───────────────────────────────────────────────────
    if mode == "CENTER_COORDS":
        bbox = bbox_from_center_radius(props.center_lat, props.center_lon, props.center_radius_km)
        print(f"[LOCATION] Modo: Centro+Radio → {bbox}")
        return bbox, "", "", props.center_lat, props.center_lon

    # ── Nombre de ciudad ──────────────────────────────────────────────────────
    result = geocode_city(props.city_name)

    if result is None:
        # Fallback: usar los valores de BBOX manual como reserva
        print("[LOCATION] Geocodificación fallida → usando BBOX manual de reserva")
        bbox = (props.bbox_south, props.bbox_west, props.bbox_north, props.bbox_east)
        c_lat = (bbox[0] + bbox[2]) / 2
        c_lon = (bbox[1] + bbox[3]) / 2
        return bbox, props.city_name, "", c_lat, c_lon

    lat, lon, display_name = result

    # Extraer nombre de ciudad y país del string de búsqueda
    city_label = ""
    country_label = ""
    if "," in props.city_name:
        parts = [p.strip() for p in props.city_name.split(",")]
        city_label    = parts[0]
        country_label = parts[-1]
    else:
        city_label = props.city_name

    # Usar bbox por radio (Nominatim a veces devuelve bbox de todo el país)
    bbox = bbox_from_center_radius(lat, lon, props.radius_km)
    print(f"[LOCATION] BBOX final (radio {props.radius_km} km): {bbox}")
    return bbox, city_label, country_label, lat, lon

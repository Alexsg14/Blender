import bpy
import urllib.request
import urllib.parse
import json
import math

# ============================================================
# GENERADOR UNIVERSAL DE PÓSTERS CARTOGRÁFICOS EN BLENDER
#
# Genera un mapa 3D estilizado a partir de datos de OpenStreetMap
# para CUALQUIER ciudad o ubicación del mundo.
#
# Compatible con el archivo .blend de plantilla incluido en la
# carpeta, o con cualquier escena de Blender limpia.
#
# ============================================================


# ============================================================
# ─── CONFIGURACIÓN PRINCIPAL ─────────────────────────────────
# ============================================================

# ─── MODO DE UBICACIÓN ───────────────────────────────────────
#
# Elige UNO de los tres modos disponibles:
#
#   "CITY_NAME"     → Busca automáticamente por nombre de ciudad
#                     (requiere conexión a Internet)
#
#   "CENTER_COORDS" → Coordenadas centrales + radio en km
#
#   "MANUAL_BBOX"   → Bounding box manual (máxima precisión)
#
LOCATION_MODE = "CITY_NAME"

# ─── Opción A: Búsqueda por nombre de ciudad ─────────────────
# Ejemplos: "Madrid, Spain" | "Tokyo, Japan" | "New York, USA"
#           "Buenos Aires, Argentina" | "Paris, France"
CITY_NAME = "Manchester, UK"
RADIUS_KM = 3.5   # Radio aproximado del mapa en km

# ─── Opción B: Coordenadas centrales + radio ─────────────────
CENTER_LAT = 53.4808  # Latitud del centro
CENTER_LON = -2.2426  # Longitud del centro
CENTER_RADIUS_KM = 3.5

# ─── Opción C: BBOX manual (south, west, north, east) ────────
MANUAL_BBOX = (53.4550, -2.2850, 53.5050, -2.2000)


# ─── TAMAÑO DEL PÓSTER ───────────────────────────────────────
POSTER_WIDTH  = 18.0
POSTER_HEIGHT = 24.0

# Qué porcentaje del póster ocupa el mapa (0.0 a 1.0)
MAP_FILL_X = 0.98
MAP_FILL_Y = 0.90


# ─── COLECCIONES Y MATERIALES ────────────────────────────────
# Nombres de las colecciones en tu escena Blender.
# Si no existen, el script las creará automáticamente.
ROADS_COLLECTION_NAME  = "Roads"
RAIL_COLLECTION_NAME   = "Rail"
WATER_COLLECTION_NAME  = "Water"
MARKER_COLLECTION_NAME = "Markers"

# Nombres de los materiales existentes en tu escena.
# Si no existen, se crearán automáticamente con colores predeterminados.
# Los colores predeterminados son los que usaba el póster original de Manchester.
ROAD_MATERIAL_NAME      = "Roads"
MAIN_ROAD_MATERIAL_NAME = "Main Roads"
RAIL_MATERIAL_NAME      = "Rail"
WATER_MATERIAL_NAME     = "Water"


# ─── TEXTOS DEL PÓSTER ───────────────────────────────────────
# Nombres de los objetos de texto que tiene tu plantilla .blend.
# Si no existen o el nombre es incorrecto, se omiten sin error.
# Pon None para deshabilitar la actualización de ese campo.
TEXT_OBJ_CITY_NAME    = "text_city"      # Nombre de la ciudad
TEXT_OBJ_COUNTRY      = "text_country"   # País / subtítulo
TEXT_OBJ_COORDS       = "text_coords"    # Coordenadas formateadas
TEXT_OBJ_YEAR         = None             # Año (None = no actualizar)

# Si se detecta el modo CITY_NAME, este campo se rellena automáticamente.
# Si prefieres escribirlo manualmente, ponlo aquí:
POSTER_CITY_LABEL     = ""   # Ej: "Manchester" (vacío = auto)
POSTER_COUNTRY_LABEL  = ""   # Ej: "United Kingdom" (vacío = auto)


# ─── FILTRO DE CALLES ────────────────────────────────────────
# Limpio (menos detalle):
# HIGHWAY_FILTER = "motorway|trunk|primary|secondary|tertiary"
# Con más detalle:
HIGHWAY_FILTER = "motorway|trunk|primary|secondary|tertiary|unclassified"
# Máximo detalle (lento, no recomendado para póster):
# HIGHWAY_FILTER = "motorway|trunk|primary|secondary|tertiary|unclassified|residential"


# ─── GROSOR DE LÍNEAS ────────────────────────────────────────
NORMAL_ROAD_WIDTH  = 0.010
MAIN_ROAD_WIDTH    = 0.030
MOTORWAY_WIDTH     = 0.050
RAIL_WIDTH         = 0.010
WATERWAY_WIDTH     = 0.028


# ─── MARCADORES DE UBICACIONES ───────────────────────────────
# Lista de marcadores para pintar en el mapa.
# Puedes dejarla vacía [], añadir tus propios puntos de interés
# o ajustar los de Manchester.
#
# Campos:
#   id           → Número/identificador del marcador
#   name         → Nombre que aparecerá en la etiqueta
#   lat / lon    → Coordenadas del punto
#   label_offset → (x, y) desplazamiento de la etiqueta respecto al punto
#   marker_shape → "circle" (defecto) o "heart"
#
MARKERS = [
    {
        "id": "1",
        "name": "Cinnabon Deansgate",
        "lat": 53.4826, "lon": -2.2475,
        "label_offset": (-1.15, 0.55),
    },
    {
        "id": "2",
        "name": "Afflecks",
        "lat": 53.4844, "lon": -2.23326,
        "label_offset": (0.70, 0.65),
    },
    {
        "id": "3",
        "name": "BeeHouse",
        "lat": 53.4746, "lon": -2.2502,
        "label_offset": (-1.10, -0.50),
    },
    {
        "id": "4",
        "name": "Urban Playground / The Cube",
        "lat": 53.4742, "lon": -2.2431,
        "label_offset": (0.25, 0.95),
    },
    {
        "id": "5",
        "name": "Revolución de Cuba",
        "lat": 53.4783931, "lon": -2.2488782,
        "label_offset": (-1.30, 0.05),
    },
    {
        "id": "6",
        "name": "Hampton & Vouis Princess Street",
        "lat": 53.479728, "lon": -2.244286,
        "label_offset": (0.85, 0.35),
    },
    {
        "id": "7",
        "name": "Another Heart To Feed",
        "lat": 53.4822, "lon": -2.2352,
        "label_offset": (0.90, -0.10),
    },
    {
        "id": "8",
        "name": "La Vie Cafe",
        "lat": 53.4833563, "lon": -2.2466934,
        "label_offset": (-1.25, 0.30),
    },
    {
        "id": "9",
        "name": "Don Marco",
        "lat": 53.4759033, "lon": -2.2513928,
        "label_offset": (-1.10, -0.25),
    },
    {
        "id": "10",
        "name": "The Quadrangle",
        "lat": 53.47268035610678, "lon": -2.241007701243298,
        "label_offset": (0.45, 0.25),
        "marker_shape": "heart",
    },
    {
        "id": "11",
        "name": "The Bridge",
        "lat": 53.48307043162128, "lon": -2.2515250823844317,
        "label_offset": (0.45, 0.25),
        "marker_shape": "heart",
    },
    {
        "id": "12",
        "name": "MOJO Manchester",
        "lat": 53.4812722, "lon": -2.24981,
        "label_offset": (-1.15, 0.45),
    },
    {
        "id": "13",
        "name": "Maki & Ramen Manchester NQ",
        "lat": 53.48427, "lon": -2.237577,
        "label_offset": (0.85, 0.10),
    },
    {
        "id": "14",
        "name": "La Bandera",
        "lat": 53.4801, "lon": -2.2495,
        "label_offset": (-1.20, -0.15),
    },
    {
        "id": "15",
        "name": "Crown Square, Spinningfields",
        "lat": 53.4804448, "lon": -2.2520667,
        "label_offset": (-1.20, 0.20),
    },
    {
        "id": "16",
        "name": "NQ64 Northern Quarter",
        "lat": 53.4824604, "lon": -2.2366911,
        "label_offset": (0.80, -0.30),
    },
    {
        "id": "17",
        "name": "The Alchemist Spinningfields",
        "lat": 53.4798, "lon": -2.2507,
        "label_offset": (-1.25, 0.05),
    },
    {
        "id": "18",
        "name": "Albert's Schloss Manchester",
        "lat": 53.4782, "lon": -2.24791,
        "label_offset": (0.65, -0.35),
    },
]


# ─── ESTILO DE MARCADORES ────────────────────────────────────
MARKER_RADIUS           = 0.10
MARKER_RING_WIDTH       = 0.018
MARKER_DOT_RADIUS_FACTOR = 0.22
MARKER_Z                = 0.22

LEADER_LABEL_SIZE  = 0.16
LEADER_LABEL_Z     = 0.27
LEADER_LINE_Z      = 0.235
LEADER_LINE_WIDTH  = 0.006

# Qué muestra la etiqueta: "name" | "id" | "both"
LEADER_LABEL_MODE = "name"

# Materiales para marcadores
MARKER_MATERIAL_NAME       = "Dots Stroke"
MARKER_LABEL_MATERIAL_NAME = "Text"
MARKER_LEGEND_MATERIAL_NAME = "Text"

# Leyenda lateral (lista de puntos)
USE_LEADER_LABELS = True
USE_LEGEND_LIST   = False
LEGEND_TITLE      = "Places"
LEGEND_X          = -7.95
LEGEND_Y          = -9.05
LEGEND_Z          = 0.30
LEGEND_TITLE_SIZE = 0.22
LEGEND_ITEM_SIZE  = 0.145
LEGEND_LINE_SPACING = 0.34
LEGEND_MODE       = "id_name"


# ============================================================
# ─── GEOCODIFICACIÓN ─────────────────────────────────────────
# ============================================================

def geocode_city(city_name):
    """
    Consulta Nominatim (OpenStreetMap) para obtener las coordenadas
    y bounding box de una ciudad.
    Devuelve (lat, lon, (south, west, north, east)) o None si falla.
    """
    encoded = urllib.parse.urlencode({
        "q": city_name,
        "format": "json",
        "limit": "1",
    })
    url = f"https://nominatim.openstreetmap.org/search?{encoded}"

    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Blender Universal Map Generator"}
    )
    try:
        print(f"[GEO] Buscando '{city_name}'...")
        with urllib.request.urlopen(req, timeout=15) as resp:
            results = json.loads(resp.read().decode("utf-8"))

        if not results:
            print(f"[GEO] No se encontró la ciudad: '{city_name}'")
            return None

        r = results[0]
        lat = float(r["lat"])
        lon = float(r["lon"])
        bb  = r.get("boundingbox")  # [south, north, west, east]

        if bb:
            south, north, west, east = float(bb[0]), float(bb[1]), float(bb[2]), float(bb[3])
            print(f"[GEO] Encontrado: {r.get('display_name', city_name)}")
            print(f"[GEO] Centro: ({lat:.4f}, {lon:.4f})  |  BBOX: ({south:.4f}, {west:.4f}, {north:.4f}, {east:.4f})")
            return lat, lon, (south, west, north, east)

        return lat, lon, None

    except Exception as e:
        print(f"[GEO] Error en geocodificación: {e}")
        return None


def bbox_from_center_radius(lat, lon, radius_km):
    """
    Calcula un BBOX (south, west, north, east) a partir de un
    centro (lat, lon) y un radio en kilómetros.
    """
    earth_radius_km = 6371.0
    delta_lat = math.degrees(radius_km / earth_radius_km)
    delta_lon = math.degrees(radius_km / (earth_radius_km * math.cos(math.radians(lat))))

    south = lat - delta_lat
    north = lat + delta_lat
    west  = lon - delta_lon
    east  = lon + delta_lon

    return (south, west, north, east)


def resolve_location():
    """
    Resuelve el BBOX final según el LOCATION_MODE configurado.
    Devuelve (bbox, city_label, country_label, center_lat, center_lon).
    """
    global POSTER_CITY_LABEL, POSTER_COUNTRY_LABEL

    city_label    = POSTER_CITY_LABEL.strip()
    country_label = POSTER_COUNTRY_LABEL.strip()

    if LOCATION_MODE == "MANUAL_BBOX":
        bbox = MANUAL_BBOX
        south, west, north, east = bbox
        center_lat = (south + north) / 2
        center_lon = (west + east) / 2
        print(f"[LOCATION] Modo: BBOX manual → {bbox}")
        return bbox, city_label, country_label, center_lat, center_lon

    if LOCATION_MODE == "CENTER_COORDS":
        bbox = bbox_from_center_radius(CENTER_LAT, CENTER_LON, CENTER_RADIUS_KM)
        print(f"[LOCATION] Modo: Coordenadas centro → {bbox}")
        return bbox, city_label, country_label, CENTER_LAT, CENTER_LON

    # LOCATION_MODE == "CITY_NAME"
    result = geocode_city(CITY_NAME)

    if result is None:
        print(f"[LOCATION] Geocodificación fallida. Usando BBOX manual de reserva.")
        bbox = MANUAL_BBOX
        south, west, north, east = bbox
        return bbox, city_label, country_label, (south + north) / 2, (west + east) / 2

    lat, lon, nom_bbox = result

    # Extraer etiquetas automáticamente del nombre de la ciudad
    if not city_label and "," in CITY_NAME:
        parts = [p.strip() for p in CITY_NAME.split(",")]
        city_label    = parts[0]
        country_label = parts[-1] if not country_label else country_label
    elif not city_label:
        city_label = CITY_NAME

    # Usar el BBOX de Nominatim ajustado al radio configurado,
    # comparando cuál es mayor para preservar el nivel de zoom deseado.
    radius_bbox = bbox_from_center_radius(lat, lon, RADIUS_KM)

    if nom_bbox:
        s1, w1, n1, e1 = nom_bbox
        s2, w2, n2, e2 = radius_bbox
        # Tomamos el bbox del radio porque Nominatim a veces devuelve
        # bboxes demasiado grandes (comunidades o países enteros).
        bbox = radius_bbox
        print(f"[LOCATION] BBOX resuelto por radio ({RADIUS_KM} km): {bbox}")
    else:
        bbox = radius_bbox

    return bbox, city_label, country_label, lat, lon


# ============================================================
# ─── COLECCIONES Y MATERIALES DEFENSIVOS ─────────────────────
# ============================================================

# Colores predeterminados para los materiales (RGBA lineal).
# Si el material ya existe en tu .blend, NO se modifica.
# Solo se usan cuando hay que crear el material desde cero.
_DEFAULT_MATERIAL_COLORS = {
    "Roads":      (0.80, 0.78, 0.72, 1.0),   # Beige claro
    "Main Roads": (0.95, 0.90, 0.75, 1.0),   # Beige más cálido
    "Rail":       (0.50, 0.50, 0.55, 1.0),   # Gris
    "Water":      (0.35, 0.60, 0.80, 1.0),   # Azul
    "Dots Stroke":(0.95, 0.80, 0.30, 1.0),   # Amarillo marcador
    "Text":       (0.15, 0.15, 0.15, 1.0),   # Casi negro
}


def get_or_create_collection(name):
    """
    Busca la colección 'name'. Si no existe, la crea y la vincula
    a la escena activa. Nunca lanza RuntimeError.
    """
    col = bpy.data.collections.get(name)
    if col is None:
        print(f"[SCENE] Colección '{name}' no encontrada → creando nueva.")
        col = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(col)
    return col


def get_or_create_material(name):
    """
    Busca el material 'name'. Si no existe, crea un material
    Principled BSDF con el color predeterminado del diccionario.
    Nunca lanza RuntimeError.
    """
    mat = bpy.data.materials.get(name)
    if mat is None:
        print(f"[SCENE] Material '{name}' no encontrado → creando nuevo.")
        mat = bpy.data.materials.new(name=name)
        mat.use_nodes = True
        nodes = mat.node_tree.nodes
        links = mat.node_tree.links
        nodes.clear()

        bsdf = nodes.new("ShaderNodeBsdfPrincipled")
        bsdf.location = (0, 0)
        color = _DEFAULT_MATERIAL_COLORS.get(name, (0.8, 0.8, 0.8, 1.0))
        bsdf.inputs["Base Color"].default_value = color
        bsdf.inputs["Roughness"].default_value  = 1.0

        out = nodes.new("ShaderNodeOutputMaterial")
        out.location = (300, 0)
        links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    return mat


def get_existing_material_or_fallback(name, fallback_name=None):
    """
    Busca un material existente sin modificarlo.
    Si no existe, crea uno o usa fallback.
    """
    mat = bpy.data.materials.get(name)
    if mat is None and fallback_name:
        mat = bpy.data.materials.get(fallback_name)
    if mat is None:
        mat = get_or_create_material(name)
    return mat


# ============================================================
# ─── TEXTOS DEL PÓSTER ───────────────────────────────────────
# ============================================================

def format_coords_dms(lat, lon):
    """
    Convierte lat/lon decimales a formato de póster estilizado.
    Ej: 53.4808, -2.2426 → "53° 28' N  •  2° 14' W"
    """
    def to_dms(deg):
        d = int(abs(deg))
        m = int((abs(deg) - d) * 60)
        return d, m

    lat_d, lat_m = to_dms(lat)
    lon_d, lon_m = to_dms(lon)
    lat_dir = "N" if lat >= 0 else "S"
    lon_dir = "E" if lon >= 0 else "W"

    return f"{lat_d}° {lat_m:02d}' {lat_dir}  •  {lon_d}° {lon_m:02d}' {lon_dir}"


def update_scene_text(obj_name, new_text):
    """
    Actualiza el body de un objeto de texto de Blender si existe.
    Si el objeto no existe o no es tipo FONT, se omite sin error.
    """
    if obj_name is None or not new_text:
        return
    obj = bpy.data.objects.get(obj_name)
    if obj is None:
        print(f"[TEXT] Objeto '{obj_name}' no encontrado en la escena (omitido).")
        return
    if obj.type != "FONT":
        print(f"[TEXT] '{obj_name}' no es un objeto de texto (omitido).")
        return
    obj.data.body = new_text
    print(f"[TEXT] '{obj_name}' actualizado → '{new_text}'")


# ============================================================
# ─── UTILIDADES DE MAPA ──────────────────────────────────────
# ============================================================

def clear_collection_objects(collection):
    """
    Borra SOLO los objetos dentro de esta colección.
    No borra la colección, materiales, cámara, luces, ni textos.
    """
    for obj in list(collection.objects):
        bpy.data.objects.remove(obj, do_unlink=True)


def link_only_to_collection(obj, target_collection):
    if obj is None:
        return
    if obj.name not in target_collection.objects:
        target_collection.objects.link(obj)
    for col in list(obj.users_collection):
        if col != target_collection:
            try:
                col.objects.unlink(obj)
            except RuntimeError:
                pass


def safe_obj_name(text):
    for ch in "/\\:*?\"<>|":
        text = text.replace(ch, "_")
    return text


def marker_label_text(marker, mode):
    marker_id = marker.get("id", "")
    name = marker.get("name", "")
    if mode == "id":
        return marker_id
    if mode == "both":
        return f"{marker_id} {name}"
    return name


def marker_inside_bbox(marker, south, west, north, east):
    lat = marker["lat"]
    lon = marker["lon"]
    return south <= lat <= north and west <= lon <= east


# ============================================================
# ─── DESCARGA DE DATOS OPENSTREETMAP ─────────────────────────
# ============================================================

def overpass_query(query):
    url = "https://overpass-api.de/api/interpreter"
    data = urllib.parse.urlencode({"data": query}).encode("utf-8")
    req = urllib.request.Request(
        url, data=data,
        headers={"User-Agent": "Blender Universal Map Generator"}
    )
    print("[OSM] Descargando datos de OpenStreetMap...")
    with urllib.request.urlopen(req, timeout=180) as response:
        return json.loads(response.read().decode("utf-8"))


# ============================================================
# ─── PROYECCIÓN LAT/LON A XY ─────────────────────────────────
# ============================================================

def make_projection(bbox):
    south, west, north, east = bbox
    center_lat = (south + north) / 2
    center_lon = (west + east) / 2

    def lonlat_to_xy(lon, lat):
        earth_radius = 6371000
        x = math.radians(lon - center_lon) * earth_radius * math.cos(math.radians(center_lat))
        y = math.radians(lat - center_lat) * earth_radius
        return x, y

    corners = [
        lonlat_to_xy(west, south),
        lonlat_to_xy(east, south),
        lonlat_to_xy(west, north),
        lonlat_to_xy(east, north),
    ]
    min_x = min(p[0] for p in corners)
    max_x = max(p[0] for p in corners)
    min_y = min(p[1] for p in corners)
    max_y = max(p[1] for p in corners)

    map_width_m  = max_x - min_x
    map_height_m = max_y - min_y

    scale = min(
        (POSTER_WIDTH  * MAP_FILL_X) / map_width_m,
        (POSTER_HEIGHT * MAP_FILL_Y) / map_height_m
    )

    def project(lon, lat):
        x, y = lonlat_to_xy(lon, lat)
        return x * scale, y * scale

    return project


# ============================================================
# ─── GEOMETRÍA ───────────────────────────────────────────────
# ============================================================

def create_curve_line(name, coords, bevel_depth, material, z=0.05):
    if len(coords) < 2:
        return None

    curve = bpy.data.curves.new(name, type="CURVE")
    curve.dimensions = "3D"
    curve.resolution_u = 2
    curve.bevel_depth = bevel_depth
    curve.bevel_resolution = 1
    curve.fill_mode = "FULL"
    curve.use_path = True

    poly = curve.splines.new("POLY")
    poly.points.add(len(coords) - 1)

    for point, coord in zip(poly.points, coords):
        x, y = coord
        point.co = (x, y, z, 1)

    obj = bpy.data.objects.new(name, curve)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(material)
    return obj


def create_filled_polygon(name, coords, material, z=0.025):
    if len(coords) < 3:
        return None

    mesh = bpy.data.meshes.new(name)
    verts = [(x, y, z) for x, y in coords]
    if verts[0] != verts[-1]:
        verts.append(verts[0])
    face = list(range(len(verts) - 1))

    try:
        mesh.from_pydata(verts, [], [face])
        mesh.update()
    except Exception:
        return None

    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(material)
    return obj


def highway_style(tags, mat_road, mat_main):
    road_type = tags.get("highway", "")
    if road_type == "motorway":
        return MOTORWAY_WIDTH, mat_main
    if road_type == "trunk":
        return MOTORWAY_WIDTH * 0.85, mat_main
    if road_type == "primary":
        return MAIN_ROAD_WIDTH, mat_main
    if road_type == "secondary":
        return MAIN_ROAD_WIDTH * 0.75, mat_main
    if road_type == "tertiary":
        return NORMAL_ROAD_WIDTH * 1.20, mat_road
    return NORMAL_ROAD_WIDTH, mat_road


# ─── MARCADORES ──────────────────────────────────────────────

def create_heart_marker(name, x, y, size, material, z, marker_collection):
    verts_2d = []
    steps = 120
    for i in range(steps):
        t = (2 * math.pi * i) / steps
        hx = 16 * (math.sin(t) ** 3)
        hy = (13 * math.cos(t) - 5 * math.cos(2 * t)
              - 2 * math.cos(3 * t) - math.cos(4 * t))
        verts_2d.append((x + (hx / 18.0) * size, y + (hy / 18.0) * size, z))

    center = (x, y, z)
    verts = [center] + verts_2d
    faces = []
    for i in range(1, len(verts)):
        next_i = 1 if i == len(verts) - 1 else i + 1
        faces.append((0, i, next_i))

    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts, [], faces)
    mesh.update()

    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    if material:
        obj.data.materials.append(material)
    link_only_to_collection(obj, marker_collection)
    return obj


def create_marker_ring(name, x, y, radius, ring_width, material, z, marker_collection):
    bpy.ops.mesh.primitive_torus_add(
        major_radius=radius, minor_radius=ring_width,
        major_segments=48, minor_segments=8,
        location=(x, y, z)
    )
    obj = bpy.context.object
    obj.name = name
    if material:
        obj.data.materials.append(material)
    link_only_to_collection(obj, marker_collection)
    return obj


def create_marker_dot(name, x, y, radius, material, z, marker_collection):
    bpy.ops.mesh.primitive_uv_sphere_add(
        segments=24, ring_count=12, radius=radius, location=(x, y, z)
    )
    obj = bpy.context.object
    obj.name = name
    obj.scale.z = 0.08
    if material:
        obj.data.materials.append(material)
    link_only_to_collection(obj, marker_collection)
    return obj


def create_text_obj(name, body, x, y, z, size, material, align_x, marker_collection):
    bpy.ops.object.text_add(location=(x, y, z), rotation=(0, 0, 0))
    obj = bpy.context.object
    obj.name = name
    obj.data.body = body
    obj.data.align_x = align_x
    obj.data.align_y = "CENTER"
    obj.data.size = size
    obj.data.extrude = 0.002
    if material:
        obj.data.materials.append(material)
    link_only_to_collection(obj, marker_collection)
    return obj


def create_leader_line(name, x1, y1, x2, y2, material, z, width, marker_collection):
    curve = bpy.data.curves.new(name, type="CURVE")
    curve.dimensions = "3D"
    curve.resolution_u = 1
    curve.bevel_depth = width
    curve.bevel_resolution = 0

    spline = curve.splines.new("POLY")
    spline.points.add(1)
    spline.points[0].co = (x1, y1, z, 1)
    spline.points[1].co = (x2, y2, z, 1)

    obj = bpy.data.objects.new(name, curve)
    bpy.context.collection.objects.link(obj)
    if material:
        obj.data.materials.append(material)
    link_only_to_collection(obj, marker_collection)
    return obj


# ============================================================
# ─── EJECUCIÓN PRINCIPAL ─────────────────────────────────────
# ============================================================

print("\n" + "=" * 60)
print("  GENERADOR UNIVERSAL DE PÓSTERS CARTOGRÁFICOS EN BLENDER")
print("=" * 60 + "\n")

# ─── 1. Resolver ubicación ───────────────────────────────────
bbox, city_label, country_label, center_lat, center_lon = resolve_location()
south, west, north, east = bbox

# ─── 2. Actualizar textos del póster ─────────────────────────
coords_str = format_coords_dms(center_lat, center_lon)
update_scene_text(TEXT_OBJ_CITY_NAME, city_label)
update_scene_text(TEXT_OBJ_COUNTRY, country_label)
update_scene_text(TEXT_OBJ_COORDS, coords_str)

# ─── 3. Cargar colecciones y materiales (sin fallar) ─────────
roads_collection  = get_or_create_collection(ROADS_COLLECTION_NAME)
rail_collection   = get_or_create_collection(RAIL_COLLECTION_NAME)
water_collection  = get_or_create_collection(WATER_COLLECTION_NAME)

mat_road  = get_or_create_material(ROAD_MATERIAL_NAME)
mat_main  = get_or_create_material(MAIN_ROAD_MATERIAL_NAME)
mat_rail  = get_or_create_material(RAIL_MATERIAL_NAME)
mat_water = get_or_create_material(WATER_MATERIAL_NAME)

marker_material        = get_existing_material_or_fallback(MARKER_MATERIAL_NAME, "Text")
marker_label_material  = get_existing_material_or_fallback(MARKER_LABEL_MATERIAL_NAME, MARKER_MATERIAL_NAME)
marker_legend_material = get_existing_material_or_fallback(MARKER_LEGEND_MATERIAL_NAME, MARKER_LABEL_MATERIAL_NAME)

print(f"\n[INFO] Ciudad: {city_label} {('| ' + country_label) if country_label else ''}")
print(f"[INFO] Coordenadas: {coords_str}")
print(f"[INFO] BBOX: S={south:.4f} W={west:.4f} N={north:.4f} E={east:.4f}")

# ─── 4. Descargar datos de OpenStreetMap ─────────────────────
bbox_str = f"{south},{west},{north},{east}"

query = f"""
[out:json][timeout:180];
(
  way["highway"~"{HIGHWAY_FILTER}"]({bbox_str});
  way["railway"~"rail|tram|light_rail"]({bbox_str});
  way["waterway"~"river|canal|stream"]({bbox_str});
  way["natural"="water"]({bbox_str});
  way["water"]({bbox_str});
);
out body;
>;
out skel qt;
"""

osm = overpass_query(query)

nodes = {}
ways  = []
for el in osm["elements"]:
    if el["type"] == "node":
        nodes[el["id"]] = (el["lon"], el["lat"])
    elif el["type"] == "way":
        ways.append(el)

print(f"[OSM] Nodos: {len(nodes)}  |  Vías: {len(ways)}")

# ─── 5. Borrar mapa anterior (solo geometría) ────────────────
clear_collection_objects(roads_collection)
clear_collection_objects(rail_collection)
clear_collection_objects(water_collection)

# ─── 6. Proyección ───────────────────────────────────────────
project = make_projection(bbox)

# ─── 7. Generar nueva geometría ──────────────────────────────
road_count  = 0
rail_count  = 0
water_count = 0

for way in ways:
    tags     = way.get("tags", {})
    node_ids = way.get("nodes", [])
    coords   = []

    for node_id in node_ids:
        if node_id in nodes:
            lon, lat = nodes[node_id]
            coords.append(project(lon, lat))

    if len(coords) < 2:
        continue

    if "highway" in tags:
        width, mat = highway_style(tags, mat_road, mat_main)
        obj = create_curve_line("road", coords, width, mat, z=0.08)
        link_only_to_collection(obj, roads_collection)
        road_count += 1

    elif "railway" in tags:
        obj = create_curve_line("rail", coords, RAIL_WIDTH, mat_rail, z=0.07)
        link_only_to_collection(obj, rail_collection)
        rail_count += 1

    elif "waterway" in tags:
        obj = create_curve_line("waterway", coords, WATERWAY_WIDTH, mat_water, z=0.06)
        link_only_to_collection(obj, water_collection)
        water_count += 1

    elif tags.get("natural") == "water" or "water" in tags:
        obj = create_filled_polygon("water", coords, mat_water, z=0.04)
        link_only_to_collection(obj, water_collection)
        water_count += 1

print(f"[GEO] Calles: {road_count}  |  Tren: {rail_count}  |  Agua: {water_count}")

# ─── 8. Colección de marcadores ──────────────────────────────
marker_collection = bpy.data.collections.get(MARKER_COLLECTION_NAME)
if marker_collection is None:
    marker_collection = bpy.data.collections.new(MARKER_COLLECTION_NAME)
    bpy.context.scene.collection.children.link(marker_collection)
else:
    for obj in list(marker_collection.objects):
        bpy.data.objects.remove(obj, do_unlink=True)

# ─── 9. Generar marcadores ───────────────────────────────────
visible_markers = []

for marker in MARKERS:
    name      = marker["name"]
    marker_id = marker.get("id", "")
    safe_name = safe_obj_name(name)

    if not marker_inside_bbox(marker, south, west, north, east):
        print(f"[MARKER] Fuera del BBOX, omitido: {name}")
        continue

    lon = marker["lon"]
    lat = marker["lat"]
    x, y = project(lon, lat)
    visible_markers.append(marker)

    marker_shape = marker.get("marker_shape", "circle")

    if marker_shape == "heart":
        create_heart_marker(
            f"marker_heart_{marker_id}_{safe_name}",
            x, y, MARKER_RADIUS * 1.65,
            marker_material, MARKER_Z + 0.01,
            marker_collection
        )
    else:
        create_marker_ring(
            f"marker_ring_{marker_id}_{safe_name}",
            x, y, MARKER_RADIUS, MARKER_RING_WIDTH,
            marker_material, MARKER_Z,
            marker_collection
        )
        create_marker_dot(
            f"marker_dot_{marker_id}_{safe_name}",
            x, y, MARKER_RADIUS * MARKER_DOT_RADIUS_FACTOR,
            marker_material, MARKER_Z + 0.01,
            marker_collection
        )

    if USE_LEADER_LABELS:
        offset_x, offset_y = marker.get("label_offset", (0.45, 0.25))
        label_x = x + offset_x
        label_y = y + offset_y
        label_body = marker_label_text(marker, LEADER_LABEL_MODE)

        create_leader_line(
            f"marker_line_{marker_id}_{safe_name}",
            x, y, label_x, label_y,
            marker_material, LEADER_LINE_Z, LEADER_LINE_WIDTH,
            marker_collection
        )
        create_text_obj(
            f"marker_label_{marker_id}_{safe_name}",
            label_body, label_x, label_y,
            LEADER_LABEL_Z, LEADER_LABEL_SIZE,
            marker_label_material, "LEFT",
            marker_collection
        )

# ─── 10. Leyenda lateral ─────────────────────────────────────
if USE_LEGEND_LIST:
    create_text_obj(
        "markers_legend_title",
        LEGEND_TITLE, LEGEND_X, LEGEND_Y, LEGEND_Z,
        LEGEND_TITLE_SIZE, marker_legend_material, "LEFT",
        marker_collection
    )
    for index, marker in enumerate(visible_markers):
        marker_id = marker.get("id", str(index + 1))
        name = marker.get("name", "")
        line_text = f"{marker_id}. {name}" if LEGEND_MODE == "id_name" else name
        create_text_obj(
            f"markers_legend_item_{marker_id}_{safe_obj_name(name)}",
            line_text,
            LEGEND_X,
            LEGEND_Y - ((index + 1) * LEGEND_LINE_SPACING),
            LEGEND_Z, LEGEND_ITEM_SIZE,
            marker_legend_material, "LEFT",
            marker_collection
        )

# ─── 11. Deseleccionar todo ──────────────────────────────────
for obj in bpy.context.scene.objects:
    obj.select_set(False)

# ─── 12. Resumen final ───────────────────────────────────────
print("\n" + "=" * 60)
print("  MAPA GENERADO CORRECTAMENTE")
print("=" * 60)
print(f"  Ciudad      : {city_label}")
print(f"  País        : {country_label}")
print(f"  Coordenadas : {coords_str}")
print(f"  Calles      : {road_count}")
print(f"  Tren        : {rail_count}")
print(f"  Agua        : {water_count}")
print(f"  Marcadores  : {len(visible_markers)}")
print("=" * 60 + "\n")
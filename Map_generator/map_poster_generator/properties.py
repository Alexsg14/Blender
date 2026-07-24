"""
properties.py — PropertyGroups del addon Map Poster Generator.

Define todos los datos de configuración almacenados en bpy.types.Scene,
incluyendo la lista dinámica de marcadores con edición completa desde la UI.
"""

import bpy
from bpy.props import (
    StringProperty,
    FloatProperty,
    IntProperty,
    BoolProperty,
    EnumProperty,
    CollectionProperty,
)
from bpy.types import PropertyGroup


# ─────────────────────────────────────────────────────────────────────────────
# Marcador individual
# ─────────────────────────────────────────────────────────────────────────────

class MapMarkerItem(PropertyGroup):
    """Un punto de interés en el mapa con su posición y opciones de etiqueta."""

    marker_id: StringProperty(
        name="ID",
        description="Identificador del marcador (número o texto corto)",
        default="1",
    )
    name: StringProperty(
        name="Name",
        description="Nombre del lugar que aparecerá en la etiqueta",
        default="Point of Interest",
    )
    lat: FloatProperty(
        name="Latitude",
        description="Latitud del punto (grados decimales)",
        default=0.0,
        min=-90.0,
        max=90.0,
        precision=6,
    )
    lon: FloatProperty(
        name="Longitude",
        description="Longitud del punto (grados decimales)",
        default=0.0,
        min=-180.0,
        max=180.0,
        precision=6,
    )
    offset_x: FloatProperty(
        name="Label Offset X",
        description="Desplazamiento horizontal de la etiqueta respecto al punto",
        default=0.45,
        soft_min=-3.0,
        soft_max=3.0,
        step=5,
    )
    offset_y: FloatProperty(
        name="Label Offset Y",
        description="Desplazamiento vertical de la etiqueta respecto al punto",
        default=0.25,
        soft_min=-3.0,
        soft_max=3.0,
        step=5,
    )
    marker_shape: EnumProperty(
        name="Shape",
        description="Forma del marcador en el mapa",
        items=[
            ("circle", "Circle", "Anillo exterior con punto central", "MESH_CIRCLE", 0),
            ("heart",  "Heart",  "Corazón relleno",                  "DECORATE",    1),
        ],
        default="circle",
    )


# ─────────────────────────────────────────────────────────────────────────────
# Propiedades principales del addon (almacenadas en bpy.types.Scene)
# ─────────────────────────────────────────────────────────────────────────────

class MapPosterProperties(PropertyGroup):

    # ── Modo de ubicación ────────────────────────────────────────────────────

    location_mode: EnumProperty(
        name="Location Mode",
        description="Cómo se define la zona del mapa",
        items=[
            ("CITY_NAME",     "City Name",         "Busca la ciudad por nombre (Nominatim)",    "WORLD_DATA",    0),
            ("CENTER_COORDS", "Coords + Radius",   "Centro lat/lon + radio en km",              "OBJECT_ORIGIN", 1),
            ("MANUAL_BBOX",   "Manual Bounding Box","Bounding box exacto (S, W, N, E)",         "SNAP_GRID",     2),
        ],
        default="CITY_NAME",
    )

    # ── Opción A: Nombre de ciudad ────────────────────────────────────────────

    city_name: StringProperty(
        name="City",
        description="Nombre de la ciudad o lugar (ej: 'Madrid, Spain')",
        default="Manchester, UK",
    )
    radius_km: FloatProperty(
        name="Radius (km)",
        description="Radio del mapa centrado en la ciudad",
        default=3.5,
        min=0.1,
        max=200.0,
        soft_max=50.0,
        step=10,
    )

    # ── Opción B: Coordenadas + radio ─────────────────────────────────────────

    center_lat: FloatProperty(
        name="Latitude",
        description="Latitud del centro del mapa",
        default=53.4808,
        min=-90.0,
        max=90.0,
        precision=6,
    )
    center_lon: FloatProperty(
        name="Longitude",
        description="Longitud del centro del mapa",
        default=-2.2426,
        min=-180.0,
        max=180.0,
        precision=6,
    )
    center_radius_km: FloatProperty(
        name="Radius (km)",
        description="Radio del mapa a partir del centro",
        default=3.5,
        min=0.1,
        max=200.0,
        soft_max=50.0,
        step=10,
    )

    # ── Opción C: BBOX manual ─────────────────────────────────────────────────

    bbox_south: FloatProperty(name="South", default=53.4550, min=-90.0,  max=90.0,  precision=6)
    bbox_west:  FloatProperty(name="West",  default=-2.2850, min=-180.0, max=180.0, precision=6)
    bbox_north: FloatProperty(name="North", default=53.5050, min=-90.0,  max=90.0,  precision=6)
    bbox_east:  FloatProperty(name="East",  default=-2.2000, min=-180.0, max=180.0, precision=6)

    # ── Tamaño del póster ─────────────────────────────────────────────────────

    poster_width: FloatProperty(
        name="Width",
        description="Ancho del póster en unidades de Blender",
        default=18.0, min=1.0, soft_max=60.0,
    )
    poster_height: FloatProperty(
        name="Height",
        description="Alto del póster en unidades de Blender",
        default=24.0, min=1.0, soft_max=80.0,
    )
    map_fill_x: FloatProperty(
        name="Fill X",
        description="Fracción del ancho del póster que ocupa el mapa",
        default=0.98, min=0.1, max=1.0, precision=2, subtype='FACTOR',
    )
    map_fill_y: FloatProperty(
        name="Fill Y",
        description="Fracción del alto del póster que ocupa el mapa",
        default=0.90, min=0.1, max=1.0, precision=2, subtype='FACTOR',
    )

    # ── Filtro de calles ──────────────────────────────────────────────────────

    highway_filter: StringProperty(
        name="Highway Filter",
        description="Tipos de vía a incluir (expresión regular Overpass)",
        default="motorway|trunk|primary|secondary|tertiary|unclassified",
    )

    # ── Grosor de líneas ──────────────────────────────────────────────────────

    normal_road_width: FloatProperty(
        name="Normal Road",
        description="Grosor de calles secundarias/terciarias",
        default=0.010, min=0.001, max=1.0, precision=3, step=0.1,
    )
    main_road_width: FloatProperty(
        name="Main Road",
        description="Grosor de vías principales (primary/secondary)",
        default=0.030, min=0.001, max=1.0, precision=3, step=0.1,
    )
    motorway_width: FloatProperty(
        name="Motorway",
        description="Grosor de autopistas (motorway/trunk)",
        default=0.050, min=0.001, max=1.0, precision=3, step=0.1,
    )
    rail_width: FloatProperty(
        name="Rail",
        description="Grosor de vías de tren",
        default=0.010, min=0.001, max=1.0, precision=3, step=0.1,
    )
    waterway_width: FloatProperty(
        name="Waterway",
        description="Grosor de ríos y canales",
        default=0.028, min=0.001, max=1.0, precision=3, step=0.1,
    )

    # ── Objetos de texto del póster ───────────────────────────────────────────

    text_city_obj: StringProperty(
        name="City Object",
        description="Nombre del objeto texto de Blender con el nombre de la ciudad",
        default="text_city",
    )
    text_country_obj: StringProperty(
        name="Country Object",
        description="Nombre del objeto texto de Blender con el país/subtítulo",
        default="text_country",
    )
    text_coords_obj: StringProperty(
        name="Coords Object",
        description="Nombre del objeto texto de Blender con las coordenadas",
        default="text_coords",
    )

    # ── Marcadores ────────────────────────────────────────────────────────────

    markers: CollectionProperty(
        name="Markers",
        description="Lista de puntos de interés a marcar en el mapa",
        type=MapMarkerItem,
    )
    marker_active_index: IntProperty(
        name="Active Marker",
        description="Índice del marcador activo en la lista",
        default=0,
        min=0,
    )

    # ── Estilo de marcadores ──────────────────────────────────────────────────

    marker_radius: FloatProperty(
        name="Marker Radius",
        description="Radio del marcador circular",
        default=0.10, min=0.01, max=2.0, step=1,
    )
    marker_ring_width: FloatProperty(
        name="Ring Width",
        description="Grosor del aro del marcador circular",
        default=0.018, min=0.001, max=0.5, step=0.1,
    )

    use_leader_labels: BoolProperty(
        name="Show Labels",
        description="Mostrar etiquetas de texto junto a cada marcador",
        default=True,
    )
    leader_label_size: FloatProperty(
        name="Label Size",
        description="Tamaño del texto de la etiqueta",
        default=0.16, min=0.01, max=2.0, step=1,
    )
    leader_label_mode: EnumProperty(
        name="Label Shows",
        description="Qué texto muestra la etiqueta junto al marcador",
        items=[
            ("name", "Name",     "Nombre completo del lugar"),
            ("id",   "ID",       "Solo el número/identificador"),
            ("both", "ID + Name","Número y nombre"),
        ],
        default="name",
    )
    leader_line_width: FloatProperty(
        name="Leader Line Width",
        description="Grosor de la línea guía desde el marcador hasta la etiqueta",
        default=0.006, min=0.001, max=0.1, step=0.1,
    )

    # ── Estado / log ──────────────────────────────────────────────────────────

    last_status: StringProperty(
        name="Status",
        description="Estado de la última operación",
        default="Ready",
    )


# ─────────────────────────────────────────────────────────────────────────────
# Register / Unregister
# ─────────────────────────────────────────────────────────────────────────────

_classes = [MapMarkerItem, MapPosterProperties]


def register():
    for cls in _classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.map_poster_props = bpy.props.PointerProperty(type=MapPosterProperties)


def unregister():
    del bpy.types.Scene.map_poster_props
    for cls in reversed(_classes):
        bpy.utils.unregister_class(cls)

"""
core/geometry.py — Creación de geometría 3D para el mapa.

Funciones para curvas de calles/ríos/tren, polígonos de agua,
marcadores (anillos, puntos, corazones), textos de etiquetas y líneas guía.
"""

import bpy
import math

from .scene import link_only_to_collection


# ─────────────────────────────────────────────────────────────────────────────
# Proyección lat/lon → XY de Blender
# ─────────────────────────────────────────────────────────────────────────────

def make_projection(bbox: tuple, poster_width: float, poster_height: float,
                    fill_x: float, fill_y: float):
    """
    Devuelve una función project(lon, lat) → (x, y) que transforma
    coordenadas geográficas al espacio 3D escalado del póster.
    """
    south, west, north, east = bbox
    center_lat = (south + north) / 2
    center_lon = (west  + east)  / 2

    def lonlat_to_xy(lon, lat):
        R = 6_371_000  # radio Tierra en metros
        x = math.radians(lon - center_lon) * R * math.cos(math.radians(center_lat))
        y = math.radians(lat - center_lat) * R
        return x, y

    corners = [
        lonlat_to_xy(west,  south),
        lonlat_to_xy(east,  south),
        lonlat_to_xy(west,  north),
        lonlat_to_xy(east,  north),
    ]
    min_x = min(p[0] for p in corners)
    max_x = max(p[0] for p in corners)
    min_y = min(p[1] for p in corners)
    max_y = max(p[1] for p in corners)

    scale = min(
        (poster_width  * fill_x) / (max_x - min_x),
        (poster_height * fill_y) / (max_y - min_y),
    )

    def project(lon, lat):
        x, y = lonlat_to_xy(lon, lat)
        return x * scale, y * scale

    return project


# ─────────────────────────────────────────────────────────────────────────────
# Utilidades de nombre
# ─────────────────────────────────────────────────────────────────────────────

def safe_obj_name(text: str) -> str:
    """Sanitiza un texto para usarlo como nombre de objeto en Blender."""
    for ch in '/\\:*?"<>|':
        text = text.replace(ch, "_")
    return text[:60]  # Blender limita nombres a ~63 chars


# ─────────────────────────────────────────────────────────────────────────────
# Grosor de calles según tipo
# ─────────────────────────────────────────────────────────────────────────────

def highway_style(tags: dict, props, mat_road, mat_main):
    """Devuelve (bevel_depth, material) según el tipo de carretera OSM."""
    road_type = tags.get("highway", "")
    if road_type == "motorway":
        return props.motorway_width, mat_main
    if road_type == "trunk":
        return props.motorway_width * 0.85, mat_main
    if road_type == "primary":
        return props.main_road_width, mat_main
    if road_type == "secondary":
        return props.main_road_width * 0.75, mat_main
    if road_type == "tertiary":
        return props.normal_road_width * 1.20, mat_road
    return props.normal_road_width, mat_road


# ─────────────────────────────────────────────────────────────────────────────
# Curva 3D (calles, tren, ríos)
# ─────────────────────────────────────────────────────────────────────────────

def create_curve_line(name: str, coords: list, bevel_depth: float,
                      material, collection, z: float = 0.05):
    """
    Crea una curva POLY 3D con bevel para representar calles, vías o ríos.
    """
    if len(coords) < 2:
        return None

    curve = bpy.data.curves.new(name, type="CURVE")
    curve.dimensions      = "3D"
    curve.resolution_u    = 2
    curve.bevel_depth     = bevel_depth
    curve.bevel_resolution = 1
    curve.fill_mode       = "FULL"
    curve.use_path        = True

    poly = curve.splines.new("POLY")
    poly.points.add(len(coords) - 1)
    for point, (x, y) in zip(poly.points, coords):
        point.co = (x, y, z, 1)

    obj = bpy.data.objects.new(name, curve)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(material)
    link_only_to_collection(obj, collection)
    return obj


# ─────────────────────────────────────────────────────────────────────────────
# Polígono relleno (masas de agua)
# ─────────────────────────────────────────────────────────────────────────────

def create_filled_polygon(name: str, coords: list, material, collection, z: float = 0.025):
    """
    Crea un mesh plano relleno para representar lagos y zonas de agua.
    """
    if len(coords) < 3:
        return None

    verts = [(x, y, z) for x, y in coords]
    if verts[0] != verts[-1]:
        verts.append(verts[0])
    face = list(range(len(verts) - 1))

    mesh = bpy.data.meshes.new(name)
    try:
        mesh.from_pydata(verts, [], [face])
        mesh.update()
    except Exception:
        return None

    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(material)
    link_only_to_collection(obj, collection)
    return obj


# ─────────────────────────────────────────────────────────────────────────────
# Marcadores
# ─────────────────────────────────────────────────────────────────────────────

def create_marker_ring(name: str, x: float, y: float, radius: float,
                        ring_width: float, material, collection, z: float):
    """Anillo toroidal (aro exterior del marcador circular)."""
    bpy.ops.mesh.primitive_torus_add(
        major_radius=radius,
        minor_radius=ring_width,
        major_segments=48,
        minor_segments=8,
        location=(x, y, z),
    )
    obj = bpy.context.object
    obj.name = name
    if material:
        obj.data.materials.append(material)
    link_only_to_collection(obj, collection)
    return obj


def create_marker_dot(name: str, x: float, y: float, radius: float,
                       material, collection, z: float):
    """Esfera aplanada (punto central del marcador circular)."""
    bpy.ops.mesh.primitive_uv_sphere_add(
        segments=24, ring_count=12,
        radius=radius,
        location=(x, y, z),
    )
    obj = bpy.context.object
    obj.name  = name
    obj.scale.z = 0.08  # Aplana la esfera para que parezca un disco
    if material:
        obj.data.materials.append(material)
    link_only_to_collection(obj, collection)
    return obj


def create_heart_marker(name: str, x: float, y: float, size: float,
                         material, collection, z: float):
    """
    Corazón como mesh relleno usando la ecuación paramétrica del corazón.
    """
    steps = 120
    verts_2d = []
    for i in range(steps):
        t = (2 * math.pi * i) / steps
        hx = 16 * (math.sin(t) ** 3)
        hy = (
            13 * math.cos(t)
            -  5 * math.cos(2 * t)
            -  2 * math.cos(3 * t)
            -      math.cos(4 * t)
        )
        verts_2d.append((x + (hx / 18.0) * size, y + (hy / 18.0) * size, z))

    center = (x, y, z)
    verts  = [center] + verts_2d
    faces  = [
        (0, i, (i % (len(verts) - 1)) + 1)
        for i in range(1, len(verts))
    ]

    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts, [], faces)
    mesh.update()

    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    if material:
        obj.data.materials.append(material)
    link_only_to_collection(obj, collection)
    return obj


# ─────────────────────────────────────────────────────────────────────────────
# Texto 3D (etiquetas de marcadores)
# ─────────────────────────────────────────────────────────────────────────────

def create_text_obj(name: str, body: str, x: float, y: float, z: float,
                     size: float, material, collection, align_x: str = "LEFT"):
    """Crea un objeto de texto 3D (tipo FONT) en la posición dada."""
    bpy.ops.object.text_add(location=(x, y, z), rotation=(0, 0, 0))
    obj = bpy.context.object
    obj.name          = name
    obj.data.body     = body
    obj.data.align_x  = align_x
    obj.data.align_y  = "CENTER"
    obj.data.size     = size
    obj.data.extrude  = 0.002
    if material:
        obj.data.materials.append(material)
    link_only_to_collection(obj, collection)
    return obj


# ─────────────────────────────────────────────────────────────────────────────
# Línea guía (leader line desde marcador hasta etiqueta)
# ─────────────────────────────────────────────────────────────────────────────

def create_leader_line(name: str, x1: float, y1: float, x2: float, y2: float,
                        material, collection, z: float, width: float):
    """Curva de dos puntos que conecta el marcador con su etiqueta."""
    curve = bpy.data.curves.new(name, type="CURVE")
    curve.dimensions      = "3D"
    curve.resolution_u    = 1
    curve.bevel_depth     = width
    curve.bevel_resolution = 0

    spline = curve.splines.new("POLY")
    spline.points.add(1)
    spline.points[0].co = (x1, y1, z, 1)
    spline.points[1].co = (x2, y2, z, 1)

    obj = bpy.data.objects.new(name, curve)
    bpy.context.collection.objects.link(obj)
    if material:
        obj.data.materials.append(material)
    link_only_to_collection(obj, collection)
    return obj

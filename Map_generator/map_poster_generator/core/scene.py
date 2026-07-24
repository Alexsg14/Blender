"""
core/scene.py — Gestión de colecciones, materiales y objetos de texto.

Todas las funciones son defensivas: nunca lanzan RuntimeError por elementos
que no existan en la escena; los crean automáticamente si es necesario.
"""

import bpy
import math


# ─────────────────────────────────────────────────────────────────────────────
# Colores predeterminados para materiales nuevos (RGBA lineal)
# ─────────────────────────────────────────────────────────────────────────────

_DEFAULT_COLORS = {
    "Roads":      (0.80, 0.78, 0.72, 1.0),   # Beige claro
    "Main Roads": (0.95, 0.90, 0.75, 1.0),   # Beige cálido
    "Rail":       (0.50, 0.50, 0.55, 1.0),   # Gris
    "Water":      (0.35, 0.60, 0.80, 1.0),   # Azul
    "Dots Stroke":(0.95, 0.80, 0.30, 1.0),   # Amarillo
    "Text":       (0.15, 0.15, 0.15, 1.0),   # Casi negro
}


# ─────────────────────────────────────────────────────────────────────────────
# Colecciones
# ─────────────────────────────────────────────────────────────────────────────

def get_or_create_collection(name: str):
    """
    Devuelve la colección con ese nombre.
    Si no existe, la crea y la vincula a la escena activa.
    """
    col = bpy.data.collections.get(name)
    if col is None:
        print(f"[SCENE] Colección '{name}' no encontrada → creando.")
        col = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(col)
    return col


def clear_collection_objects(collection):
    """
    Borra SOLO los objetos dentro de la colección.
    No borra la colección, materiales, cámara, luces ni textos del póster.
    """
    for obj in list(collection.objects):
        bpy.data.objects.remove(obj, do_unlink=True)


def link_only_to_collection(obj, target_collection):
    """Asegura que el objeto pertenece únicamente a target_collection."""
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


# ─────────────────────────────────────────────────────────────────────────────
# Materiales
# ─────────────────────────────────────────────────────────────────────────────

def get_or_create_material(name: str):
    """
    Devuelve el material con ese nombre.
    Si no existe, crea un Principled BSDF con el color del diccionario.
    Nunca modifica un material ya existente.
    """
    mat = bpy.data.materials.get(name)
    if mat is not None:
        return mat

    print(f"[SCENE] Material '{name}' no encontrado → creando con color predeterminado.")
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.location = (0, 0)
    color = _DEFAULT_COLORS.get(name, (0.8, 0.8, 0.8, 1.0))
    bsdf.inputs["Base Color"].default_value = color
    bsdf.inputs["Roughness"].default_value  = 1.0

    out = nodes.new("ShaderNodeOutputMaterial")
    out.location = (300, 0)
    links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])

    return mat


def get_or_fallback_material(name: str, fallback: str = None):
    """
    Busca el material. Si no existe, intenta el fallback.
    Si ninguno existe, lo crea automáticamente.
    """
    mat = bpy.data.materials.get(name)
    if mat is None and fallback:
        mat = bpy.data.materials.get(fallback)
    if mat is None:
        mat = get_or_create_material(name)
    return mat


# ─────────────────────────────────────────────────────────────────────────────
# Textos del póster
# ─────────────────────────────────────────────────────────────────────────────

def format_coords_dms(lat: float, lon: float) -> str:
    """
    Convierte lat/lon decimales a formato DMS estilizado para el póster.
    Ej: 53.4808, -2.2426 → "53° 28' N  •  2° 14' W"
    """
    def to_dm(deg):
        d = int(abs(deg))
        m = int((abs(deg) - d) * 60)
        return d, m

    lat_d, lat_m = to_dm(lat)
    lon_d, lon_m = to_dm(lon)
    lat_dir = "N" if lat >= 0 else "S"
    lon_dir = "E" if lon >= 0 else "W"
    return f"{lat_d}° {lat_m:02d}' {lat_dir}  •  {lon_d}° {lon_m:02d}' {lon_dir}"


def update_scene_text(obj_name: str, new_text: str):
    """
    Actualiza el body de un objeto de texto FONT si existe en la escena.
    Si el nombre está vacío, el texto es vacío, o el objeto no existe/no es
    de tipo FONT, se omite silenciosamente.
    """
    if not obj_name or not new_text:
        return
    obj = bpy.data.objects.get(obj_name)
    if obj is None:
        print(f"[TEXT] '{obj_name}' no existe en la escena (omitido).")
        return
    if obj.type != "FONT":
        print(f"[TEXT] '{obj_name}' no es tipo FONT (omitido).")
        return
    obj.data.body = new_text
    print(f"[TEXT] '{obj_name}' → '{new_text}'")

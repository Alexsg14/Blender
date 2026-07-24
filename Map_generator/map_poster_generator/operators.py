"""
operators.py — Operadores de Blender para el addon Map Poster Generator.

Operadores disponibles:
  map.generate             → Geocodifica + descarga OSM + genera geometría 3D
  map.clear_map            → Borra solo calles/tren/agua
  map.clear_all            → Borra mapa + marcadores
  map.add_marker           → Añade un marcador a la lista
  map.remove_marker        → Elimina el marcador activo
  map.move_marker_up/down  → Reordena la lista
  map.load_sample_markers  → Carga los marcadores de Manchester como ejemplo
  map.clear_markers        → Vacía la lista de marcadores
"""

import bpy
from bpy.types import Operator


# ─────────────────────────────────────────────────────────────────────────────
# Datos de los marcadores de muestra (Manchester)
# ─────────────────────────────────────────────────────────────────────────────

_MANCHESTER_MARKERS = [
    ("1",  "Cinnabon Deansgate",          53.4826,          -2.2475,          -1.15,  0.55, "circle"),
    ("2",  "Afflecks",                    53.4844,          -2.23326,          0.70,  0.65, "circle"),
    ("3",  "BeeHouse",                    53.4746,          -2.2502,          -1.10, -0.50, "circle"),
    ("4",  "Urban Playground / The Cube", 53.4742,          -2.2431,           0.25,  0.95, "circle"),
    ("5",  "Revolución de Cuba",          53.4783931,       -2.2488782,       -1.30,  0.05, "circle"),
    ("6",  "Hampton & Vouis Princess St", 53.479728,        -2.244286,         0.85,  0.35, "circle"),
    ("7",  "Another Heart To Feed",       53.4822,          -2.2352,           0.90, -0.10, "circle"),
    ("8",  "La Vie Cafe",                 53.4833563,       -2.2466934,       -1.25,  0.30, "circle"),
    ("9",  "Don Marco",                   53.4759033,       -2.2513928,       -1.10, -0.25, "circle"),
    ("10", "The Quadrangle",              53.47268035610678,-2.241007701243298, 0.45,  0.25, "heart"),
    ("11", "The Bridge",                  53.48307043162128,-2.2515250823844317,0.45,  0.25, "heart"),
    ("12", "MOJO Manchester",             53.4812722,       -2.24981,         -1.15,  0.45, "circle"),
    ("13", "Maki & Ramen NQ",             53.48427,         -2.237577,         0.85,  0.10, "circle"),
    ("14", "La Bandera",                  53.4801,          -2.2495,          -1.20, -0.15, "circle"),
    ("15", "Crown Square, Spinningfields",53.4804448,       -2.2520667,       -1.20,  0.20, "circle"),
    ("16", "NQ64 Northern Quarter",       53.4824604,       -2.2366911,        0.80, -0.30, "circle"),
    ("17", "The Alchemist Spinningfields",53.4798,          -2.2507,          -1.25,  0.05, "circle"),
    ("18", "Albert's Schloss Manchester", 53.4782,          -2.24791,          0.65, -0.35, "circle"),
]


# ─────────────────────────────────────────────────────────────────────────────
# Operador principal: generar el mapa completo
# ─────────────────────────────────────────────────────────────────────────────

class MAP_OT_generate(Operator):
    bl_idname      = "map.generate"
    bl_label       = "Generate Map"
    bl_description = ("Descarga datos de OpenStreetMap y genera el mapa 3D completo. "
                      "Requiere conexión a Internet. Puede tardar 30-90 segundos.")
    bl_options     = {'REGISTER', 'UNDO'}

    def execute(self, context):
        props = context.scene.map_poster_props

        # Importaciones locales para evitar import circular al cargar el addon
        from .core.geocoding import resolve_location
        from .core.osm       import download_osm, parse_osm
        from .core.scene     import (
            get_or_create_collection,
            get_or_create_material,
            get_or_fallback_material,
            clear_collection_objects,
            format_coords_dms,
            update_scene_text,
            link_only_to_collection,
        )
        from .core.geometry  import (
            make_projection,
            safe_obj_name,
            highway_style,
            create_curve_line,
            create_filled_polygon,
            create_marker_ring,
            create_marker_dot,
            create_heart_marker,
            create_text_obj,
            create_leader_line,
        )

        try:
            # ── 1. Resolver ubicación ─────────────────────────────────────────
            props.last_status = "Resolving location..."
            bbox, city_label, country_label, c_lat, c_lon = resolve_location(props)
            south, west, north, east = bbox

            # ── 2. Actualizar textos del póster ───────────────────────────────
            coords_str = format_coords_dms(c_lat, c_lon)
            update_scene_text(props.text_city_obj,    city_label)
            update_scene_text(props.text_country_obj, country_label)
            update_scene_text(props.text_coords_obj,  coords_str)

            # ── 3. Colecciones y materiales (sin fallo) ───────────────────────
            roads_col  = get_or_create_collection("Roads")
            rail_col   = get_or_create_collection("Rail")
            water_col  = get_or_create_collection("Water")

            mat_road  = get_or_create_material("Roads")
            mat_main  = get_or_create_material("Main Roads")
            mat_rail  = get_or_create_material("Rail")
            mat_water = get_or_create_material("Water")
            mat_marker       = get_or_fallback_material("Dots Stroke", "Text")
            mat_marker_label = get_or_fallback_material("Text", "Dots Stroke")

            # ── 4. Descargar OpenStreetMap ────────────────────────────────────
            props.last_status = "Downloading OSM data..."
            osm_data      = download_osm(bbox, props.highway_filter)
            nodes, ways   = parse_osm(osm_data)

            # ── 5. Borrar geometría anterior ──────────────────────────────────
            clear_collection_objects(roads_col)
            clear_collection_objects(rail_col)
            clear_collection_objects(water_col)

            # ── 6. Proyección geográfica ──────────────────────────────────────
            project = make_projection(
                bbox,
                props.poster_width, props.poster_height,
                props.map_fill_x,   props.map_fill_y,
            )

            # ── 7. Generar geometría de calles / tren / agua ──────────────────
            props.last_status = "Building geometry..."
            road_count = rail_count = water_count = 0

            for way in ways:
                tags     = way.get("tags", {})
                node_ids = way.get("nodes", [])
                coords   = [
                    project(nodes[nid][0], nodes[nid][1])
                    for nid in node_ids
                    if nid in nodes
                ]
                if len(coords) < 2:
                    continue

                if "highway" in tags:
                    width, mat = highway_style(tags, props, mat_road, mat_main)
                    create_curve_line("road", coords, width, mat, roads_col, z=0.08)
                    road_count += 1

                elif "railway" in tags:
                    create_curve_line("rail", coords, props.rail_width, mat_rail, rail_col, z=0.07)
                    rail_count += 1

                elif "waterway" in tags:
                    create_curve_line("waterway", coords, props.waterway_width, mat_water, water_col, z=0.06)
                    water_count += 1

                elif tags.get("natural") == "water" or "water" in tags:
                    create_filled_polygon("water", coords, mat_water, water_col, z=0.04)
                    water_count += 1

            # ── 8. Colección de marcadores ────────────────────────────────────
            marker_col = bpy.data.collections.get("Markers")
            if marker_col is None:
                marker_col = bpy.data.collections.new("Markers")
                bpy.context.scene.collection.children.link(marker_col)
            else:
                for obj in list(marker_col.objects):
                    bpy.data.objects.remove(obj, do_unlink=True)

            MARKER_Z     = 0.22
            LEADER_Z     = 0.235
            LABEL_Z      = 0.27
            LEADER_WIDTH = props.leader_line_width

            # ── 9. Generar marcadores ─────────────────────────────────────────
            marker_count = 0
            for marker in props.markers:
                lat, lon = marker.lat, marker.lon
                if not (south <= lat <= north and west <= lon <= east):
                    continue

                x, y       = project(lon, lat)
                safe_name  = safe_obj_name(marker.name)
                mid        = marker.marker_id

                if marker.marker_shape == "heart":
                    create_heart_marker(
                        f"marker_heart_{mid}_{safe_name}",
                        x, y, props.marker_radius * 1.65,
                        mat_marker, marker_col, MARKER_Z + 0.01,
                    )
                else:
                    create_marker_ring(
                        f"marker_ring_{mid}_{safe_name}",
                        x, y, props.marker_radius, props.marker_ring_width,
                        mat_marker, marker_col, MARKER_Z,
                    )
                    create_marker_dot(
                        f"marker_dot_{mid}_{safe_name}",
                        x, y, props.marker_radius * 0.22,
                        mat_marker, marker_col, MARKER_Z + 0.01,
                    )

                if props.use_leader_labels:
                    lx = x + marker.offset_x
                    ly = y + marker.offset_y

                    mode = props.leader_label_mode
                    if mode == "id":
                        label_body = mid
                    elif mode == "both":
                        label_body = f"{mid} {marker.name}"
                    else:
                        label_body = marker.name

                    create_leader_line(
                        f"marker_line_{mid}_{safe_name}",
                        x, y, lx, ly,
                        mat_marker, marker_col, LEADER_Z, LEADER_WIDTH,
                    )
                    create_text_obj(
                        f"marker_label_{mid}_{safe_name}",
                        label_body, lx, ly, LABEL_Z,
                        props.leader_label_size, mat_marker_label, marker_col,
                    )

                marker_count += 1

            # ── 10. Deseleccionar todo ────────────────────────────────────────
            for obj in bpy.context.scene.objects:
                obj.select_set(False)

            # ── 11. Resumen ───────────────────────────────────────────────────
            status = (
                f"Done ✓  Roads:{road_count}  "
                f"Rail:{rail_count}  Water:{water_count}  "
                f"Markers:{marker_count}"
            )
            props.last_status = status
            self.report({'INFO'}, status)
            print(f"\n[MAP] {status}\n")

        except Exception as exc:
            msg = str(exc)
            props.last_status = f"Error: {msg[:60]}"
            self.report({'ERROR'}, msg)
            import traceback
            traceback.print_exc()
            return {'CANCELLED'}

        return {'FINISHED'}


# ─────────────────────────────────────────────────────────────────────────────
# Operadores de limpieza
# ─────────────────────────────────────────────────────────────────────────────

class MAP_OT_clear_map(Operator):
    bl_idname      = "map.clear_map"
    bl_label       = "Clear Map"
    bl_description = "Elimina la geometría del mapa (calles, tren, agua) sin borrar marcadores ni póster"
    bl_options     = {'REGISTER', 'UNDO'}

    def execute(self, context):
        from .core.scene import clear_collection_objects
        cleared = 0
        for col_name in ("Roads", "Rail", "Water"):
            col = bpy.data.collections.get(col_name)
            if col:
                cleared += len(col.objects)
                clear_collection_objects(col)
        self.report({'INFO'}, f"Map cleared ({cleared} objects removed)")
        context.scene.map_poster_props.last_status = "Map cleared"
        return {'FINISHED'}


class MAP_OT_clear_all(Operator):
    bl_idname      = "map.clear_all"
    bl_label       = "Clear All"
    bl_description = "Elimina mapa completo y marcadores"
    bl_options     = {'REGISTER', 'UNDO'}

    def execute(self, context):
        from .core.scene import clear_collection_objects
        cleared = 0
        for col_name in ("Roads", "Rail", "Water", "Markers"):
            col = bpy.data.collections.get(col_name)
            if col:
                cleared += len(col.objects)
                clear_collection_objects(col)
        self.report({'INFO'}, f"All cleared ({cleared} objects removed)")
        context.scene.map_poster_props.last_status = "All cleared"
        return {'FINISHED'}


# ─────────────────────────────────────────────────────────────────────────────
# Operadores de gestión de marcadores
# ─────────────────────────────────────────────────────────────────────────────

class MAP_OT_add_marker(Operator):
    bl_idname      = "map.add_marker"
    bl_label       = "Add Marker"
    bl_description = "Añade un nuevo marcador vacío a la lista"

    def execute(self, context):
        props  = context.scene.map_poster_props
        marker = props.markers.add()
        marker.marker_id = str(len(props.markers))
        marker.name      = "New Marker"
        props.marker_active_index = len(props.markers) - 1
        return {'FINISHED'}


class MAP_OT_remove_marker(Operator):
    bl_idname      = "map.remove_marker"
    bl_label       = "Remove Marker"
    bl_description = "Elimina el marcador seleccionado en la lista"

    def execute(self, context):
        props = context.scene.map_poster_props
        idx   = props.marker_active_index
        if 0 <= idx < len(props.markers):
            props.markers.remove(idx)
            props.marker_active_index = max(0, idx - 1)
        return {'FINISHED'}


class MAP_OT_move_marker_up(Operator):
    bl_idname      = "map.move_marker_up"
    bl_label       = "Move Up"
    bl_description = "Mueve el marcador hacia arriba en la lista"

    def execute(self, context):
        props = context.scene.map_poster_props
        idx   = props.marker_active_index
        if idx > 0:
            props.markers.move(idx, idx - 1)
            props.marker_active_index -= 1
        return {'FINISHED'}


class MAP_OT_move_marker_down(Operator):
    bl_idname      = "map.move_marker_down"
    bl_label       = "Move Down"
    bl_description = "Mueve el marcador hacia abajo en la lista"

    def execute(self, context):
        props = context.scene.map_poster_props
        idx   = props.marker_active_index
        if idx < len(props.markers) - 1:
            props.markers.move(idx, idx + 1)
            props.marker_active_index += 1
        return {'FINISHED'}


class MAP_OT_load_sample_markers(Operator):
    bl_idname      = "map.load_sample_markers"
    bl_label       = "Load Manchester Sample"
    bl_description = "Carga los 18 marcadores originales de Manchester como punto de partida"

    def execute(self, context):
        props = context.scene.map_poster_props
        props.markers.clear()

        for mid, name, lat, lon, ox, oy, shape in _MANCHESTER_MARKERS:
            m            = props.markers.add()
            m.marker_id  = mid
            m.name       = name
            m.lat        = lat
            m.lon        = lon
            m.offset_x   = ox
            m.offset_y   = oy
            m.marker_shape = shape

        props.marker_active_index = 0
        self.report({'INFO'}, f"Loaded {len(props.markers)} Manchester markers")
        return {'FINISHED'}


class MAP_OT_clear_markers(Operator):
    bl_idname      = "map.clear_markers"
    bl_label       = "Clear Marker List"
    bl_description = "Vacía la lista de marcadores (no borra los objetos 3D de la escena)"

    def execute(self, context):
        props = context.scene.map_poster_props
        props.markers.clear()
        props.marker_active_index = 0
        return {'FINISHED'}


# ─────────────────────────────────────────────────────────────────────────────
# Register / Unregister
# ─────────────────────────────────────────────────────────────────────────────

_classes = [
    MAP_OT_generate,
    MAP_OT_clear_map,
    MAP_OT_clear_all,
    MAP_OT_add_marker,
    MAP_OT_remove_marker,
    MAP_OT_move_marker_up,
    MAP_OT_move_marker_down,
    MAP_OT_load_sample_markers,
    MAP_OT_clear_markers,
]


def register():
    for cls in _classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(_classes):
        bpy.utils.unregister_class(cls)

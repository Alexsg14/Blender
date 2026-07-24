"""
panel.py — Panel UI del addon Map Poster Generator.

Ubicación: View3D > N-Panel > pestaña "Map Poster"

Secciones:
  - Location: modo de búsqueda (ciudad, coordenadas, BBOX manual)
  - Poster: tamaño y escala
  - Streets: filtro y grosores de línea
  - Poster Texts: nombres de objetos de texto a actualizar
  - Markers: UIList con editor inline del marcador activo
  - Marker Style: radio, etiquetas
  - Actions: botones Generar / Limpiar
"""

import bpy
from bpy.types import Panel, UIList


# ─────────────────────────────────────────────────────────────────────────────
# UIList de marcadores
# ─────────────────────────────────────────────────────────────────────────────

class MAP_UL_markers(UIList):
    """Lista de marcadores con ID, nombre y forma visible directamente."""

    def draw_item(self, context, layout, data, item, icon,
                  active_data, active_propname, index):
        row = layout.row(align=True)

        # Icono según forma
        shape_icon = "DECORATE" if item.marker_shape == "heart" else "MESH_CIRCLE"
        row.label(text="", icon=shape_icon)

        # ID editable (corto)
        row.prop(item, "marker_id", text="", emboss=False, icon_value=0)

        # Nombre del marcador
        row.prop(item, "name", text="", emboss=False)

    def filter_items(self, context, data, propname):
        # Sin filtrado personalizado; usa el orden por defecto
        return [], []


# ─────────────────────────────────────────────────────────────────────────────
# Panel principal
# ─────────────────────────────────────────────────────────────────────────────

class MAP_PT_main(Panel):
    bl_label      = "Map Poster Generator"
    bl_idname     = "MAP_PT_main"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category   = "Map Poster"

    def draw_header(self, context):
        self.layout.label(text="", icon='WORLD_DATA')

    def draw(self, context):
        layout = self.layout
        props  = context.scene.map_poster_props

        # ── Ubicación ──────────────────────────────────────────────────────────
        box = layout.box()
        row = box.row()
        row.label(text="Location", icon='WORLD_DATA')

        box.prop(props, "location_mode", text="")

        if props.location_mode == 'CITY_NAME':
            box.prop(props, "city_name",  icon='VIEWZOOM')
            box.prop(props, "radius_km")

        elif props.location_mode == 'CENTER_COORDS':
            row = box.row(align=True)
            row.prop(props, "center_lat", text="Lat")
            row.prop(props, "center_lon", text="Lon")
            box.prop(props, "center_radius_km")

        else:  # MANUAL_BBOX
            col = box.column(align=True)
            col.prop(props, "bbox_north", text="North ↑")
            row = col.row(align=True)
            row.prop(props, "bbox_west",  text="← West")
            row.prop(props, "bbox_east",  text="East →")
            col.prop(props, "bbox_south", text="South ↓")

        # ── Póster ─────────────────────────────────────────────────────────────
        box = layout.box()
        row = box.row()
        row.label(text="Poster", icon='IMAGE_DATA')
        row = box.row(align=True)
        row.prop(props, "poster_width",  text="W")
        row.prop(props, "poster_height", text="H")
        row = box.row(align=True)
        row.prop(props, "map_fill_x", slider=True, text="Fill X")
        row.prop(props, "map_fill_y", slider=True, text="Fill Y")

        # ── Calles ─────────────────────────────────────────────────────────────
        box = layout.box()
        header = box.row()
        header.label(text="Streets", icon='CURVE_PATH')

        box.prop(props, "highway_filter", text="Filter")

        col = box.column(align=True)
        col.prop(props, "normal_road_width", text="Normal Road")
        col.prop(props, "main_road_width",   text="Main Road")
        col.prop(props, "motorway_width",    text="Motorway")
        col.separator()
        col.prop(props, "rail_width",       text="Rail")
        col.prop(props, "waterway_width",   text="Waterway")

        # ── Textos del póster ──────────────────────────────────────────────────
        box = layout.box()
        row = box.row()
        row.label(text="Poster Text Objects", icon='FONT_DATA')
        box.label(text="Leave blank to skip update", icon='INFO')
        box.prop(props, "text_city_obj",    text="City")
        box.prop(props, "text_country_obj", text="Country")
        box.prop(props, "text_coords_obj",  text="Coords")

        # ── Marcadores ─────────────────────────────────────────────────────────
        box = layout.box()
        row = box.row()
        row.label(text="Markers", icon='PINNED')

        # Lista + botones laterales
        row = box.row()
        row.template_list(
            "MAP_UL_markers", "",
            props, "markers",
            props, "marker_active_index",
            rows=5,
        )

        col = row.column(align=True)
        col.operator("map.add_marker",       icon='ADD',    text="")
        col.operator("map.remove_marker",    icon='REMOVE', text="")
        col.separator()
        col.operator("map.move_marker_up",   icon='TRIA_UP',   text="")
        col.operator("map.move_marker_down", icon='TRIA_DOWN',  text="")
        col.separator()
        col.operator("map.clear_markers",    icon='X', text="")

        # Editor del marcador activo
        if props.markers and 0 <= props.marker_active_index < len(props.markers):
            m   = props.markers[props.marker_active_index]
            sub = box.box()
            sub.label(text=f"Editing: #{m.marker_id}", icon='GREASEPENCIL')

            row = sub.row(align=True)
            row.prop(m, "marker_id", text="ID")
            row.prop(m, "marker_shape", text="")

            sub.prop(m, "name", text="Name")

            row = sub.row(align=True)
            row.prop(m, "lat", text="Lat")
            row.prop(m, "lon", text="Lon")

            row = sub.row(align=True)
            row.prop(m, "offset_x", text="Label ↔")
            row.prop(m, "offset_y", text="Label ↕")

        # Botones de carga de muestra
        row = box.row(align=True)
        row.operator("map.load_sample_markers", icon='IMPORT', text="Load Manchester Sample")

        # ── Estilo de marcadores ───────────────────────────────────────────────
        box = layout.box()
        row = box.row()
        row.label(text="Marker Style", icon='OBJECT_DATA')
        box.prop(props, "marker_radius")
        box.prop(props, "marker_ring_width")
        box.prop(props, "use_leader_labels")
        if props.use_leader_labels:
            box.prop(props, "leader_label_size")
            box.prop(props, "leader_label_mode")
            box.prop(props, "leader_line_width")

        # ── Botones de acción ──────────────────────────────────────────────────
        layout.separator()

        col = layout.column(align=True)
        col.scale_y = 1.8
        col.operator("map.generate", icon='WORLD_DATA', text="Generate Map")

        row = layout.row(align=True)
        row.scale_y = 1.2
        row.operator("map.clear_map", icon='TRASH', text="Clear Map")
        row.operator("map.clear_all", icon='X',     text="Clear All")

        # ── Estado ────────────────────────────────────────────────────────────
        layout.separator()
        status_row = layout.row()
        icon = 'ERROR' if props.last_status.startswith("Error") else 'INFO'
        status_row.label(text=props.last_status, icon=icon)


# ─────────────────────────────────────────────────────────────────────────────
# Register / Unregister
# ─────────────────────────────────────────────────────────────────────────────

_classes = [MAP_UL_markers, MAP_PT_main]


def register():
    for cls in _classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(_classes):
        bpy.utils.unregister_class(cls)

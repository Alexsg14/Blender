"""
Map Poster Generator - Blender Addon
Genera pósters cartográficos 3D a partir de datos de OpenStreetMap.
Compatible con Blender 4.2+
"""

bl_info = {
    "name": "Map Poster Generator",
    "author": "Map Poster Generator",
    "version": (1, 0, 0),
    "blender": (4, 2, 0),
    "location": "View3D > N-Panel > Map Poster",
    "description": "Generate 3D map posters from OpenStreetMap data for any city in the world",
    "doc_url": "",
    "category": "3D View",
}

from . import properties, operators, panel


def register():
    properties.register()
    operators.register()
    panel.register()


def unregister():
    panel.unregister()
    operators.unregister()
    properties.unregister()

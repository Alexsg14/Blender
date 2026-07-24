# 🗺️ Universal Map Poster Generator para Blender

Script y plantilla en Blender para generar pósters cartográficos 3D estilizados a partir de datos vectoriales de **OpenStreetMap** de cualquier ciudad o coordenada del mundo.

---

## 🚀 Características Principales

- **Descarga de Datos OSM**: Obtiene carreteras, edificios, agua y áreas verdes mediante consultas a la API de Overpass/OpenStreetMap.
- **Búsqueda por Ciudad o Coordenadas**: Permite especificar el nombre de una ciudad o pares de coordenadas latitud/longitud con un radio de mapa en kilómetros.
- **Generación de Mallas 3D**: Convierte elementos 2D de mapas en mallas 3D extrusionadas con materiales y colores temáticos (mapas oscuros, minimalistas, vintage, etc.).
- **Etiquetas y Leyendas**: Crea composiciones de póster listas para renderizar.

---

## 📖 Uso

1. Abre Blender con la plantilla [`Mapa_Manchester_Loli_workspace2_bck_update_zoom_and_labels.blend`](file:///home/ciqus/GIT/Github_Personal/Blender/Map_generator/Mapa_Manchester_Loli_workspace2_bck_update_zoom_and_labels.blend) o una escena limpia.
2. Abre el script [`map_scripting_generator.py`](file:///home/ciqus/GIT/Github_Personal/Blender/Map_generator/map_scripting_generator.py) en el Editor de Texto.
3. Ajusta la variable de ciudad/coordenadas en la sección de configuración.
4. Ejecuta el script (`Alt + P`).

# 🎨 Blender 3D Tools & Add-ons

Colección de scripts en Python, add-ons personalizados y herramientas procedimentales para **Blender (4.0+)**, enfocados principalmente en **visualización científica** (estructuras biológicas, metadinámica, moléculas) y **generación de mapas cartográficos 3D**.

---

## 📂 Contenido del Repositorio

| Proyecto | Tipo | Descripción | Link |
| :--- | :--- | :--- | :--- |
| **Molecule of the Month** | Script Automatizado | Scraper e importador PDB que convierte estructuras de RCSB PDB101 en mallas estáticas `.glb`. | [`Molecule_Of_The_Month/`](file:///home/ciqus/GIT/Github_Personal/Blender/Molecule_Of_The_Month/) |
| **Molecule Builder** | Add-on de Blender | Herramienta para construir y animar mallas atómicas (radios CPK) y enlaces dinámicos estirables. | [`_molecules_addon_/`](file:///home/ciqus/GIT/Github_Personal/Blender/_molecules_addon_/) |
| **Metadynamics Animator** | Add-on de Blender | Visualizador 3D de paisajes de energía libre (PES) y trayectorias de simulación de metadinámica 2D. | [`_metadyn_animator_/`](file:///home/ciqus/GIT/Github_Personal/Blender/_metadyn_animator_/) |
| **Map Poster Generator** | Generador Procedimental | Generador de pósters 3D cartográficos a partir de datos vectoriales de OpenStreetMap. | [`Map_generator/`](file:///home/ciqus/GIT/Github_Personal/Blender/Map_generator/) |

---

## 🛠️ Requisitos Generales

- **Blender 4.0+** (Recomendado Blender 4.2+).
- **Molecular Nodes** (para las herramientas moleculares).
- Conexión a Internet (para descarga de PDB/CIF y consultas a OpenStreetMap Overpass API).

---

## 📖 Resumen de Proyectos

### 🧬 [Molecule of the Month](file:///home/ciqus/GIT/Github_Personal/Blender/Molecule_Of_The_Month/README.md)
Script [`motm_blender_pro.py`](file:///home/ciqus/GIT/Github_Personal/Blender/Molecule_Of_The_Month/motm_blender_pro.py) que detecta el PDB destacado de RCSB PDB101, lo importa en estilo *cartoon*, aplica los modificadores para convertirlo a una malla limpia (`MESH`), le asigna un material sólido en espacio de color Linear RGB y permite exportarlo directamente a `.glb`.

### ⚛️ [Molecule Builder Add-on](file:///home/ciqus/GIT/Github_Personal/Blender/_molecules_addon_/README.md)
Add-on en el N-Panel de Blender ([`molecule_builder.py`](file:///home/ciqus/GIT/Github_Personal/Blender/_molecules_addon_/molecule_builder.py)) que permite crear átomos individuales (H, C, N, O, P, S, F, Cl, Br o personalizados) y unirlos con enlaces sencillos, dobles o triples mediante restricciones `STRETCH_TO` para animaciones reactivas.

### 📈 [Metadynamics Animator Add-on](file:///home/ciqus/GIT/Github_Personal/Blender/_metadyn_animator_/README.md)
Add-on ([`metadyn_animator.py`](file:///home/ciqus/GIT/Github_Personal/Blender/_metadyn_animator_/metadyn_animator.py)) enfocado en simular la adición de colinas gaussianas de potencial sobre un perfil de energía (PES), animando el movimiento del caminante (*walker*) con cámara y materiales de nivel de presentación.

### 🗺️ [Map Poster Generator](file:///home/ciqus/GIT/Github_Personal/Blender/Map_generator/README.md)
Sistema de scripts para construir representaciones 3D de ciudades extrusionadas (carreteras, edificios, agua, vegetación) a partir del nombre de una ciudad o coordenadas geográficas.

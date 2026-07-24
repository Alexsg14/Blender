# 🧬 PDB Molecule of the Month -> Blender (motm_blender_pro.py)

Script en Python para **Blender (4.0+)** que automatiza la obtención, renderizado en 3D y exportación a mallas `.glb` estáticas de la estructura biológica destacada en **RCSB PDB101 ("Molecule of the Month")**.

---

## 🚀 Características Principales

- **Scraping Automático de PDB101**: Conecta directamente con la API / Web de RCSB PDB101 para detectar el código PDB de la molécula del mes (con fallback a `7A4W` si falla la red).
- **Integración con Molecular Nodes**: Utiliza el complemento *Molecular Nodes* para generar la representación en estilo `cartoon`.
- **Conversión a Malla Estática (`MESH`)**: Aplica y congela automáticamente los modificadores de Geometry Nodes, desacoplando la molécula del addon.
- **Material Sólido Limpio**: Sustituye shaders complejos por un nodo `Principled BSDF` con un color aleatorio vibrante convertido fielmente de HSV a **Linear RGB**.
- **Alineación y Centrado**: Reubica el origen del objeto en su centro de masa en el origen `(0, 0, 0)`.
- **Exportación Automática GLB**: Opciones para exportar directamente archivos `.glb` optimizados para la web o visores 3D.
- **Compatibilidad Multi-Versión**: Compatible con Blender 3.6, 4.0, 4.1 y **4.2+** (soporta `wm.gltf_export` y `temp_override` en modo headless).

---

## 🛠️ Requisitos

- **Blender 4.0+** (Recomendado 4.2+).
- **Extension/Add-on Molecular Nodes** instalado en Blender.
- Conexión a Internet (para scraping y descarga de archivos PDB/CIF).

---

## 📖 Uso y Ejecución

### 1. Desde la Interfaz de Blender (GUI)
1. Abre Blender.
2. Ve a la pestaña **Text Editor** (Editor de Texto).
3. Abre el archivo [`motm_blender_pro.py`](file:///home/ciqus/GIT/Github_Personal/Blender/motm_blender_pro.py).
4. Haz clic en **Run Script** (`Alt + P`).

### 2. Desde la Terminal / Línea de Comandos

- **Modo Interactivo (Abre Blender y ejecuta el script)**:
  ```bash
  blender --python motm_blender_pro.py
  ```

- **Modo Background / Headless (Sin GUI, ideal para servidores y pipelines)**:
  Para activar la exportación automática a `.glb`, asegúrate de tener `GLB_EXPORT = True` en la configuración del script y ejecuta:
  ```bash
  blender -b --python motm_blender_pro.py
  ```

---

## ⚙️ Configuración del Script

En las primeras líneas de [`motm_blender_pro.py`](file:///home/ciqus/GIT/Github_Personal/Blender/motm_blender_pro.py) puedes ajustar los siguientes parámetros:

```python
ROUGHNESS       = 1.0    # Rugosidad del material (0.0 a 1.0)
TRANSMISSION    = 0.0    # Transmisión (0.0 = opaco, 1.0 = cristal/transparente)
FALLBACK_PDB_ID = "7A4W" # ID PDB alternativo si falla el scraping
GLB_EXPORT      = False  # Cambiar a True para exportar automáticamente a .glb
GLB_OUTPUT_DIR  = tempfile.gettempdir() # Directorio de destino para el archivo .glb
```

---

## 📂 Estructura del Repositorio

El repositorio incluye herramientas adicionales organizadas en subdirectorios:

- **[`motm_blender_pro.py`](file:///home/ciqus/GIT/Github_Personal/Blender/motm_blender_pro.py)**: Script automatizado PDB MOTM a MESH/GLB.
- **[`_molecules_addon_/`](file:///home/ciqus/GIT/Github_Personal/Blender/_molecules_addon_/)**: Addon *Molecule Builder* para construir y animar átomos y enlaces dinámicos en Blender.
- **[`_metadyn_animator_/`](file:///home/ciqus/GIT/Github_Personal/Blender/_metadyn_animator_/)**: Addon *Metadynamics Animator* para visualizar simulación de metadinámica 2D.
- **[`Map_generator/`](file:///home/ciqus/GIT/Github_Personal/Blender/Map_generator/)**: Generador de pósters cartográficos 3D con datos de OpenStreetMap.

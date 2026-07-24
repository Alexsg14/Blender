# ⚛️ Molecule Builder Add-on para Blender

Add-on de Python para Blender que permite construir, personalizar y animar estructuras moleculares 3D (átomos y enlaces dinámicos) con materiales realistas y restricciones de seguimiento (*constraints*).

---

## 🚀 Características Principales

- **Biblioteca de Elementos**: Incluye parámetros preconfigurados para `H`, `C`, `N`, `O`, `P`, `S`, `F`, `Cl`, `Br` (radios atómicos CPK y paleta de colores).
- **Átomos Personalizados**: Posibilidad de definir elementos customizados con radio y color a medida.
- **Enlaces Dinámicos (*Dynamic Bonds*)**:
  - Enlaces sencillos, dobles y triples.
  - Utiliza `COPY_LOCATION` y `STRETCH_TO` para que los cilindros de los enlaces se estiren y orienten automáticamente al mover o animar los átomos.
- **Animación Molecular**: Genera interpolaciones y movimiento armónico / vibratorio de enlaces para presentaciones.
- **Interfaz Integrada**: Panel dedicado en el **Sidebar del View3D (N-Panel)** bajo la pestaña `Molécula`.

---

## 🛠️ Instalación

1. En Blender, ve a **Edit > Preferences > Add-ons**.
2. Haz clic en el menú desplegable superior derecho y selecciona **Install from Disk...**
3. Selecciona el archivo [`molecule_builder.py`](file:///home/ciqus/GIT/Github_Personal/Blender/_molecules_addon_/molecule_builder.py).
4. Activa la casilla junto a **Molecule Builder**.

---

## 📖 Uso

1. Abre el panel lateral presionando `N` en la vista 3D.
2. Haz clic en la pestaña **Molécula**.
3. Selecciona el tipo de elemento y haz clic en **Añadir Átomo**.
4. Selecciona dos átomos en la escena y presiona **Crear Enlace** para conectarlos dinámicamente.

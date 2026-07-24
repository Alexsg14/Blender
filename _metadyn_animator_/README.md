# 📈 Metadynamics Animator Add-on para Blender

Add-on de animación 3D en Blender diseñado para crear visualizaciones estéticas de Superficies de Energía Potencial (PES) y simular trayectorias de **Metadinámica 2D**.

---

## 🚀 Características Principales

- **Simulación 2D de Metadinámica**: Representa el avance del caminante (*walker*) agregando colinas gaussianas de potencial a lo largo de la coordenada de reacción.
- **Gráficos 3D Estilizados**: Genera mallas de rejilla, perfil de energía, capas de sombreado y efectos de iluminación optimizados para pósters o vídeos científicos.
- **Cámara y Configuración Automática**: Configura la vista ortográfica o en perspectiva alineada con el eje Z (energía) frente a X (CV).
- **Control por N-Panel**: Panel lateral en `View3D > Metadyn` para controlar parámetros de simulación (número de colinas, altura, ancho, velocidad de animación).

---

## 🛠️ Instalación

1. En Blender, ve a **Edit > Preferences > Add-ons**.
2. Selecciona **Install from Disk...** y elige [`metadyn_animator.py`](file:///home/ciqus/GIT/Github_Personal/Blender/_metadyn_animator_/metadyn_animator.py).
3. Marca la casilla para activar **Metadynamics Animator**.

---

## 📖 Uso

1. Abre el N-Panel en la Vista 3D (`N`).
2. Ve a la pestaña **Metadyn**.
3. Ajusta los parámetros del paisaje de energía y presiona **Generar Simulación / Animar**.

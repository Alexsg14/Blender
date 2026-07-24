"""
PDB Molecule of the Month -> Blender + Molecular Nodes (Blender 4.2+)
Estrategia: Importar PDB -> Convertir a MESH -> Material solido limpio -> Exportar GLB
"""

import bpy
import mathutils
import urllib.request
import re
import importlib
import os
import tempfile
import random
import colorsys

# ─── CONFIGURACION ────────────────────────────────────────────────────────────

ROUGHNESS       = 1.0    # Rugosidad del material
TRANSMISSION    = 0.0    # Transmision (0.0 = opaco)
FALLBACK_PDB_ID = "7A4W" # PDB de reserva
GLB_EXPORT      = False  # Cambiar a True para exportar automaticamente a GLB
GLB_OUTPUT_DIR  = tempfile.gettempdir()

# ─── COLOR ALEATORIO (H aleatorio, S=1, V=1) ─────────────────────────────────

def get_random_linear_color():
    h = random.random()
    r, g, b = colorsys.hsv_to_rgb(h, 1.0, 1.0)
    def lin(c): return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    lr, lg, lb = lin(r), lin(g), lin(b)
    hex_col = "#{:02X}{:02X}{:02X}".format(int(r*255), int(g*255), int(b*255))
    print(f"[COLOR] Hue={h:.3f} -> sRGB={hex_col} -> Linear=({lr:.3f}, {lg:.3f}, {lb:.3f})")
    return (lr, lg, lb, 1.0)

# ─── IMPORT MN ────────────────────────────────────────────────────────────────

def import_mn():
    for name in ("bl_ext.blender_org.molecularnodes", "molecularnodes"):
        try:
            mn = importlib.import_module(name)
            print(f"[MN] Modulo: '{name}'")
            return mn
        except ImportError:
            pass
    print("[ERROR] Molecular Nodes no encontrado.")
    return None

# ─── MOTM SCRAPER ─────────────────────────────────────────────────────────────

def get_motm_pdbs():
    try:
        req = urllib.request.Request(
            "https://pdb101.rcsb.org/motm/",
            headers={"User-Agent": "Mozilla/5.0"}
        )
        with urllib.request.urlopen(req, timeout=15) as r:
            html = r.read().decode("utf-8", errors="replace")
        ids = re.findall(r'/structure/([A-Za-z0-9]{4})\b', html)
        seen, unique = set(), []
        for i in ids:
            i = i.upper()
            if i not in seen:
                seen.add(i)
                unique.append(i)
        if unique:
            print(f"[MOTM] PDB principal: {unique[0]}  (candidatos: {unique[:6]})")
            return unique
    except Exception as e:
        print(f"[MOTM] Error scraping: {e}")
    return [FALLBACK_PDB_ID]

# ─── HELPERS DE ESCENA ────────────────────────────────────────────────────────

def scene_names():
    return set(o.name for o in bpy.data.objects)

def newest_objects(before):
    new_names = set(o.name for o in bpy.data.objects) - before
    return [bpy.data.objects[n] for n in new_names]

def op_properties(op_func):
    try:
        rna = op_func.get_rna_type()
        return [p.identifier for p in rna.properties if p.identifier != 'rna_type']
    except Exception:
        return []

# ─── CARGA DE MOLECULA ────────────────────────────────────────────────────────

def try_import_fetch(pdb_id):
    if not hasattr(bpy.ops, "mn") or not hasattr(bpy.ops.mn, "import_fetch"):
        return None
    props = op_properties(bpy.ops.mn.import_fetch)
    code_param = None
    for c in ('code', 'pdb_code', 'pdb_id', 'accession', 'entry_id'):
        if c in props:
            code_param = c
            break
    if code_param is None:
        return None
    print(f"[MN] import_fetch({code_param}='{pdb_id}') ...")
    before = scene_names()
    try:
        kwargs = {code_param: pdb_id, 'style': 'cartoon'}
        if 'style' not in props:
            kwargs = {code_param: pdb_id}
        bpy.ops.mn.import_fetch(**kwargs)
        new = newest_objects(before)
        return new[0] if new else None
    except Exception as e:
        print(f"[MN]   Fallo import_fetch: {e}")
    return None

def try_entities_fetch(mn, pdb_id):
    try:
        entities = importlib.import_module(mn.__name__ + ".entities")
    except ImportError:
        return None
    print(f"[MN] entities.fetch('{pdb_id}') ...")
    before = scene_names()
    try:
        entities.fetch(pdb_id, style='cartoon')
        new = newest_objects(before)
        if new:
            return new[0]
    except Exception as e:
        print(f"[MN]   entities.fetch fallo: {e}")
    # Workaround CIF manual
    tmp = os.path.join(tempfile.gettempdir(), f"{pdb_id}.cif")
    try:
        urllib.request.urlretrieve(f"https://files.rcsb.org/download/{pdb_id}.cif", tmp)
        entities.load_local(tmp, style='cartoon')
        new = newest_objects(before)
        return new[0] if new else None
    except Exception as e:
        print(f"[MN]   Workaround CIF fallo: {e}")
    return None

def load_molecule(mn, pdb_ids):
    for pdb_id in pdb_ids:
        print(f"\n--- Intentando PDB: {pdb_id} ---")
        obj = try_import_fetch(pdb_id)
        if not obj:
            obj = try_entities_fetch(mn, pdb_id)
        if obj:
            print(f"[MN] Cargado: '{obj.name}'")
            return obj
    return None

# ─── CONVERTIR A MESH ─────────────────────────────────────────────────────────

def convert_to_mesh(obj):
    """
    Aplica todos los modificadores (incluido Geometry Nodes de MN)
    y convierte el objeto a un MESH real, libre de dependencias de MN.
    """
    print(f"[MESH] Convirtiendo '{obj.name}' a mesh...")

    # Deseleccionar todo y seleccionar solo el objetivo
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj

    # Convertir: aplica todos los modifiers -> convierte a MESH
    try:
        if hasattr(bpy.context, "temp_override"):
            with bpy.context.temp_override(active_object=obj, selected_editable_objects=[obj]):
                bpy.ops.object.convert(target='MESH')
        else:
            bpy.ops.object.convert(target='MESH')
        print(f"[MESH] Conversion exitosa: '{obj.name}'")
        return obj
    except Exception as e:
        print(f"[MESH] Error en convert: {e}")
        return None

# ─── MATERIAL SOLIDO LIMPIO ───────────────────────────────────────────────────

def apply_solid_material(obj, color_linear):
    """
    Elimina todos los materiales existentes (los de MN) y aplica
    un material nuevo limpio con Principled BSDF de color solido.
    Esto es necesario para que el GLB exporte correctamente.
    """
    # Crear material nuevo
    mat_name = f"SolidColor_{obj.name[:20]}"
    mat = bpy.data.materials.new(name=mat_name)
    mat.use_nodes = True

    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    # Principled BSDF
    bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.location = (0, 0)
    bsdf.inputs["Base Color"].default_value = color_linear
    bsdf.inputs["Roughness"].default_value  = ROUGHNESS
    for t in ("Transmission", "Transmission Weight"):
        if t in bsdf.inputs:
            bsdf.inputs[t].default_value = TRANSMISSION
            break

    # Material Output
    out = nodes.new("ShaderNodeOutputMaterial")
    out.location = (300, 0)
    links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])

    # Limpiar materiales anteriores y asignar el nuevo
    obj.data.materials.clear()
    obj.data.materials.append(mat)

    # Asegurar que todas las caras de la malla utilicen el slot 0 (el nuevo material)
    if hasattr(obj.data, "polygons"):
        for poly in obj.data.polygons:
            poly.material_index = 0

    print(f"[MAT] Material limpio '{mat_name}' aplicado con exito.")
    return mat

# ─── CENTRAR OBJETO ───────────────────────────────────────────────────────────

def center_object(obj):
    try:
        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        # Aplicar transformaciones y centrar el origin al centro de masa
        if hasattr(bpy.context, "temp_override"):
            with bpy.context.temp_override(active_object=obj, selected_editable_objects=[obj]):
                bpy.ops.object.origin_set(type='ORIGIN_CENTER_OF_MASS', center='BOUNDS')
        else:
            bpy.ops.object.origin_set(type='ORIGIN_CENTER_OF_MASS', center='BOUNDS')

        obj.location = (0, 0, 0)
        print(f"[SCENE] '{obj.name}' centrado en el origen.")
    except Exception as e:
        print(f"[SCENE] Error centrando: {e}")

# ─── EXPORTAR GLB ─────────────────────────────────────────────────────────────

def export_glb(obj, pdb_id):
    if not GLB_EXPORT:
        return
    path = os.path.join(GLB_OUTPUT_DIR, f"{pdb_id}.glb")
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    try:
        # Compatibilidad con Blender 4.2+ (wm.gltf_export) y versiones anteriores (export_scene.gltf)
        if hasattr(bpy.ops.wm, "gltf_export"):
            bpy.ops.wm.gltf_export(
                filepath=path,
                use_selection=True,
                export_format='GLB',
                export_materials='EXPORT',
            )
        else:
            bpy.ops.export_scene.gltf(
                filepath=path,
                use_selection=True,
                export_format='GLB',
                export_materials='EXPORT',
            )
        print(f"[GLB] Exportado: {path}")
    except Exception as e:
        print(f"[GLB] Error exportando: {e}")

# ─── MAIN ─────────────────────────────────────────────────────────────────────

def main():
    print("\n" + "="*60)
    print("  MOTM -> MESH -> MATERIAL SOLIDO -> (GLB)")
    print("="*60 + "\n")

    mn = import_mn()
    if not mn:
        return

    # 1. Color aleatorio (H aleatorio, S=1, V=1)
    color_linear = get_random_linear_color()

    # 2. Obtener PDB IDs del Molecule of the Month
    pdb_ids = get_motm_pdbs()

    # 3. Importar con Molecular Nodes
    obj = load_molecule(mn, pdb_ids)
    if not obj:
        print("[ERROR] No se pudo cargar ninguna molecula.")
        return

    pdb_id = pdb_ids[0]

    # 4. Convertir a MESH real (aplica GN de MN, objeto libre de dependencias)
    obj = convert_to_mesh(obj)
    if not obj:
        print("[ERROR] Fallo la conversion a mesh.")
        return

    # 5. Aplicar material limpio con color solido
    apply_solid_material(obj, color_linear)

    # 6. Centrar en el origen
    center_object(obj)

    # 7. (Opcional) Exportar a GLB
    export_glb(obj, pdb_id)

    print(f"\n[OK] '{obj.name}' listo como MESH solido.")
    print(f"     Roughness={ROUGHNESS}  Transmission={TRANSMISSION}")
    if GLB_EXPORT:
        print(f"     GLB: {os.path.join(GLB_OUTPUT_DIR, pdb_id + '.glb')}")
    print("="*60 + "\n")

if __name__ == "__main__":
    main()

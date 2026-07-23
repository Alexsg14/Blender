bl_info = {
    "name": "Molecule Builder",
    "author": "Antigravity",
    "version": (1, 0, 3),
    "blender": (3, 6, 0),
    "location": "Vista 3D > Barra lateral > Molécula",
    "description": "Construye y anima estructuras moleculares (átomos y enlaces)",
    "category": "3D View",
}

import bpy
import math
from mathutils import Vector

# ──────────────────────────────────────────────
#  DATOS DE ELEMENTOS
# ──────────────────────────────────────────────

ELEMENT_DATA = {
    'H':      {'radius': 0.31, 'color': (0.85, 0.85, 0.85)},
    'C':      {'radius': 0.77, 'color': (0.15, 0.15, 0.15)},
    'N':      {'radius': 0.75, 'color': (0.10, 0.30, 0.90)},
    'O':      {'radius': 0.73, 'color': (0.90, 0.10, 0.10)},
    'P':      {'radius': 1.06, 'color': (1.00, 0.50, 0.00)},
    'S':      {'radius': 1.02, 'color': (0.90, 0.80, 0.10)},
    'F':      {'radius': 0.64, 'color': (0.20, 0.90, 0.20)},
    'Cl':     {'radius': 0.99, 'color': (0.10, 0.80, 0.10)},
    'Br':     {'radius': 1.14, 'color': (0.60, 0.10, 0.10)},
    'CUSTOM': {'radius': 0.50, 'color': (0.60, 0.60, 0.90)},
}

ELEMENT_ITEMS = [
    ('H',      'H  – Hidrógeno',  ''),
    ('C',      'C  – Carbono',    ''),
    ('N',      'N  – Nitrógeno',  ''),
    ('O',      'O  – Oxígeno',    ''),
    ('P',      'P  – Fósforo',    ''),
    ('S',      'S  – Azufre',     ''),
    ('F',      'F  – Flúor',      ''),
    ('Cl',     'Cl – Cloro',      ''),
    ('Br',     'Br – Bromo',      ''),
    ('CUSTOM', 'Personalizado',   ''),
]


# ──────────────────────────────────────────────
#  UTILIDADES
# ──────────────────────────────────────────────

def get_or_create_material(name, color, metallic=0.2, roughness=0.35):
    if name in bpy.data.materials:
        return bpy.data.materials[name]
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get('Principled BSDF')
    if bsdf:
        bsdf.inputs['Base Color'].default_value = (*color, 1.0)
        bsdf.inputs['Metallic'].default_value = metallic
        bsdf.inputs['Roughness'].default_value = roughness
    return mat


def apply_material(obj, mat):
    if obj.data.materials:
        obj.data.materials[0] = mat
    else:
        obj.data.materials.append(mat)


def orient_object_to_vector(obj, loc_a, loc_b):
    """Coloca obj entre loc_a y loc_b orientado en esa dirección (eje Z local)."""
    direction = loc_b - loc_a
    length = direction.length
    if length < 1e-6:
        return 0.0
    obj.location = (loc_a + loc_b) / 2.0
    q = Vector((0, 0, 1)).rotation_difference(direction.normalized())
    obj.rotation_euler = q.to_euler()
    return length


def get_atom_world_loc(obj):
    return obj.matrix_world.to_translation()


def atom_counter(context):
    """Cuenta cuántos átomos hay en la escena para nombrar el siguiente."""
    return sum(1 for o in context.scene.objects if o.get('mol_type') == 'atom')


def bond_exists(scene, name_a, name_b):
    for obj in scene.objects:
        if obj.get('mol_type') != 'bond':
            continue
        a = obj.get('mol_atom_a', '')
        b = obj.get('mol_atom_b', '')
        if (a == name_a and b == name_b) or (a == name_b and b == name_a):
            return True
    return False


def create_dynamic_bond(scene, name, atom_a, atom_b, radius, color):
    """
    Crea un cilindro dinámico que sigue a atom_a y atom_b mediante constraints:
      • COPY_LOCATION → atom_a  (el origen del cilindro se ancla en atom_a)
      • STRETCH_TO    → atom_b  (el cilindro se orienta y estira hasta atom_b)
    El mesh tiene longitud unitaria con el origen en el extremo Y=0 (atom_a).
    """
    import bmesh
    from mathutils import Matrix

    # ── Crear mesh: cilindro unitario con eje Y, origen en extremo Y=0 ──
    mesh = bpy.data.meshes.new(name)
    bm = bmesh.new()
    bmesh.ops.create_cone(
        bm,
        cap_ends=True,
        cap_tris=False,
        segments=16,
        radius1=radius,
        radius2=radius,
        depth=1.0,           # Profundidad unitaria (escala a través de STRETCH_TO)
    )
    # Girar 90° en X: eje Z → eje Y
    rot = Matrix.Rotation(math.pi / 2, 4, 'X')
    for v in bm.verts:
        v.co = rot @ v.co
    # Trasladar +0.5 en Y: origin queda en Y=0, punta en Y=1
    for v in bm.verts:
        v.co.y += 0.5
    bm.to_mesh(mesh)
    bm.free()

    # Smooth shading
    for poly in mesh.polygons:
        poly.use_smooth = True
    mesh.update()

    # ── Crear objeto ──
    bond_obj = bpy.data.objects.new(name, mesh)
    scene.collection.objects.link(bond_obj)
    bond_obj.location = atom_a.matrix_world.to_translation().copy()

    # ── Material ──
    mat = get_or_create_material(f"Mat_Bond", color, metallic=0.3, roughness=0.4)
    apply_material(bond_obj, mat)

    # ── Constraint 1: anclar origen en atom_a ──
    cloc = bond_obj.constraints.new('COPY_LOCATION')
    cloc.target = atom_a

    # ── Constraint 2: estirar y rotar hasta atom_b ──
    st = bond_obj.constraints.new('STRETCH_TO')
    st.target     = atom_b
    st.rest_length = 1.0    # la malla tiene longitud 1 antes de escalar
    st.bulge       = 0.0    # sin preservar volumen: radio constante

    # ── Propiedades personalizadas ──
    bond_obj['mol_type']     = 'bond'
    bond_obj['mol_atom_a']   = atom_a.name
    bond_obj['mol_atom_b']   = atom_b.name
    bond_obj['mol_dynamic']  = True   # marca: usa constraints, no recalcular manualmente
    bond_obj['mol_radius']   = radius

    return bond_obj


# ──────────────────────────────────────────────
#  PROPIEDADES
# ──────────────────────────────────────────────

class MOL_Properties(bpy.types.PropertyGroup):
    element: bpy.props.EnumProperty(
        name="Elemento",
        items=ELEMENT_ITEMS,
        default='C',
    )
    custom_radius: bpy.props.FloatProperty(
        name="Radio",
        default=0.5, min=0.01, max=5.0, step=1,
    )
    custom_color: bpy.props.FloatVectorProperty(
        name="Color",
        subtype='COLOR',
        default=(0.6, 0.6, 0.9),
        min=0.0, max=1.0,
    )
    bond_radius: bpy.props.FloatProperty(
        name="Radio enlace",
        default=0.15, min=0.01, max=1.0, step=1,
    )
    bond_color: bpy.props.FloatVectorProperty(
        name="Color enlace",
        subtype='COLOR',
        default=(0.55, 0.55, 0.55),
        min=0.0, max=1.0,
    )
    auto_distance: bpy.props.FloatProperty(
        name="Distancia máx.",
        default=3.5, min=0.1, max=20.0, step=10,
    )
    group_name: bpy.props.StringProperty(
        name="Nombre grupo",
        default="Molecula",
    )
    torsion_angle: bpy.props.FloatProperty(
        name="Ángulo (°)",
        default=60.0, min=-360.0, max=360.0,
    )
    rotation_axis: bpy.props.PointerProperty(
        type=bpy.types.Object,
        name="Eje activo",
        description="Empty que define el eje de rotación (se asigna automáticamente al crearlo)",
    )


# ──────────────────────────────────────────────
#  OPERADOR: Añadir átomo
# ──────────────────────────────────────────────

class MOL_OT_AddAtom(bpy.types.Operator):
    bl_idname = "mol.add_atom"
    bl_label = "Añadir Átomo"
    bl_description = "Añade un átomo (esfera) en la posición del cursor 3D"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        props = context.scene.mol_props
        elem = props.element
        data = ELEMENT_DATA[elem]

        if elem == 'CUSTOM':
            radius = props.custom_radius
            color  = tuple(props.custom_color)
        else:
            radius = data['radius']
            color  = data['color']

        loc = context.scene.cursor.location.copy()
        n = atom_counter(context) + 1
        name = f"Atom_{elem}_{n}"

        bpy.ops.mesh.primitive_uv_sphere_add(
            radius=radius, location=loc,
            segments=32, ring_count=16
        )
        obj = context.active_object
        obj.name = name

        bpy.ops.object.shade_smooth()

        mat = get_or_create_material(f"Mat_{elem}", color, metallic=0.15, roughness=0.30)
        apply_material(obj, mat)

        obj['mol_type']    = 'atom'
        obj['mol_element'] = elem

        self.report({'INFO'}, f"Átomo {name} creado en {tuple(round(v,3) for v in loc)}")
        return {'FINISHED'}


# ──────────────────────────────────────────────
#  OPERADOR: Conectar dos átomos seleccionados
# ──────────────────────────────────────────────

class MOL_OT_ConnectAtoms(bpy.types.Operator):
    bl_idname = "mol.connect_atoms"
    bl_label = "Conectar Seleccionados"
    bl_description = "Crea un enlace dinámico entre 2 átomos (sigue a los átomos al moverlos)"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        props = context.scene.mol_props
        sel = [o for o in context.selected_objects if o.get('mol_type') == 'atom']

        if len(sel) != 2:
            self.report({'ERROR'}, "Selecciona exactamente 2 átomos")
            return {'CANCELLED'}

        atom_a, atom_b = sel
        if bond_exists(context.scene, atom_a.name, atom_b.name):
            self.report({'WARNING'}, "Ya existe un enlace entre esos átomos")
            return {'CANCELLED'}

        bond_name  = f"Bond_{atom_a.name}_{atom_b.name}"
        bond_color = tuple(props.bond_color)

        create_dynamic_bond(
            context.scene, bond_name,
            atom_a, atom_b,
            props.bond_radius, bond_color,
        )

        self.report({'INFO'}, f"Enlace dinámico creado: {atom_a.name} ↔ {atom_b.name}")
        return {'FINISHED'}


# ──────────────────────────────────────────────
#  OPERADOR: Auto-conectar por distancia
# ──────────────────────────────────────────────

class MOL_OT_AutoConnect(bpy.types.Operator):
    bl_idname = "mol.auto_connect"
    bl_label = "Auto-conectar"
    bl_description = "Conecta todos los átomos seleccionados que estén dentro de la distancia máxima"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        props = context.scene.mol_props
        atoms = [o for o in context.selected_objects if o.get('mol_type') == 'atom']

        if len(atoms) < 2:
            self.report({'ERROR'}, "Selecciona al menos 2 átomos")
            return {'CANCELLED'}

        max_d      = props.auto_distance
        bond_radius = props.bond_radius
        bond_color  = tuple(props.bond_color)
        created = 0

        for i in range(len(atoms)):
            for j in range(i + 1, len(atoms)):
                a, b = atoms[i], atoms[j]
                loc_a = get_atom_world_loc(a)
                loc_b = get_atom_world_loc(b)
                dist = (loc_b - loc_a).length

                if dist > max_d:
                    continue
                if bond_exists(context.scene, a.name, b.name):
                    continue

                bond_name = f"Bond_{a.name}_{b.name}"
                create_dynamic_bond(
                    context.scene, bond_name,
                    a, b,
                    bond_radius, bond_color,
                )
                created += 1

        self.report({'INFO'}, f"{created} enlace(s) dinámico(s) creado(s)")
        return {'FINISHED'}


# ──────────────────────────────────────────────
#  OPERADOR: Actualizar posición de todos los enlaces
# ──────────────────────────────────────────────

class MOL_OT_UpdateBonds(bpy.types.Operator):
    bl_idname = "mol.update_bonds"
    bl_label = "Actualizar Enlaces"
    bl_description = "Recalcula posición y orientación de todos los enlaces según la posición actual de los átomos"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        updated = 0
        for obj in context.scene.objects:
            if obj.get('mol_type') != 'bond':
                continue
            name_a = obj.get('mol_atom_a', '')
            name_b = obj.get('mol_atom_b', '')
            atom_a = context.scene.objects.get(name_a)
            atom_b = context.scene.objects.get(name_b)
            if not atom_a or not atom_b:
                continue

            loc_a = get_atom_world_loc(atom_a)
            loc_b = get_atom_world_loc(atom_b)
            direction = loc_b - loc_a
            length = direction.length
            if length < 1e-6:
                continue

            obj.location = (loc_a + loc_b) / 2.0
            q = Vector((0, 0, 1)).rotation_difference(direction.normalized())
            obj.rotation_euler = q.to_euler()

            # Ajustar longitud: escalar Z solo si el cilindro tiene depth=1 base
            # Los cilindros se crearon con depth=length, así que basta con actualizar scale Z
            # Para actualizar la longitud real, mejor escalar:
            old_len = obj.get('mol_length', length)
            if old_len > 1e-6:
                ratio = length / old_len
                obj.scale[2] = obj.scale[2] * ratio
                obj['mol_length'] = length

            updated += 1

        self.report({'INFO'}, f"{updated} enlace(s) actualizados")
        return {'FINISHED'}


# ──────────────────────────────────────────────
#  OPERADOR: Agrupar como molécula (Empty padre)
# ──────────────────────────────────────────────

class MOL_OT_GroupMolecule(bpy.types.Operator):
    bl_idname = "mol.group_molecule"
    bl_label = "Agrupar como Molécula"
    bl_description = "Crea un Empty padre para los objetos seleccionados (átomo + enlaces)"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        props = context.scene.mol_props
        sel = list(context.selected_objects)
        if not sel:
            self.report({'ERROR'}, "Nada seleccionado")
            return {'CANCELLED'}

        # Calcular centro del grupo
        center = Vector()
        for o in sel:
            center += o.matrix_world.to_translation()
        center /= len(sel)

        # Crear Empty en el centro
        bpy.ops.object.empty_add(type='PLAIN_AXES', location=center)
        empty = context.active_object
        empty.name = props.group_name
        empty['mol_type'] = 'group'

        # Parentar los objetos seleccionados al Empty
        for o in sel:
            o.select_set(True)
        context.view_layer.objects.active = empty
        bpy.ops.object.parent_set(type='OBJECT', keep_transform=True)

        self.report({'INFO'}, f"Grupo '{empty.name}' creado con {len(sel)} objetos")
        return {'FINISHED'}


# ──────────────────────────────────────────────
#  OPERADOR: Seleccionar molécula conectada
# ──────────────────────────────────────────────

class MOL_OT_SelectMolecule(bpy.types.Operator):
    bl_idname = "mol.select_molecule"
    bl_label = "Seleccionar Molécula"
    bl_description = "Selecciona todos los átomos y enlaces conectados al átomo activo (BFS)"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        active = context.active_object
        if not active or active.get('mol_type') not in ('atom', 'bond'):
            self.report({'ERROR'}, "Activa un átomo o enlace primero")
            return {'CANCELLED'}

        # Construir grafo: átomo_nombre → lista de átomos vecinos y enlaces
        bonds = [o for o in context.scene.objects if o.get('mol_type') == 'bond']
        graph = {}  # átomo → set de átomos vecinos

        for bond in bonds:
            a = bond.get('mol_atom_a', '')
            b = bond.get('mol_atom_b', '')
            graph.setdefault(a, set()).add(b)
            graph.setdefault(b, set()).add(a)

        # BFS desde átomo de inicio
        start_name = active.name if active.get('mol_type') == 'atom' else active.get('mol_atom_a', '')
        visited = set()
        queue = [start_name]
        while queue:
            curr = queue.pop(0)
            if curr in visited:
                continue
            visited.add(curr)
            for neighbor in graph.get(curr, []):
                if neighbor not in visited:
                    queue.append(neighbor)

        # Deseleccionar todo y seleccionar los encontrados + sus enlaces
        bpy.ops.object.select_all(action='DESELECT')
        for name in visited:
            o = context.scene.objects.get(name)
            if o:
                o.select_set(True)

        for bond in bonds:
            a = bond.get('mol_atom_a', '')
            b = bond.get('mol_atom_b', '')
            if a in visited and b in visited:
                bond.select_set(True)

        self.report({'INFO'}, f"{len(visited)} átomo(s) seleccionado(s)")
        return {'FINISHED'}


# ──────────────────────────────────────────────
#  HELPER: Rotación arbitraria en espacio mundo
# ──────────────────────────────────────────────

def rotate_objects_around_axis(objects, pivot, axis_vec, angle_rad):
    """
    Rota una lista de ÁTOMOS alrededor de un eje arbitrario.
    Solo mueve posición; la orientación de los enlaces se recalcula aparte.
    pivot    : Vector world-space (punto en el eje)
    axis_vec : Vector world-space (dirección del eje, se normaliza)
    angle_rad: ángulo en radianes
    """
    from mathutils import Matrix
    rot4 = Matrix.Rotation(angle_rad, 4, axis_vec.normalized())

    for obj in objects:
        world_loc = obj.matrix_world.to_translation()
        new_world_loc = rot4 @ (world_loc - pivot) + pivot
        if obj.parent:
            obj.location = obj.parent.matrix_world.inverted() @ new_world_loc
        else:
            obj.location = new_world_loc


def recalculate_affected_bonds(scene, atom_names_set):
    """
    Recalcula posición y orientación de enlaces ESTÁTICOS conectados a los átomos dados.
    Los enlaces dinámicos (mol_dynamic=True) se saltan porque sus constraints
    (COPY_LOCATION + STRETCH_TO) los actualizan automáticamente.
    """
    for obj in scene.objects:
        if obj.get('mol_type') != 'bond':
            continue
        if obj.get('mol_dynamic'):      # ← enlace con constraints: skip
            continue
        name_a = obj.get('mol_atom_a', '')
        name_b = obj.get('mol_atom_b', '')
        if name_a not in atom_names_set and name_b not in atom_names_set:
            continue
        atom_a = scene.objects.get(name_a)
        atom_b = scene.objects.get(name_b)
        if not atom_a or not atom_b:
            continue
        loc_a = atom_a.matrix_world.to_translation()
        loc_b = atom_b.matrix_world.to_translation()
        direction = loc_b - loc_a
        length = direction.length
        if length < 1e-6:
            continue
        obj.location = (loc_a + loc_b) / 2.0
        q = Vector((0, 0, 1)).rotation_difference(direction.normalized())
        obj.rotation_euler = q.to_euler()
        obj['mol_length'] = length


# ──────────────────────────────────────────────
#  OPERADOR: Crear eje de rotación desde enlace
# ──────────────────────────────────────────────

class MOL_OT_CreateRotationAxis(bpy.types.Operator):
    bl_idname = "mol.create_rotation_axis"
    bl_label = "1. Crear Eje de Rotación"
    bl_description = (
        "Selecciona 2 átomos que definen el eje del enlace: "
        "crea un Empty (flechas) cuyo eje Z LOCAL apunta a lo largo de ese enlace"
    )
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        sel = [o for o in context.selected_objects if o.get('mol_type') == 'atom']
        if len(sel) != 2:
            self.report({'ERROR'}, "Selecciona exactamente 2 átomos que definan el eje")
            return {'CANCELLED'}

        atom_a, atom_b = sel
        loc_a = get_atom_world_loc(atom_a)
        loc_b = get_atom_world_loc(atom_b)
        direction = loc_b - loc_a
        length = direction.length

        if length < 1e-6:
            self.report({'ERROR'}, "Los dos átomos están en la misma posición")
            return {'CANCELLED'}

        # Empty en el punto medio del enlace
        midpoint = (loc_a + loc_b) / 2.0
        bpy.ops.object.empty_add(type='ARROWS', location=midpoint)
        axis_empty = context.active_object
        axis_empty.name = f"RotAxis_{atom_a.name}_{atom_b.name}"

        # Eje Z local → dirección del enlace
        q = Vector((0, 0, 1)).rotation_difference(direction.normalized())
        axis_empty.rotation_euler = q.to_euler()
        axis_empty.empty_display_size = max(length * 0.6, 0.5)

        axis_empty['mol_type']   = 'rotation_axis'
        axis_empty['mol_axis_a'] = atom_a.name
        axis_empty['mol_axis_b'] = atom_b.name

        # Guardar referencia en la propiedad de escena
        context.scene.mol_props.rotation_axis = axis_empty

        self.report({'INFO'},
            f"Eje '{axis_empty.name}' guardado. "
            "Selecciona los átomos a rotar y pulsa 'Rotar' o 'Animar'.")
        return {'FINISHED'}


# ──────────────────────────────────────────────
#  OPERADOR: Rotar átomos alrededor del eje (sin keyframe)
# ──────────────────────────────────────────────

class MOL_OT_ApplyRotation(bpy.types.Operator):
    bl_idname = "mol.apply_rotation"
    bl_label = "2. Rotar por Eje"
    bl_description = (
        "Selecciona los átomos a rotar y pulsa este botón. "
        "El eje se toma del Empty creado en el paso 1 (guardado automáticamente)."
    )
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        props    = context.scene.mol_props
        axis_obj = props.rotation_axis

        if not axis_obj:
            self.report({'ERROR'}, "Primero crea un Eje de Rotación (paso 1)")
            return {'CANCELLED'}

        # Solo rotar átomos; los enlaces se recalculan a partir de ellos
        atoms = [o for o in context.selected_objects
                 if o != axis_obj and o.get('mol_type') == 'atom']
        if not atoms:
            self.report({'ERROR'}, "Selecciona los átomos a rotar (no hace falta seleccionar los enlaces)")
            return {'CANCELLED'}

        pivot    = axis_obj.matrix_world.to_translation()
        axis_vec = (axis_obj.matrix_world.to_3x3() @ Vector((0, 0, 1))).normalized()
        angle    = math.radians(props.torsion_angle)

        rotate_objects_around_axis(atoms, pivot, axis_vec, angle)

        # Actualizar geometría de todos los enlaces afectados
        atom_names = {o.name for o in atoms}
        recalculate_affected_bonds(context.scene, atom_names)

        self.report({'INFO'},
            f"{props.torsion_angle:.1f}° aplicado a {len(atoms)} átomo(s) "
            f"alrededor de '{axis_obj.name}'")
        return {'FINISHED'}


# ──────────────────────────────────────────────
#  OPERADOR: Animar torsión (con keyframes)
# ──────────────────────────────────────────────

class MOL_OT_AnimateTorsion(bpy.types.Operator):
    bl_idname = "mol.animate_torsion"
    bl_label = "3. Animar Torsión (keyframes)"
    bl_description = (
        "Selecciona los átomos a rotar y pulsa este botón. "
        "Inserta keyframe en el frame actual y otro 24 frames después con la torsión aplicada."
    )
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        props    = context.scene.mol_props
        scene    = context.scene
        frame_0  = scene.frame_current
        axis_obj = props.rotation_axis

        if not axis_obj:
            self.report({'ERROR'}, "Primero crea un Eje de Rotación (paso 1)")
            return {'CANCELLED'}

        atoms = [o for o in context.selected_objects
                 if o != axis_obj and o.get('mol_type') == 'atom']
        if not atoms:
            self.report({'ERROR'}, "Selecciona los átomos a rotar")
            return {'CANCELLED'}

        atom_names = {o.name for o in atoms}
        # Bonds afectados (los que conectan al menos un átomo rotado)
        bonds = [o for o in scene.objects
                 if o.get('mol_type') == 'bond'
                 and (o.get('mol_atom_a','') in atom_names
                      or o.get('mol_atom_b','') in atom_names)]

        pivot    = axis_obj.matrix_world.to_translation()
        axis_vec = (axis_obj.matrix_world.to_3x3() @ Vector((0, 0, 1))).normalized()
        angle    = math.radians(props.torsion_angle)

        # ── Keyframe inicial (posición actual) ──
        for obj in atoms + bonds:
            obj.keyframe_insert(data_path="location",       frame=frame_0)
            obj.keyframe_insert(data_path="rotation_euler", frame=frame_0)

        # ── Rotar átomos y recalcular enlaces ──
        rotate_objects_around_axis(atoms, pivot, axis_vec, angle)
        recalculate_affected_bonds(scene, atom_names)

        # ── Keyframe final ──
        frame_1 = frame_0 + 24
        for obj in atoms + bonds:
            obj.keyframe_insert(data_path="location",       frame=frame_1)
            obj.keyframe_insert(data_path="rotation_euler", frame=frame_1)

        self.report({'INFO'},
            f"Torsión {props.torsion_angle:.1f}° animada: frames {frame_0}→{frame_1}")
        return {'FINISHED'}


# ──────────────────────────────────────────────
#  PANEL PRINCIPAL
# ──────────────────────────────────────────────

class MOL_PT_MainPanel(bpy.types.Panel):
    bl_label       = "Molecule Builder"
    bl_idname      = "MOL_PT_main"
    bl_space_type  = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category    = "Molécula"

    def draw(self, context):
        layout = self.layout
        props  = context.scene.mol_props

        # ── ÁTOMOS ──────────────────────────────
        box = layout.box()
        box.label(text="⬤  Átomos", icon='MESH_UVSPHERE')

        box.prop(props, "element")
        if props.element == 'CUSTOM':
            row = box.row(align=True)
            row.prop(props, "custom_radius")
            row.prop(props, "custom_color", text="")

        box.operator("mol.add_atom", icon='ADD')

        # ── ENLACES ─────────────────────────────
        box = layout.box()
        box.label(text="━  Enlaces", icon='MESH_CYLINDER')

        row = box.row(align=True)
        row.prop(props, "bond_radius")
        row.prop(props, "bond_color", text="")

        box.operator("mol.connect_atoms", icon='LINK_BLEND')

        col = box.column(align=True)
        col.prop(props, "auto_distance")
        col.operator("mol.auto_connect", icon='OUTLINER_OB_FORCE_FIELD')

        box.operator("mol.update_bonds", icon='FILE_REFRESH')

        # ── GRUPOS ──────────────────────────────
        box = layout.box()
        box.label(text="□  Grupos", icon='OBJECT_DATA')

        box.prop(props, "group_name")
        box.operator("mol.group_molecule", icon='OUTLINER_OB_EMPTY')
        box.operator("mol.select_molecule", icon='RESTRICT_SELECT_OFF')

        # ── ROTACIÓN / ANIMACIÓN ─────────────────
        box = layout.box()
        box.label(text="↻  Rotación y Animación", icon='DRIVER_ROTATIONAL_DIFFERENCE')

        col = box.column(align=True)
        col.scale_y = 0.72
        col.label(text="Flujo:", icon='INFO')
        col.label(text="  1· Sel. 2 átomos del enlace-eje")
        col.label(text="  2· Pulsa 'Crear Eje' (se guarda solo)")
        col.label(text="  3· Sel. átomos a rotar → Rotar")

        box.separator()
        box.operator("mol.create_rotation_axis", icon='EMPTY_ARROWS')

        # Mostrar qué eje está guardado actualmente
        row = box.row(align=True)
        row.prop(props, "rotation_axis", text="Eje", icon='EMPTY_ARROWS')

        box.separator()
        box.prop(props, "torsion_angle")
        col2 = box.column(align=True)
        col2.operator("mol.apply_rotation",  icon='DRIVER_ROTATIONAL_DIFFERENCE')
        col2.operator("mol.animate_torsion", icon='ANIM')


# ──────────────────────────────────────────────
#  REGISTRO
# ──────────────────────────────────────────────

classes = [
    MOL_Properties,
    MOL_OT_AddAtom,
    MOL_OT_ConnectAtoms,
    MOL_OT_AutoConnect,
    MOL_OT_UpdateBonds,
    MOL_OT_GroupMolecule,
    MOL_OT_SelectMolecule,
    MOL_OT_CreateRotationAxis,
    MOL_OT_ApplyRotation,
    MOL_OT_AnimateTorsion,
    MOL_PT_MainPanel,
]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.mol_props = bpy.props.PointerProperty(type=MOL_Properties)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.mol_props


if __name__ == "__main__":
    register()

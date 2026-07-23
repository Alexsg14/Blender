"""
Metadynamics Animator – Blender Addon (Aesthetic Edition)
Coordinate system: X = CV, Z = Energy, Y = tiny layer offsets
Camera looks in +Y → renders X (horizontal) vs Z (vertical = energy).
"""

bl_info = {
    "name": "Metadynamics Animator",
    "author": "Antigravity",
    "version": (2, 0, 0),
    "blender": (4, 0, 0),
    "location": "View3D > Sidebar > Metadyn",
    "description": "Simula y anima metadinámica 2D con estética para presentaciones",
    "category": "Animation",
}

import bpy, bmesh, math, json, random
from bpy.props import FloatProperty, IntProperty, BoolProperty, CollectionProperty
from bpy.types import Operator, Panel, PropertyGroup, UIList

# ─────────────────────────────────────────────
# CONSTANTES
# ─────────────────────────────────────────────
X_MIN, X_MAX = -4.5, 4.5
N   = 91
XG  = [X_MIN + i*(X_MAX-X_MIN)/(N-1) for i in range(N)]
ZFL = -15.0   # energy floor

# Layer offsets (Y axis, depth)
L_GRID  = -0.10
L_PES   =  0.00
L_ZERO  =  0.01
L_PESED =  0.02
L_BIAS  =  0.04
L_BIAED =  0.06
L_WALK  =  0.10

NAMES = ["MD_Grid","MD_PES","MD_PESEdge","MD_Bias","MD_BiasEdge",
         "MD_Zero","MD_Walker","MD_WalkLight","MD_Camera"]

# ─────────────────────────────────────────────
# FÍSICA
# ─────────────────────────────────────────────
def pes(x, wells):
    e = 0.2*x**4
    for w in wells:
        e -= w['d']*math.exp(-(x-w['p'])**2/w['w'])
    return e

def bias(x, gs):
    b = 0.0
    for g in gs:
        b += g['h']*math.exp(-(x-g['m'])**2/(2*g['s']**2))
    return b

def force(x, gs, wells):
    dx=0.001
    dp=(pes(x+dx,wells)-pes(x-dx,wells))/(2*dx)
    db=sum(g['h']*math.exp(-(x-g['m'])**2/(2*g['s']**2))*(-(x-g['m'])/g['s']**2) for g in gs)
    return -(dp+db)

def simulate(cfg):
    wells=cfg['wells']; rng=random.Random(cfg['seed'])
    wx=wells[0]['p'] if wells else 0.0
    gs=[]; frames=[]
    dt=0.05; T=cfg['T']; W=cfg['W']; sig=cfg['sig']
    stride=cfg['stride']; wt=cfg['wt']; gam=cfg['gam']
    for step in range(cfg['steps']):
        frames.append({'wx':wx,'ng':len(gs)})
        f=max(-15.,min(15.,force(wx,gs,wells)))
        n=math.sqrt(2*T*dt)*(rng.random()-0.5)*2
        wx=max(X_MIN,min(X_MAX,wx+f*dt+n))
        if (step+1)%stride==0:
            h=W
            if wt:
                bv=bias(wx,gs); dt2=T*(gam-1)
                if dt2>0: h=W*math.exp(-bv/dt2)
            gs.append({'m':wx,'h':h,'s':sig})
    return frames, gs

# ─────────────────────────────────────────────
# MATERIALES
# ─────────────────────────────────────────────
def _mat(name, color, emit=0.0, alpha=1.0, metallic=0.0, rough=0.5):
    m = bpy.data.materials.get(name)
    if m: bpy.data.materials.remove(m)
    m = bpy.data.materials.new(name)
    m.use_nodes=True; m.blend_method='BLEND'
    nt=m.node_tree; nt.nodes.clear()
    out =nt.nodes.new('ShaderNodeOutputMaterial')
    add =nt.nodes.new('ShaderNodeAddShader')
    bsd =nt.nodes.new('ShaderNodeBsdfPrincipled')
    em  =nt.nodes.new('ShaderNodeEmission')
    r,g,b,a=color[0],color[1],color[2],alpha
    bsd.inputs['Base Color'].default_value=(r,g,b,1)
    bsd.inputs['Alpha'].default_value=alpha
    bsd.inputs['Roughness'].default_value=rough
    bsd.inputs['Metallic'].default_value=metallic
    em.inputs['Color'].default_value=(r,g,b,1)
    em.inputs['Strength'].default_value=emit
    nt.links.new(bsd.outputs['BSDF'],add.inputs[0])
    nt.links.new(em.outputs['Emission'],add.inputs[1])
    nt.links.new(add.outputs['Shader'],out.inputs['Surface'])
    return m

def setup_mats():
    _mat('MD_MatPES',   (0.04,0.10,0.28), emit=0.0,  alpha=1.0, metallic=0.2, rough=0.6)
    _mat('MD_MatPESEd', (0.20,0.75,1.00), emit=4.0,  alpha=1.0)
    _mat('MD_MatBias',  (1.00,0.42,0.05), emit=0.3,  alpha=0.55)
    _mat('MD_MatBiasEd',(1.00,0.65,0.00), emit=6.0,  alpha=1.0)
    _mat('MD_MatWalk',  (0.30,0.85,1.00), emit=8.0,  alpha=1.0)
    _mat('MD_MatZero',  (0.35,0.40,0.50), emit=0.5,  alpha=0.6)
    _mat('MD_MatGrid',  (0.04,0.06,0.10), emit=0.0,  alpha=1.0, rough=1.0)

def assign(obj, mat_name):
    mat=bpy.data.materials.get(mat_name)
    if mat and obj:
        obj.data.materials.clear()
        obj.data.materials.append(mat)

# ─────────────────────────────────────────────
# MALLAS
# ─────────────────────────────────────────────
def _del(name):
    o=bpy.data.objects.get(name)
    if o: bpy.data.meshes.remove(o.data,do_unlink=True)

def _link(obj):
    if obj.name not in bpy.context.collection.objects:
        bpy.context.collection.objects.link(obj)

def make_fill(name, top_z, bot_z, layer):
    """Quad strip: top row z=top_z, bottom row z=bot_z, at y=layer."""
    _del(name)
    mesh=bpy.data.meshes.new(name)
    obj=bpy.data.objects.new(name,mesh)
    _link(obj)
    verts=[(XG[i],layer,top_z[i]) for i in range(N)] + \
          [(XG[i],layer,bot_z[i]) for i in range(N)]
    faces=[(i,i+1,N+i+1,N+i) for i in range(N-1)]
    mesh.from_pydata(verts,[],faces); mesh.update()
    return obj

def make_edge_strip(name, z_vals, layer, half=0.07):
    """Thin glowing strip following z_vals curve."""
    _del(name)
    mesh=bpy.data.meshes.new(name)
    obj=bpy.data.objects.new(name,mesh)
    _link(obj)
    top=[(XG[i],layer,z_vals[i]+half) for i in range(N)]
    bot=[(XG[i],layer,z_vals[i]-half) for i in range(N)]
    verts=top+bot
    faces=[(i,i+1,N+i+1,N+i) for i in range(N-1)]
    mesh.from_pydata(verts,[],faces); mesh.update()
    return obj

def make_zero_line():
    _del('MD_Zero')
    mesh=bpy.data.meshes.new('MD_Zero')
    obj=bpy.data.objects.new('MD_Zero',mesh)
    _link(obj)
    mesh.from_pydata([(X_MIN,L_ZERO,0),(X_MAX,L_ZERO,0)],[(0,1)],[])
    mesh.update(); return obj

def make_grid():
    _del('MD_Grid')
    bpy.ops.mesh.primitive_grid_add(
        x_subdivisions=18, y_subdivisions=40,
        size=1,
        location=(0,L_GRID,-5)
    )
    obj=bpy.context.active_object
    obj.name='MD_Grid'
    obj.scale=(4.8,11,1)
    bpy.ops.object.transform_apply(scale=True)
    return obj

def make_walker(wells):
    _del('MD_Walker')
    o=bpy.data.objects.get('MD_WalkLight')
    if o: bpy.data.objects.remove(o,do_unlink=True)
    px=wells[0]['p'] if wells else 0.0
    pz=pes(px,wells)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.22,location=(px,L_WALK,pz),segments=32,ring_count=16)
    sph=bpy.context.active_object; sph.name='MD_Walker'
    # Point light child
    bpy.ops.object.light_add(type='POINT',location=(px,L_WALK+0.05,pz))
    lt=bpy.context.active_object; lt.name='MD_WalkLight'
    lt.data.color=(0.4,0.9,1.0); lt.data.energy=80; lt.data.shadow_soft_size=0.3
    lt.parent=sph
    return sph

def make_camera():
    o=bpy.data.objects.get('MD_Camera')
    if o: bpy.data.objects.remove(o,do_unlink=True)
    bpy.ops.object.camera_add(location=(0,-28,-4.5))
    cam=bpy.context.active_object; cam.name='MD_Camera'
    cam.rotation_euler=(math.radians(90),0,0)
    cam.data.type='ORTHO'; cam.data.ortho_scale=22
    bpy.context.scene.camera=cam
    return cam

# ─────────────────────────────────────────────
# HANDLER
# ─────────────────────────────────────────────
_handler_on=False

def _handler(scene, depsgraph=None):
    raw=scene.get('metadyn_sim_data')
    if not raw: return
    sim=json.loads(raw)
    frames=sim['f']; gauss=sim['g']; wells=sim['w']
    fi=max(0,min(scene.frame_current-1,len(frames)-1))
    wx=frames[fi]['wx']; ng=frames[fi]['ng']
    cg=gauss[:ng]

    # Bias fill
    bf=bpy.data.objects.get('MD_Bias')
    if bf:
        mv=bf.data.vertices
        for i in range(N):
            pz=pes(XG[i],wells); bz=bias(XG[i],cg)
            mv[i].co=(XG[i],L_BIAS,pz+bz)
            mv[N+i].co=(XG[i],L_BIAS,pz)
        bf.data.update()

    # Bias edge
    be=bpy.data.objects.get('MD_BiasEdge')
    if be:
        mv=be.data.vertices; H=0.07
        for i in range(N):
            pz=pes(XG[i],wells); bz=bias(XG[i],cg); top=pz+bz
            mv[i].co=(XG[i],L_BIAED,top+H)
            mv[N+i].co=(XG[i],L_BIAED,top-H)
        be.data.update()

    # Walker
    wo=bpy.data.objects.get('MD_Walker')
    if wo:
        pz=pes(wx,wells); bz=bias(wx,cg)
        wo.location=(wx,L_WALK,pz+bz)

def reg_handler():
    global _handler_on
    if _handler not in bpy.app.handlers.frame_change_post:
        bpy.app.handlers.frame_change_post.append(_handler)
    _handler_on=True

def unreg_handler():
    global _handler_on
    if _handler in bpy.app.handlers.frame_change_post:
        bpy.app.handlers.frame_change_post.remove(_handler)
    _handler_on=False

# ─────────────────────────────────────────────
# PROPIEDADES
# ─────────────────────────────────────────────
class MDWell(PropertyGroup):
    p: FloatProperty(name="Posición",    default=0.0, min=-4.0,max=4.0,  step=10)
    d: FloatProperty(name="Profundidad", default=8.0, min=0.5, max=15.0, step=50)
    w: FloatProperty(name="Anchura",     default=0.8, min=0.05,max=3.0,  step=5)

class MDProps(PropertyGroup):
    wells:      CollectionProperty(type=MDWell)
    well_idx:   IntProperty(default=0)
    steps:      IntProperty  (name="Pasos",           default=600, min=50,  max=5000)
    T:          FloatProperty(name="Temperatura",      default=0.8, min=0.05,max=5.0,  step=5)
    W:          FloatProperty(name="Altura Gauss (W₀)",default=0.5, min=0.05,max=2.0,  step=5)
    sig:        FloatProperty(name="Anchura Gauss (σ)",default=0.4, min=0.05,max=1.5,  step=5)
    stride:     IntProperty  (name="Stride deposición",default=20,  min=5,   max=500)
    seed:       IntProperty  (name="Semilla",          default=12345)
    wt:         BoolProperty (name="Well-Tempered",    default=False)
    gam:        IntProperty  (name="Bias Factor (γ)",  default=10,  min=2,   max=50)

# ─────────────────────────────────────────────
# OPERADORES
# ─────────────────────────────────────────────
class MD_OT_AddWell(Operator):
    bl_idname="md.add_well"; bl_label="Añadir Pozo"
    def execute(self,ctx):
        p=ctx.scene.md_props; w=p.wells.add()
        w.p=0.0; w.d=8.0; w.w=0.8; return {'FINISHED'}

class MD_OT_RemoveWell(Operator):
    bl_idname="md.remove_well"; bl_label="Eliminar Pozo"
    def execute(self,ctx):
        p=ctx.scene.md_props; i=p.well_idx
        if 0<=i<len(p.wells): p.wells.remove(i); p.well_idx=max(0,i-1)
        return {'FINISHED'}

class MD_OT_Setup(Operator):
    bl_idname="md.setup"; bl_label="1. Crear Escena"
    bl_description="Genera paisaje, malla de bias y walker con materiales de presentación"
    def execute(self,ctx):
        p=ctx.scene.md_props
        if not p.wells: self.report({'WARNING'},"Añade pozos primero."); return {'CANCELLED'}
        wells=[{'p':w.p,'d':w.d,'w':w.w} for w in p.wells]

        setup_mats()

        # World background dark
        world=ctx.scene.world
        if not world: world=bpy.data.worlds.new("World"); ctx.scene.world=world
        world.use_nodes=True
        world.node_tree.nodes["Background"].inputs[0].default_value=(0.01,0.02,0.04,1)
        world.node_tree.nodes["Background"].inputs[1].default_value=1.0

        # EEVEE settings
        rs=ctx.scene.render
        try: rs.engine='BLENDER_EEVEE_NEXT'
        except TypeError: pass

        # Grid
        gobj=make_grid(); assign(gobj,'MD_MatGrid')

        # PES fill (static)
        pz=[pes(x,wells) for x in XG]
        pfl=make_fill('MD_PES',pz,[ZFL]*N,L_PES); assign(pfl,'MD_MatPES')

        # PES edge (static glowing line)
        ped=make_edge_strip('MD_PESEdge',pz,L_PESED,half=0.07); assign(ped,'MD_MatPESEd')

        # Bias fill (dynamic, starts flat)
        bfl=make_fill('MD_Bias',pz,pz,L_BIAS); assign(bfl,'MD_MatBias')

        # Bias edge (dynamic)
        bed=make_edge_strip('MD_BiasEdge',pz,L_BIAED,half=0.07); assign(bed,'MD_MatBiasEd')

        # Zero line
        zl=make_zero_line(); assign(zl,'MD_MatZero')

        # Walker
        wobj=make_walker(wells); assign(wobj,'MD_MatWalk')

        # Camera
        make_camera()

        if 'metadyn_sim_data' in ctx.scene: del ctx.scene['metadyn_sim_data']

        for area in ctx.screen.areas:
            if area.type == 'VIEW_3D':
                region = next((r for r in area.regions if r.type == 'WINDOW'), None)
                if region:
                    with ctx.temp_override(area=area, region=region):
                        bpy.ops.view3d.view_all(center=False)
                break

        self.report({'INFO'},"Escena creada. Ahora pulsa 'Simular y Hornear'.")
        return {'FINISHED'}

class MD_OT_Bake(Operator):
    bl_idname="md.bake"; bl_label="2. Simular y Hornear"
    bl_description="Corre la simulación y activa la animación"
    def execute(self,ctx):
        p=ctx.scene.md_props
        if not p.wells: self.report({'WARNING'},"Sin pozos."); return {'CANCELLED'}
        if not bpy.data.objects.get('MD_PES'): self.report({'WARNING'},"Crea la escena primero."); return {'CANCELLED'}
        wells=[{'p':w.p,'d':w.d,'w':w.w} for w in p.wells]
        cfg={'wells':wells,'seed':p.seed,'steps':p.steps,'T':p.T,'W':p.W,
             'sig':p.sig,'stride':p.stride,'wt':p.wt,'gam':p.gam}
        frames,gauss=simulate(cfg)
        ctx.scene['metadyn_sim_data']=json.dumps({'f':frames,'g':gauss,'w':wells})
        ctx.scene.frame_start=1; ctx.scene.frame_end=p.steps
        reg_handler(); ctx.scene.frame_set(1)
        self.report({'INFO'},f"Listo: {p.steps} frames, {len(gauss)} gaussianas. Pulsa SPACE.")
        return {'FINISHED'}

class MD_OT_ReHook(Operator):
    bl_idname="md.rehook"; bl_label="Re-registrar Handler"
    def execute(self,ctx):
        if not ctx.scene.get('metadyn_sim_data'): self.report({'WARNING'},"Sin datos. Hornea primero."); return {'CANCELLED'}
        reg_handler(); ctx.scene.frame_set(ctx.scene.frame_current)
        self.report({'INFO'},"Handler activo."); return {'FINISHED'}

class MD_OT_Clear(Operator):
    bl_idname="md.clear"; bl_label="Limpiar Todo"
    def execute(self,ctx):
        unreg_handler()
        for name in NAMES:
            o=bpy.data.objects.get(name)
            if o:
                if o.data and hasattr(o.data,'users'): bpy.data.meshes.remove(o.data,do_unlink=True)
                else: bpy.data.objects.remove(o,do_unlink=True)
        for mn in ['MD_MatPES','MD_MatPESEd','MD_MatBias','MD_MatBiasEd',
                   'MD_MatWalk','MD_MatZero','MD_MatGrid']:
            m=bpy.data.materials.get(mn)
            if m: bpy.data.materials.remove(m)
        if 'metadyn_sim_data' in ctx.scene: del ctx.scene['metadyn_sim_data']
        self.report({'INFO'},"Escena limpiada."); return {'FINISHED'}

# ─────────────────────────────────────────────
# PANEL
# ─────────────────────────────────────────────
class MD_UL_Wells(UIList):
    def draw_item(self,ctx,layout,data,item,icon,active_data,active_propname):
        layout.label(text=f"p={item.p:.1f}  depth={item.d:.1f}  w={item.w:.2f}",icon='FORCE_HARMONIC')

class MD_PT_Panel(Panel):
    bl_label="Metadynamics Animator"; bl_idname="MD_PT_Panel"
    bl_space_type='VIEW_3D'; bl_region_type='UI'; bl_category="Metadyn"

    def draw(self,ctx):
        layout=self.layout; p=ctx.scene.md_props

        # Pozos
        b=layout.box(); b.label(text="Pozos de Potencial",icon='FORCE_HARMONIC')
        r=b.row()
        r.template_list("MD_UL_Wells","",p,"wells",p,"well_idx",rows=3)
        c=r.column(align=True)
        c.operator("md.add_well",text="",icon='ADD')
        c.operator("md.remove_well",text="",icon='REMOVE')
        if len(p.wells)>0 and p.well_idx<len(p.wells):
            w=p.wells[p.well_idx]; sub=b.column(align=True)
            sub.prop(w,"p",slider=True); sub.prop(w,"d",slider=True); sub.prop(w,"w",slider=True)

        # Parámetros
        b=layout.box(); b.label(text="Simulación",icon='SETTINGS')
        c=b.column(align=True)
        c.prop(p,"steps"); c.prop(p,"T",slider=True)
        c.prop(p,"W",slider=True); c.prop(p,"sig",slider=True)
        c.prop(p,"stride"); c.prop(p,"seed")

        # Well-Tempered
        b=layout.box(); r=b.row(); r.prop(p,"wt",toggle=True)
        if p.wt: b.prop(p,"gam",slider=True)

        layout.separator()
        c=layout.column(align=True); c.scale_y=1.5
        c.operator("md.setup",   icon='SCENE_DATA')
        c.operator("md.bake",    icon='PLAY')
        c.separator()
        c.operator("md.rehook",  icon='FILE_REFRESH', text="Re-registrar Handler")
        c.separator()
        c.operator("md.clear",   icon='TRASH')

        # Estado
        layout.separator(); b=layout.box()
        has_data=bool(ctx.scene.get('metadyn_sim_data'))
        has_objs=bool(bpy.data.objects.get('MD_PES'))
        b.label(text=("✓ Escena lista" if has_objs else "✗ Sin escena"),    icon='OBJECT_DATA')
        b.label(text=("✓ Datos simulados" if has_data else "✗ Sin datos"), icon='RNA')
        b.label(text=("✓ Handler activo" if _handler_on else "✗ Handler OFF"),icon='SCRIPT')

# ─────────────────────────────────────────────
# REGISTRO
# ─────────────────────────────────────────────
classes=[MDWell,MDProps,MD_UL_Wells,MD_OT_AddWell,MD_OT_RemoveWell,
         MD_OT_Setup,MD_OT_Bake,MD_OT_ReHook,MD_OT_Clear,MD_PT_Panel]

def register():
    for cls in classes: bpy.utils.register_class(cls)
    bpy.types.Scene.md_props=bpy.props.PointerProperty(type=MDProps)

def unregister():
    unreg_handler()
    for cls in reversed(classes): bpy.utils.unregister_class(cls)
    del bpy.types.Scene.md_props

if __name__=="__main__": register()

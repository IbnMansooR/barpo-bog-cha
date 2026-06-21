# v2: materiallar UV/tekstura mapping'ini tozalab muammoli .blend ni GLB ga eksport qiladi.
#   blender --background --python tools/fix_one_v2.py -- "<input.blend>" "<output.glb>" [max_tex]
import bpy, sys, os, math

argv = sys.argv
argv = argv[argv.index("--") + 1:] if "--" in argv else []
inp, out = argv[0], argv[1]
MAX_TEX = int(argv[2]) if len(argv) > 2 else 2048

bpy.ops.wm.open_mainfile(filepath=inp)
print("Opened:", inp, flush=True)

# 1) Buzuq (hajmi yo'q) rasmlarni olib tashlaymiz
removed = 0
for img in list(bpy.data.images):
    try:
        if (img.size[0] == 0 or img.size[1] == 0) and img.name not in ("Render Result", "Viewer Node"):
            bpy.data.images.remove(img); removed += 1
    except Exception:
        pass
print("Buzuq rasm olib tashlandi:", removed, flush=True)

# 2) Texturalarni kichraytirish
shrunk = 0
for img in list(bpy.data.images):
    try:
        w, h = img.size; m = max(w, h)
        if m > MAX_TEX:
            s = MAX_TEX / m
            img.scale(max(1, int(w * s)), max(1, int(h * s))); shrunk += 1
    except Exception:
        pass
print("Tex kichraytirildi:", shrunk, flush=True)

# 3) Har bir mesh'da UV bo'lishini ta'minlash
no_uv = 0
for ob in bpy.data.objects:
    if ob.type == 'MESH' and ob.data is not None:
        me = ob.data
        if len(me.uv_layers) == 0:
            try:
                me.uv_layers.new(name="UVMap"); no_uv += 1
            except Exception:
                pass
print("UV qo'shilgan mesh:", no_uv, flush=True)

# 4) Materiallar: Mapping/TexCoord node'larni olib tashlab, Image Texture'ni toza UV (uv_map="") ga ulaymiz
cleaned = 0
for mat in bpy.data.materials:
    if not (mat.use_nodes and mat.node_tree):
        continue
    nt = mat.node_tree
    nodes, links = nt.nodes, nt.links
    img_nodes = [n for n in nodes if n.type == 'TEX_IMAGE']
    for tn in img_nodes:
        vec = tn.inputs.get('Vector')
        if vec is None:
            continue
        # mavjud ulanishlarni uzamiz
        for l in list(vec.links):
            links.remove(l)
        # toza UV Map node (uv_map bo'sh -> har mesh'ning active UV'si ishlatiladi)
        uvn = nodes.new('ShaderNodeUVMap')
        uvn.uv_map = ""
        uvn.location = (tn.location.x - 300, tn.location.y)
        links.new(uvn.outputs['UV'], vec)
        cleaned += 1
    # endi yetim Mapping / TexCoord node'larni o'chiramiz
    for n in list(nodes):
        if n.type in ('MAPPING', 'TEX_COORD'):
            if not any(o.is_linked for o in n.outputs):
                nodes.remove(n)
    # NaN/inf tozalash
    for node in nodes:
        for s in node.inputs:
            try:
                v = s.default_value
                try:
                    for i in range(len(v)):
                        if isinstance(v[i], float) and (math.isnan(v[i]) or math.isinf(v[i])):
                            v[i] = 0.0
                except TypeError:
                    if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
                        s.default_value = 0.0
            except Exception:
                pass
print("Tekstura node toza UV'ga ulandi:", cleaned, flush=True)

# 5) Eksport
base = dict(filepath=out, export_format='GLB', use_selection=False, export_apply=True,
            export_animations=False)
draco = dict(export_draco_mesh_compression_enable=True, export_draco_mesh_compression_level=6)
exported = False
for extra in (
    {**draco, "export_yup": True, "export_cameras": False, "export_lights": False},
    {**draco, "export_yup": True},
    {**draco},
    {"export_yup": True},
    {},
):
    try:
        bpy.ops.export_scene.gltf(**{**base, **extra})
        exported = True
        break
    except TypeError:
        continue
    except Exception as e:
        print("EXPORT EXCEPTION:", repr(e)[:300], flush=True)
        break

if exported and os.path.exists(out):
    sz = os.path.getsize(out) / (1024 * 1024)
    print(f"OK [{sz:.1f} MB] -> {out}", flush=True)
else:
    print("EKSPORT BO'LMADI", flush=True)

# Bitta muammoli .blend ni tozalab GLB ga eksport qiladi.
#   blender --background --python tools/fix_one.py -- "<input.blend>" "<output.glb>" [max_tex]
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
        if img.size[0] == 0 or img.size[1] == 0:
            if img.name not in ("Render Result", "Viewer Node"):
                bpy.data.images.remove(img)
                removed += 1
    except Exception:
        pass
print("Buzuq rasm olib tashlandi:", removed, flush=True)

# 2) Texturalarni kichraytirish
shrunk = 0
for img in list(bpy.data.images):
    try:
        w, h = img.size
        m = max(w, h)
        if m > MAX_TEX:
            s = MAX_TEX / m
            img.scale(max(1, int(w * s)), max(1, int(h * s)))
            shrunk += 1
    except Exception:
        pass
print("Tex kichraytirildi:", shrunk, flush=True)

# 3) Materiallardagi NaN/inf qiymatlarni tozalash
fixed = 0
def clean_val(inp_socket):
    global fixed
    try:
        v = inp_socket.default_value
    except Exception:
        return
    try:
        n = len(v)
        for i in range(n):
            x = v[i]
            if isinstance(x, float) and (math.isnan(x) or math.isinf(x)):
                v[i] = 0.0; fixed += 1
    except TypeError:
        if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
            try:
                inp_socket.default_value = 0.0; fixed += 1
            except Exception:
                pass

for mat in bpy.data.materials:
    if mat.use_nodes and mat.node_tree:
        for node in mat.node_tree.nodes:
            for s in node.inputs:
                clean_val(s)
print("NaN/inf tuzatildi:", fixed, flush=True)

# 4) Eksport (animatsiyasiz, Draco bilan)
base = dict(filepath=out, export_format='GLB', use_selection=False, export_apply=True,
            export_animations=False)
draco = dict(export_draco_mesh_compression_enable=True, export_draco_mesh_compression_level=6)
for extra in (
    {**draco, "export_yup": True, "export_cameras": False, "export_lights": False},
    {**draco, "export_yup": True},
    {**draco},
    {"export_yup": True},
    {},
):
    try:
        bpy.ops.export_scene.gltf(**{**base, **extra})
        break
    except TypeError:
        continue

sz = os.path.getsize(out) / (1024 * 1024)
print(f"OK [{sz:.1f} MB] -> {out}", flush=True)

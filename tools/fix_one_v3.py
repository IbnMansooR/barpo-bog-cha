# v3: yaroqsiz rasmli TEX_IMAGE node'larni materialdan olib tashlab eksport qiladi.
#   blender --background --python tools/fix_one_v3.py -- "<input.blend>" "<output.glb>" [max_tex]
import bpy, sys, os, math

argv = sys.argv
argv = argv[argv.index("--") + 1:] if "--" in argv else []
inp, out = argv[0], argv[1]
MAX_TEX = int(argv[2]) if len(argv) > 2 else 2048

bpy.ops.wm.open_mainfile(filepath=inp)
print("Opened:", inp, flush=True)


def img_bad(img):
    if img is None:
        return True
    try:
        if img.size[0] == 0 or img.size[1] == 0:
            return True
        if not img.has_data and not img.packed_file and not (img.filepath and os.path.exists(bpy.path.abspath(img.filepath))):
            return True
    except Exception:
        return True
    return False


# 1) Materiallardan yaroqsiz rasmli TEX_IMAGE node'larni olib tashlash
removed_nodes = 0
for mat in bpy.data.materials:
    if not (mat.use_nodes and mat.node_tree):
        continue
    nt = mat.node_tree
    for node in list(nt.nodes):
        if node.type == 'TEX_IMAGE' and img_bad(node.image):
            nt.nodes.remove(node)
            removed_nodes += 1
print("Yaroqsiz tekstura node olib tashlandi:", removed_nodes, flush=True)

# 2) Endi orfan/buzuq rasmlarni data'dan tozalash
for img in list(bpy.data.images):
    try:
        if img.name in ("Render Result", "Viewer Node"):
            continue
        if img.size[0] == 0 or img.size[1] == 0:
            bpy.data.images.remove(img)
    except Exception:
        pass

# 3) Texturalarni kichraytirish
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

# 4) NaN/inf tozalash
for mat in bpy.data.materials:
    if mat.use_nodes and mat.node_tree:
        for node in mat.node_tree.nodes:
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
        bpy.ops.export_scene.gltf(**{**base, **extra}); exported = True; break
    except TypeError:
        continue
    except Exception as e:
        print("EXPORT EXCEPTION:", repr(e)[:200], flush=True); break

if exported and os.path.exists(out):
    print(f"OK [{os.path.getsize(out)/(1024*1024):.1f} MB] -> {out}", flush=True)
else:
    print("EKSPORT BO'LMADI", flush=True)

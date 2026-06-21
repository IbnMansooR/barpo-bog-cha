# To'liq tuzatuvchi eksport: papkadagi barcha .blend -> GLB
#   - yaroqsiz rasmli TEX_IMAGE node'larini olib tashlaydi
#   - Mapping node'lardagi X/Y rotation'ni 0 ga tushiradi (tekstura transform eksport bo'lsin)
#   - texturalarni MAX_TEX px gacha kichraytiradi
#   - Draco bilan, animatsiyasiz eksport
# blender --background --python tools/export_all_fixed.py -- "<in_dir>" "<out_dir>" [max_tex]
import bpy, sys, os, glob, math

argv = sys.argv
argv = argv[argv.index("--") + 1:] if "--" in argv else []
in_dir, out_dir = argv[0], argv[1]
MAX_TEX = int(argv[2]) if len(argv) > 2 else 2048
os.makedirs(out_dir, exist_ok=True)

blends = sorted(b for b in glob.glob(os.path.join(in_dir, "**", "*.blend"), recursive=True)
                if b.lower().endswith(".blend"))
print(f"\n=== {len(blends)} ta .blend ===\n", flush=True)


def img_bad(img):
    if img is None:
        return True
    try:
        if img.size[0] == 0 or img.size[1] == 0:
            return True
        if not img.has_data and not img.packed_file and not (
                img.filepath and os.path.exists(bpy.path.abspath(img.filepath))):
            return True
    except Exception:
        return True
    return False


def fix_materials():
    bad_nodes = 0
    map_fixed = 0
    for mat in bpy.data.materials:
        if not (mat.use_nodes and mat.node_tree):
            continue
        nt = mat.node_tree
        for node in list(nt.nodes):
            # yaroqsiz rasmli node -> o'chirish
            if node.type == 'TEX_IMAGE' and img_bad(node.image):
                nt.nodes.remove(node); bad_nodes += 1
                continue
            # Mapping node: X/Y rotation'ni 0 ga (glTF faqat Z rotation'ni qo'llaydi)
            if node.type == 'MAPPING':
                try:
                    rot = node.inputs.get('Rotation')
                    if rot is not None:
                        v = rot.default_value
                        if abs(v[0]) > 1e-6 or abs(v[1]) > 1e-6:
                            v[0] = 0.0; v[1] = 0.0; map_fixed += 1
                except Exception:
                    pass
            # NaN/inf
            for s in node.inputs:
                try:
                    val = s.default_value
                    try:
                        for i in range(len(val)):
                            if isinstance(val[i], float) and (math.isnan(val[i]) or math.isinf(val[i])):
                                val[i] = 0.0
                    except TypeError:
                        if isinstance(val, float) and (math.isnan(val) or math.isinf(val)):
                            s.default_value = 0.0
                except Exception:
                    pass
    return bad_nodes, map_fixed


def shrink():
    n = 0
    for img in list(bpy.data.images):
        try:
            w, h = img.size; m = max(w, h)
            if m > MAX_TEX:
                s = MAX_TEX / m
                img.scale(max(1, int(w * s)), max(1, int(h * s))); n += 1
        except Exception:
            pass
    return n


def export_glb(out):
    base = dict(filepath=out, export_format='GLB', use_selection=False,
                export_apply=True, export_animations=False)
    draco = dict(export_draco_mesh_compression_enable=True, export_draco_mesh_compression_level=6)
    for extra in (
        {**draco, "export_yup": True, "export_cameras": False, "export_lights": False},
        {**draco, "export_yup": True},
        {**draco},
        {"export_yup": True},
        {},
    ):
        try:
            bpy.ops.export_scene.gltf(**{**base, **extra}); return True
        except TypeError:
            continue
        except Exception as e:
            print("   EXPORT EXCEPTION:", repr(e)[:160], flush=True); return False
    return False


used = {}
ok = fail = 0
for b in blends:
    name = os.path.splitext(os.path.basename(b))[0]
    try:
        bpy.ops.wm.open_mainfile(filepath=b)
        bad, mf = fix_materials()
        sh = shrink()
        n = used.get(name.lower(), 0)
        oname = f"{name}-{n+1}" if n else name
        used[name.lower()] = n + 1
        out = os.path.join(out_dir, oname + ".glb")
        if export_glb(out) and os.path.exists(out):
            sz = os.path.getsize(out) / (1024 * 1024)
            print(f"OK  [{sz:7.1f} MB | bad_tex {bad} | map_fix {mf} | shrink {sh}]  {name}.glb", flush=True)
            ok += 1
        else:
            print(f"FAIL  {name}", flush=True); fail += 1
    except Exception as e:
        print(f"FAIL  {name}\n   {repr(e)[:200]}", flush=True); fail += 1

print(f"\n=== {ok} OK, {fail} FAIL ===", flush=True)

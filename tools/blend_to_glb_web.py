# Blender headless: .blend -> GLB (WEB uchun optimallashtirilgan)
#   - texturalarni MAX_TEX px gacha kichraytiradi
#   - Draco geometriya siqishini yoqadi
# Ishlatish:
#   blender --background --python tools/blend_to_glb_web.py -- "<input_dir>" "<output_dir>" [MAX_TEX]
import bpy, sys, os, glob

argv = sys.argv
argv = argv[argv.index("--") + 1:] if "--" in argv else []
if len(argv) < 2:
    print("Usage: ... -- <input_dir> <output_dir> [max_tex]")
    sys.exit(1)

in_dir, out_dir = argv[0], argv[1]
MAX_TEX = int(argv[2]) if len(argv) > 2 else 2048
os.makedirs(out_dir, exist_ok=True)

blends = sorted(glob.glob(os.path.join(in_dir, "**", "*.blend"), recursive=True))
blends = [b for b in blends if b.lower().endswith(".blend")]
print(f"\n=== {len(blends)} ta .blend | tex<= {MAX_TEX}px | Draco ON ===\n", flush=True)


def shrink_textures():
    n = 0
    for img in list(bpy.data.images):
        try:
            w, h = img.size
            if w <= 0 or h <= 0:
                continue
            m = max(w, h)
            if m > MAX_TEX:
                s = MAX_TEX / m
                img.scale(max(1, int(w * s)), max(1, int(h * s)))
                n += 1
        except Exception:
            pass
    return n


def export_glb(out):
    base = dict(filepath=out, export_format='GLB', use_selection=False, export_apply=True)
    draco = dict(
        export_draco_mesh_compression_enable=True,
        export_draco_mesh_compression_level=6,
    )
    extra_sets = [
        {**draco, "export_yup": True, "export_cameras": False, "export_lights": False},
        {**draco, "export_yup": True},
        {**draco},
        {"export_yup": True},
        {},
    ]
    for extra in extra_sets:
        try:
            bpy.ops.export_scene.gltf(**{**base, **extra})
            return "draco" in str(extra)
        except TypeError:
            continue
    bpy.ops.export_scene.gltf(filepath=out)
    return False


used = {}
ok, fail = 0, 0
for b in blends:
    try:
        bpy.ops.wm.open_mainfile(filepath=b)
        shrunk = shrink_textures()
        base = os.path.splitext(os.path.basename(b))[0]
        n = used.get(base.lower(), 0)
        name = f"{base}-{n+1}" if n else base
        used[base.lower()] = n + 1

        out = os.path.join(out_dir, name + ".glb")
        used_draco = export_glb(out)
        sz = os.path.getsize(out) / (1024 * 1024)
        tag = "draco" if used_draco else "no-draco"
        print(f"OK  [{sz:7.1f} MB | {tag} | {shrunk} tex shrunk]  {os.path.basename(b)} -> {name}.glb", flush=True)
        ok += 1
    except Exception as e:
        print(f"FAIL  {b}\n      {e}", flush=True)
        fail += 1

print(f"\n=== Tayyor: {ok} OK, {fail} xato ===", flush=True)

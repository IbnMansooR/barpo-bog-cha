# Blender headless skript: papkadagi barcha .blend fayllarni GLB ga eksport qiladi.
# Ishlatish:
#   blender --background --python tools/blend_to_glb.py -- "<input_dir>" "<output_dir>"
import bpy, sys, os, glob

argv = sys.argv
argv = argv[argv.index("--") + 1:] if "--" in argv else []
if len(argv) < 2:
    print("Usage: ... -- <input_dir> <output_dir>")
    sys.exit(1)

in_dir, out_dir = argv[0], argv[1]
os.makedirs(out_dir, exist_ok=True)

blends = sorted(glob.glob(os.path.join(in_dir, "**", "*.blend"), recursive=True))
blends = [b for b in blends if b.lower().endswith(".blend")]

print(f"\n=== {len(blends)} ta .blend fayl topildi ===\n", flush=True)


def export_glb(out):
    # Blender versiyalari orasida parametrlar farq qilishi mumkin -> bosqichma-bosqich
    opts = dict(filepath=out, export_format='GLB', use_selection=False, export_apply=True)
    for extra in (
        dict(export_yup=True, export_cameras=False, export_lights=False),
        dict(export_yup=True),
        dict(),
    ):
        try:
            bpy.ops.export_scene.gltf(**{**opts, **extra})
            return
        except TypeError:
            continue
    bpy.ops.export_scene.gltf(filepath=out)  # eng minimal


used = {}
ok, fail = 0, 0
for b in blends:
    try:
        bpy.ops.wm.open_mainfile(filepath=b)
        base = os.path.splitext(os.path.basename(b))[0]
        n = used.get(base.lower(), 0)
        name = f"{base}-{n+1}" if n else base
        used[base.lower()] = n + 1

        out = os.path.join(out_dir, name + ".glb")
        export_glb(out)
        sz = os.path.getsize(out) / (1024 * 1024)
        print(f"OK   [{sz:7.1f} MB]  {os.path.basename(b)}  ->  {name}.glb", flush=True)
        ok += 1
    except Exception as e:
        print(f"FAIL  {b}\n      {e}", flush=True)
        fail += 1

print(f"\n=== Tayyor: {ok} ta muvaffaqiyatli, {fail} ta xato ===", flush=True)

# Object/Generated koordinatali teksturalarni UV ga o'tkazib eksport qiladi.
# blender --background --python tools/export_uvfix.py -- "<in_dir>" "<out_dir>" [max_tex]
import bpy, sys, os, glob, math

argv = sys.argv
argv = argv[argv.index("--") + 1:] if "--" in argv else []
in_dir, out_dir = argv[0], argv[1]
MAX_TEX = int(argv[2]) if len(argv) > 2 else 2048
os.makedirs(out_dir, exist_ok=True)

blends = sorted(b for b in glob.glob(os.path.join(in_dir, "**", "*.blend"), recursive=True)
                if b.lower().endswith(".blend"))
print(f"\n=== {len(blends)} ta .blend ===\n", flush=True)

NON_UV = {'Generated', 'Object', 'Camera', 'Window', 'Reflection', 'Normal'}


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


def real_source(socket):
    """reroute'lar orqali asl manbani topadi -> (node, output_name) yoki None"""
    if not socket or not socket.is_linked:
        return None
    ln = socket.links[0]
    n, sname = ln.from_node, ln.from_socket.name
    guard = 0
    while n.type == 'REROUTE' and guard < 50:
        inp = n.inputs[0]
        if not inp.is_linked:
            return None
        ln = inp.links[0]; n, sname = ln.from_node, ln.from_socket.name
        guard += 1
    return n, sname


def set_uv(nt, socket):
    for l in list(socket.links):
        nt.links.remove(l)
    uvn = nt.nodes.new('ShaderNodeUVMap')
    uvn.uv_map = ""  # bo'sh -> har mesh'ning active UV'si
    nt.links.new(uvn.outputs['UV'], socket)


def fix_materials():
    bad, rewired = 0, 0
    for mat in bpy.data.materials:
        if not (mat.use_nodes and mat.node_tree):
            continue
        nt = mat.node_tree
        for node in list(nt.nodes):
            if node.type == 'TEX_IMAGE' and img_bad(node.image):
                nt.nodes.remove(node); bad += 1
        for node in list(nt.nodes):
            if node.type != 'TEX_IMAGE':
                continue
            vec = node.inputs.get('Vector')
            src = real_source(vec)
            if src is None:
                continue  # AUTO-UV
            snode, sout = src
            if snode.type == 'MAPPING':
                msrc = real_source(snode.inputs.get('Vector'))
                if msrc is None:
                    continue
                mnode, mout = msrc
                if mnode.type == 'TEX_COORD' and mout in NON_UV:
                    set_uv(nt, snode.inputs['Vector']); rewired += 1
                elif mnode.type not in ('UVMAP',) and not (mnode.type == 'TEX_COORD' and mout == 'UV'):
                    if mout in NON_UV:
                        set_uv(nt, snode.inputs['Vector']); rewired += 1
            elif snode.type == 'TEX_COORD' and sout in NON_UV:
                set_uv(nt, vec); rewired += 1
        # mapping X/Y rotation -> 0  va NaN tozalash
        for node in nt.nodes:
            if node.type == 'MAPPING':
                try:
                    r = node.inputs.get('Rotation')
                    if r is not None:
                        v = r.default_value
                        v[0] = 0.0; v[1] = 0.0
                except Exception:
                    pass
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
    return bad, rewired


def ensure_uv():
    n = 0
    for ob in bpy.data.objects:
        if ob.type == 'MESH' and ob.data and len(ob.data.uv_layers) == 0:
            try:
                ob.data.uv_layers.new(name="UVMap"); n += 1
            except Exception:
                pass
    return n


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


def strip_all_textures():
    """zaxira: barcha TEX_IMAGE node'larni olib tashlaydi (tekisrang)"""
    for mat in bpy.data.materials:
        if mat.use_nodes and mat.node_tree:
            for node in list(mat.node_tree.nodes):
                if node.type == 'TEX_IMAGE':
                    mat.node_tree.nodes.remove(node)


def export_glb(out):
    base = dict(filepath=out, export_format='GLB', use_selection=False,
                export_apply=True, export_animations=False)
    draco = dict(export_draco_mesh_compression_enable=True, export_draco_mesh_compression_level=6)
    for extra in (
        {**draco, "export_yup": True, "export_cameras": False, "export_lights": False},
        {**draco, "export_yup": True}, {**draco}, {"export_yup": True}, {},
    ):
        try:
            bpy.ops.export_scene.gltf(**{**base, **extra}); return True
        except TypeError:
            continue
        except Exception:
            return False
    return False


used = {}
ok = fail = 0
for b in blends:
    name = os.path.splitext(os.path.basename(b))[0]
    try:
        bpy.ops.wm.open_mainfile(filepath=b)
        bad, rew = fix_materials()
        uv = ensure_uv()
        sh = shrink()
        n = used.get(name.lower(), 0)
        oname = f"{name}-{n+1}" if n else name
        used[name.lower()] = n + 1
        out = os.path.join(out_dir, oname + ".glb")
        note = ""
        if not (export_glb(out) and os.path.exists(out)):
            # zaxira: teksturasiz qayta urinish
            strip_all_textures()
            note = " (TEKSTURASIZ-zaxira)"
            export_glb(out)
        if os.path.exists(out):
            sz = os.path.getsize(out) / (1024 * 1024)
            print(f"OK  [{sz:7.1f} MB | bad {bad} | uv→ {rew} | +uv {uv} | shrink {sh}]{note}  {name}", flush=True)
            ok += 1
        else:
            print(f"FAIL  {name}", flush=True); fail += 1
    except Exception as e:
        print(f"FAIL  {name}: {repr(e)[:160]}", flush=True); fail += 1

print(f"\n=== {ok} OK, {fail} FAIL ===", flush=True)

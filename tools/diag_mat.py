import bpy, sys
argv = sys.argv; argv = argv[argv.index("--")+1:]
bpy.ops.wm.open_mainfile(filepath=argv[0])

def vec_source(node):
    vec = node.inputs.get('Vector')
    if not vec or not vec.is_linked:
        return "AUTO-UV (default)"
    fn = vec.links[0].from_node
    fs = vec.links[0].from_socket.name
    if fn.type == 'MAPPING':
        mv = fn.inputs.get('Vector')
        if mv and mv.is_linked:
            return f"MAPPING <- {fn2type(mv)}"
        return "MAPPING <- (none)"
    if fn.type == 'TEX_COORD':
        return f"TexCoord:{fs}"
    if fn.type == 'UVMAP':
        return f"UVMap:'{fn.uv_map}'"
    return fn.type

def fn2type(sock):
    n = sock.links[0].from_node; s = sock.links[0].from_socket.name
    if n.type == 'TEX_COORD': return f"TexCoord:{s}"
    if n.type == 'UVMAP': return f"UVMap:'{n.uv_map}'"
    return n.type

# materiallarni hisoblaymiz
from collections import Counter
srcs = Counter()
rows = []
for mat in bpy.data.materials:
    if not (mat.use_nodes and mat.node_tree): continue
    for node in mat.node_tree.nodes:
        if node.type == 'TEX_IMAGE':
            s = vec_source(node)
            srcs[s] += 1
            rows.append(f"{mat.name[:34]:34} | {(node.image.name if node.image else 'NoImg')[:28]:28} | {s}")

print("\n=== KOORDINATA MANBAI BO'YICHA ===")
for k, v in srcs.most_common():
    print(f"  {v:4}  {k}")
print(f"\n=== Jami {len(rows)} ta tekstura node (birinchi 60) ===")
for r in rows[:60]:
    print(r)

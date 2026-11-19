# Mesh the BoxTurtle v1.1 hub/buffer combo from BT_V1.1_release.step (GPL-3.0, ArmoredTurtle/BoxTurtle, CAD/Cad.zip).
#   STEP_IN=/path/to/BT_V1.1_release.step freecadcmd tools/export_btcombo.py
# Writes cad/btcombo.npz and cad/btcombo.json. AGPL-3.0 (see LICENSE).
import os, json, FreeCAD, Import, MeshPart, numpy as np
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
doc = FreeCAD.newDocument(); Import.insert(os.environ["STEP_IN"], doc.Name); out = {}; names = []
def walk(o, pp):
    p = pp + [o.Label]; ps = "/".join(p); kids = getattr(o, "Group", None)
    if kids:
        for c in kids: walk(c, p)
    elif o.TypeId.startswith("Part::") and "/hub_buffer_combo/" in ps:
        sh = o.Shape.copy(); sh.Placement = o.getGlobalPlacement()
        if not sh.Solids: return
        m = MeshPart.meshFromShape(Shape=sh, LinearDeflection=0.03, AngularDeflection=0.35, Relative=False)
        k = "p%03d" % len(names)
        out[k + "_V"] = np.array([[v.x, v.y, v.z] for v in m.Points], np.float32)
        out[k + "_F"] = np.array([list(f.PointIndices) for f in m.Facets], np.int32); names.append(ps.split("/hub_buffer_combo/")[1])
for r in [o for o in doc.Objects if not o.InList]: walk(r, [])
np.savez_compressed(os.path.join(ROOT, "cad/btcombo.npz"), **out); json.dump(names, open(os.path.join(ROOT, "cad/btcombo.json"), "w"), indent=0)
print("done", len(names))

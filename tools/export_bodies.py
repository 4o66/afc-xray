# Mesh the single- and no-switch FilamATrix CW2 main bodies from the FilamATrix Stealthburner STEP (GPL-3.0).
#   STEP_IN=/path/to/Stealthburner_FilamATrix.step freecadcmd tools/export_bodies.py
# Writes cad/bodies_cw2.npz and cad/bodies_cw2.json. AGPL-3.0 (see LICENSE).
import os, json, FreeCAD, Import, MeshPart, numpy as np
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
doc = FreeCAD.newDocument(); Import.insert(os.environ["STEP_IN"], doc.Name); out = {}; names = []
def walk(o, pp):
    p = pp + [o.Label]; ps = "/".join(p); kids = getattr(o, "Group", None)
    if kids:
        for c in kids: walk(c, p)
    elif o.TypeId.startswith("Part::") and ("Main_Body_No_Switch" in ps or "Main_Body_One_Switch" in ps):
        sh = o.Shape.copy(); sh.Placement = o.getGlobalPlacement()
        m = MeshPart.meshFromShape(Shape=sh, LinearDeflection=0.03, AngularDeflection=0.35, Relative=False)
        k = "p%03d" % len(names)
        out[k + "_V"] = np.array([[v.x, v.y, v.z] for v in m.Points], np.float32)
        out[k + "_F"] = np.array([list(f.PointIndices) for f in m.Facets], np.int32); names.append(ps)
for r in [o for o in doc.Objects if not o.InList]: walk(r, [])
np.savez_compressed(os.path.join(ROOT, "cad/bodies_cw2.npz"), **out); json.dump(names, open(os.path.join(ROOT, "cad/bodies_cw2.json"), "w")); print("done", names)

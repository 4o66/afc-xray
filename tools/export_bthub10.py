# Mesh the BoxTurtle v1.0 hub (Rear/Hubs/Hub_D2HW v2, GPL-3.0, ArmoredTurtle/BoxTurtle tag BT-1.0, CAD/Cad.zip) and its
# five ECAS04 collets (Rear/Hardware (1)/ECAS Bowden Collet*), in the v1.0 assembly's frame.
#   STEP_IN=/path/to/BoxTurtle.step freecadcmd tools/export_bthub10.py
# Writes cad/bthub10_raw.{npz,json}; tools/place_bthub10.py moves it into the v1.1 hubs' frame. AGPL-3.0 (see LICENSE).
import os, json, re, FreeCAD, Import, MeshPart, numpy as np
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
doc = FreeCAD.newDocument(); Import.insert(os.environ["STEP_IN"], doc.Name); out = {}; names = []
def walk(o, pp):
    p = pp + [o.Label]; ps = "/".join(p); kids = getattr(o, "Group", None)
    if kids:
        for c in kids: walk(c, p)
    elif o.TypeId.startswith("Part::") and ("/Hub_D2HW v2/" in ps or re.search(r"/Rear/Hardware \(1\)/ECAS Bowden Collet", ps)):
        sh = o.Shape.copy(); sh.Placement = o.getGlobalPlacement()
        if not sh.Solids and not sh.Faces: return
        m = MeshPart.meshFromShape(Shape=sh, LinearDeflection=0.03, AngularDeflection=0.35, Relative=False)
        k = "p%03d" % len(names)
        out[k + "_V"] = np.array([[v.x, v.y, v.z] for v in m.Points], np.float32)
        out[k + "_F"] = np.array([list(f.PointIndices) for f in m.Facets], np.int32)
        names.append(ps.split("/Rear/")[1])
for r in [o for o in doc.Objects if not o.InList]: walk(r, [])
np.savez_compressed(os.path.join(ROOT, "cad/bthub10_raw.npz"), **out); json.dump(names, open(os.path.join(ROOT, "cad/bthub10_raw.json"), "w"), indent=0)
print("done", len(names))

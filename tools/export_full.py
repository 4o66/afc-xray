# Mesh the toolhead parts out of the FilamATrix Stealthburner STEP (GPL-3.0, github.com/thunderkeys/FilamATrix, CAD/).
# Run with FreeCAD's command-line interpreter:
#   STEP_IN=/path/to/Stealthburner_FilamATrix.step freecadcmd tools/export_full.py
# Writes cad/full_parts.npz and cad/full_names.json. AGPL-3.0 (see LICENSE).
import os, time, json, FreeCAD, Import, MeshPart, numpy as np
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."); t0 = time.time()
doc = FreeCAD.newDocument(); Import.insert(os.environ["STEP_IN"], doc.Name); print("loaded", round(time.time() - t0), flush=True)
R = "Stealthburner_FilamATrix v5/"
INC = ["Clockwork2 FilamATrix/", "Hotends/Rapido Hotends/Rapido_UHF_V2/", "Hotends/Rapido Hotends/Hardware (6)/", "Stealthburner/", "Stealthburner_UHF", "X_Carriage (1)/"]
EXC = ["Main_Body_No_Switch", "Main_Body_One_Switch", "Cable_Cover_EBB", "Cover_w_Sensor", "probe_bracket"]
out = {}; names = []
def walk(o, pp):
    p = pp + [o.Label]; ps = "/".join(p); kids = getattr(o, "Group", None)
    if kids:
        for c in kids: walk(c, p)
    elif o.TypeId.startswith("Part::") and ps.startswith(R):
        q = ps[len(R):]
        if not any(q.startswith(i) for i in INC) or any(e in q for e in EXC): return
        sh = o.Shape.copy(); sh.Placement = o.getGlobalPlacement()
        if not sh.Solids: return
        m = MeshPart.meshFromShape(Shape=sh, LinearDeflection=0.03, AngularDeflection=0.35, Relative=False)
        k = "p%03d" % len(names)
        out[k + "_V"] = np.array([[v.x, v.y, v.z] for v in m.Points], np.float32)
        out[k + "_F"] = np.array([list(f.PointIndices) for f in m.Facets], np.int32); names.append(q)
for r in [o for o in doc.Objects if not o.InList]: walk(r, [])
np.savez_compressed(os.path.join(ROOT, "cad/full_parts.npz"), **out); json.dump(names, open(os.path.join(ROOT, "cad/full_names.json"), "w"), indent=0)
print("done", len(names), round(time.time() - t0))

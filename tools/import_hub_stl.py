# Replace the load-only hub's body in cad/bthub_loadonly.npz with Armored Turtle's printable STL
# (STLs/Modules/Hub/hub_load_only/hub_load_only.stl, GPL-3.0, ArmoredTurtle/BoxTurtle). The STEP release models that body
# without its filament channels; the STL has them. The STL is the same size but turned 180 degrees about Z (its inlets
# face +Y), so it is turned back about its bounding-box centre and then placed by its bounding box.
# Usage: python tools/import_hub_stl.py /path/to/hub_load_only.stl. AGPL-3.0 (see LICENSE).
import numpy as np, json, sys, os
D = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "")
b = open(sys.argv[1], "rb").read(); n = int.from_bytes(b[80:84], "little")
a = np.frombuffer(b[84:84 + n * 50], dtype=np.dtype([("n", "<f4", 3), ("v", "<f4", (3, 3)), ("x", "<u2")]))
T = a["v"].astype(np.float64).reshape(-1, 3)
V, inv = np.unique(np.round(T, 5), axis=0, return_inverse=True); F = inv.reshape(-1, 3).astype(np.int32)
z = dict(np.load(D + "cad/bthub_loadonly.npz")); N = json.load(open(D + "cad/bthub_loadonly.json"))
i = N.index("hub_load_only_1.1/SOLID035"); old = z["p%03d_V" % i]
c = (V.min(0) + V.max(0)) / 2; V = np.c_[2 * c[0] - V[:, 0], 2 * c[1] - V[:, 1], V[:, 2]]   # 180 deg about Z keeps the winding
off = old.min(0) - V.min(0); ext = (old.max(0) - old.min(0)) - (V.max(0) - V.min(0))
assert np.abs(ext).max() < 0.05, ext
z["p%03d_V" % i] = (V + off).astype(np.float32); z["p%03d_F" % i] = F
np.savez_compressed(D + "cad/bthub_loadonly.npz", **z); print("placed with offset", off.round(3), len(V), "vertices")

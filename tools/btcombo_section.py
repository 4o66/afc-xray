# Render a section of the BoxTurtle v1.1 hub/buffer combo (GPL-3.0, ArmoredTurtle/BoxTurtle) through its outlet filament
# axis (along Y, at X 150.1 Z 18.2), with the inferred PTFE. Same rasterizer as tools/section.py.
# Usage: MODE=static|base|full|slide SLIDE_DY=<mm> SIDE=a|b python tools/btcombo_section.py. AGPL-3.0 (see LICENSE).
import numpy as np, json, re, os
from PIL import Image
D = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "")
MODE = os.environ.get("MODE", "static"); SLIDE_DY = float(os.environ.get("SLIDE_DY", "0")); SIDE = os.environ.get("SIDE", "a")
OUT = D + "build/buffer_bt/"; os.makedirs(OUT, exist_ok=True)
AX, AZ = 150.1, 18.2
Y0 = 0.0; PXMM = 14; SS = 2; S = PXMM * SS; SUF = ""
def hexc(h): return np.array([int(h[i:i+2], 16) for i in (1, 3, 5)], float)
RULES = [
 (r"wires|Logo", None, None),
 (r"\[a\]_(buffer_trigger|hub/SOLID|bowden_retainer/SOLID|buffer_tag|cover)", "Printed, accent (red)", "#b8142c"),
 (r"load_sense/SOLID|mount|printed_washer", "Printed, main (black)", "#2d2e33"),
 (r"PTFE|bowden_4x2", "PTFE tube, inferred (cut face pink)", "#e9ece4"),
 (r"Plunger|Collet Body|Grab Ring|Seal Retainer", "ECAS04 collets", "#4b6fa8"),
 (r"D2F_Button|D2F_Hinge", "Switch levers", "#c3c9d1"),
 (r"D2F|Omron", "Switches", "#3a3d44"),
 (r"bearing", "Bearing (load sensor)", "#b4bac3"),
 (r"spring", "Springs", "#9aa1aa"),
 (r"barrel|bushing", "Barrels and bushings", "#a7adb5"),
 (r"Threaded Insert", "Brass heat-set inserts", "#c9a24a"),
 (r"SHCS|STS", "Screws", "#7c828b"),
]
def classify(n):
    for rx, lab, col in RULES:
        if re.search(rx, n): return lab, col
    return "Other", "#9a9a9a"
MOVING = r"buffer_trigger|bowden_retainer|bushing|M3x6 SHCS002|M3 Threaded Insert \(2\)001|M3x10 SHCS|PTFE_OUT_MOVE"
def group(n): return "slide" if re.search(MOVING, n) else None
def wanted(n):
    g = group(n)
    if MODE == "static" or MODE == "full": return True
    if MODE == "base": return g is None
    return g == MODE
d = np.load(D + "cad/btcombo.npz"); N = json.load(open(D + "cad/btcombo.json")); parts = []
for i, n in enumerate(N):
    V = d["p%03d_V" % i].astype(float)
    if group(n) == "slide": V = V + [0, SLIDE_DY, 0]
    parts.append((n, V, d["p%03d_F" % i]))
def lathe_y(poly, n=96):
    a = np.linspace(0, 2*np.pi, n, endpoint=False); c, sn = np.cos(a), np.sin(a); m = len(poly)
    V = np.concatenate([np.c_[AX + r*c, np.full(n, y), AZ + r*sn] for r, y in poly]); F = []
    for k in range(m):
        k2 = (k + 1) % m
        for i in range(n):
            j = (i + 1) % n; F += [[k*n+i, k2*n+i, k2*n+j], [k*n+i, k2*n+j, k*n+j]]
    F = np.array(F); T = V[F] - [AX, 0, AZ]; vol = np.einsum("ij,ij->i", T[:, 0], np.cross(T[:, 1], T[:, 2])).sum()
    return V, (F[:, ::-1] if vol < 0 else F)
# PTFE to the toolhead (4 x 2 mm, inferred): from the outlet collet out of the top of the drawing
PT_OUT_SEAT = float(os.environ.get("PT_OUT_SEAT", "277.0"))
V, F = lathe_y([(1.0, PT_OUT_SEAT), (1.97, PT_OUT_SEAT), (1.97, 320.0), (1.0, 320.0)]); parts.append(("PTFE_TOOLHEAD", V, F))
# view: SIDE a looks from +X (keep X <= AX), SIDE b from -X (keep X >= AX); screen right along the outlet path, up = Z
if SIDE == "a": parts = [(n, np.c_[V[:, 1], AX - V[:, 0], V[:, 2]], F) for n, V, F in parts]
else: parts = [(n, np.c_[-V[:, 1], V[:, 0] - AX, V[:, 2]], F) for n, V, F in parts]
CAPOVR = {"PTFE tube, inferred (cut face pink)": "#f4a3c4"}
src = open(D + "tools/section.py").read()
tail = src[src.index("tris, cols, pid = [], [], []"):].replace("CAPOVR = {", "_unused = {", 1)
bounds = "xmin, xmax = 192.0, 292.0; zmin, zmax = -10.0, 48.0" if SIDE == "a" else "xmin, xmax = -292.0, -192.0; zmin, zmax = -10.0, 48.0"
tail = re.sub(r"xmin, xmax = [^\n]*", bounds, tail, count=1).replace('OUT + "section.png"', f'OUT + "section_{SIDE}.png"')
exec(tail)

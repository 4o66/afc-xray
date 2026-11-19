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
HILITE = os.environ.get("HILITE", "")   # A: outlet block slides | B: hub slides (for the question page)
_HL = {"A": r"load_sense|Omron|bearing|ECAS Bowden Collet \(1\)/|bowden_retainer|buffer_trigger|bushing|M3x6 SHCS002|M3 Threaded Insert \(2\)001|M3x10 SHCS|PTFE_TOOLHEAD",
       "B": r"\[a\]_hub/SOLID|buffer_tag|ECAS Bowden Collet \(1\) \(1\)|D2F|M2x10 STS"}.get(HILITE)
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
    if n == "mount": return None, None   # the mounting bracket is left out
    if _HL and not re.search(r"wires|Logo", n) and re.search(_HL, n): return "Moves in this reading", "#2a7fd4"
    for rx, lab, col in RULES:
        if re.search(rx, n): return lab, col
    return "Other", "#9a9a9a"
# hub (left) is fixed in the frame, filament arrives from the lane extruders; the outlet block (right, to the toolhead)
# slides up to 10 mm (repo owner), carrying the load-sensor block, bearing, switch, outlet collet, trigger, and the two binding
# barrels screwed into it; the barrels slide in bushings in the hub, and their springs pull the block back. The PTFE wear
# tube and its retainer ring (bowden_retainer) and the screw clamping it stay with the hub (repo owner).
MOVING = r"load_sense|Omron|bearing|ECAS Bowden Collet \(1\)/|buffer_trigger|binding barrel|M3x6 SHCS(001)?$|M3x10 SHCS|PTFE_TOOLHEAD"
def group(n): return "slide" if re.search(MOVING, n) else None
BEAR = r"bearing|Omron D2HW-C201H( \(1\))?00[12]$"   # the hub sensor: bearing and the switch actuator above it, lifted together by the filament (MODE=bear)
def wanted(n):
    g = group(n)
    if MODE == "static": return True
    if MODE == "full": return not re.search(BEAR, n)   # the bearing is drawn whole on its own layer: keep it out of the masking reference
    if MODE == "bear": return bool(re.search(BEAR, n))
    if re.search(BEAR, n): return False
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
PT_OUT_SEAT = float(os.environ.get("PT_OUT_SEAT", "274.3"))   # shoulder past the outlet fitting (tools/hub_paths.py)
V, F = lathe_y([(1.0, PT_OUT_SEAT), (1.97, PT_OUT_SEAT), (1.97, 320.0), (1.0, 320.0)]); parts.append(("PTFE_TOOLHEAD", V, F))
# view: SIDE a looks from +X (keep X <= AX), SIDE b from -X (keep X >= AX); screen right along the outlet path, up = Z
if SIDE == "a": parts = [(n, np.c_[V[:, 1], AX - V[:, 0] + (100.0 if MODE == "bear" else 0.0), V[:, 2]], F) for n, V, F in parts]   # sensor layer uncut
else: parts = [(n, np.c_[-V[:, 1], V[:, 0] - AX, V[:, 2]], F) for n, V, F in parts]
CAPOVR = {"PTFE tube, inferred (cut face pink)": "#f4a3c4"}
src = open(D + "tools/section.py").read()
tail = src[src.index("tris, cols, pid = [], [], []"):].replace("CAPOVR = {", "_unused = {", 1)
bounds = "xmin, xmax = 192.0, 292.0; zmin, zmax = -10.0, 48.0" if SIDE == "a" else "xmin, xmax = -292.0, -192.0; zmin, zmax = -10.0, 48.0"
tail = re.sub(r"xmin, xmax = [^\n]*", bounds, tail, count=1).replace('OUT + "section.png"', f'OUT + "section_{SIDE}{HILITE}.png"')
exec(tail)

# Render a section of the TurtleNeck buffer (GPL-3.0, ArmoredTurtle/TurtleNeck) through its filament axis, seen from the
# lid side, with the inferred PTFE tubes. Same rasterizer as tools/section.py (its drawing stage is reused).
# Usage: MODE=static|base|full|slide SLIDE_DX=<mm> python tools/buffer_section.py. AGPL-3.0 (see LICENSE).
import numpy as np, json, re, os
from PIL import Image
D = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "")
MODE = os.environ.get("MODE", "static"); SLIDE_DX = float(os.environ.get("SLIDE_DX", "0"))
BUF = os.environ.get("BUF", "tn")   # tn: TurtleNeck | bt: BoxTurtle v1.1 hub/buffer combo
SIDE = os.environ.get("SIDE", "a")
OUT = D + f"build/buffer_{BUF}/"; os.makedirs(OUT, exist_ok=True)
AY, AZ = 115.9, -2.85          # filament axis (along X) in the TurtleNeck CAD
Y0 = 0.0; PXMM = 14; SS = 2; S = PXMM * SS; SUF = ""
def hexc(h): return np.array([int(h[i:i+2], 16) for i in (1, 3, 5)], float)
RULES = [
 (r"/Slide$", "Printed, accent (red)", "#b8142c"),
 (r"/(lid|Frame)$", "Printed, main (black)", "#2d2e33"),
 (r"PTFE", "PTFE tube, inferred (cut face pink)", "#e9ece4"),
 (r"Plunger|Collet Body|Grab Ring|Seal Retainer", "ECAS04 collet", "#4b6fa8"),
 (r"D2F_Button|D2F_Hinge", "Switch levers", "#c3c9d1"),
 (r"D2F", "Switches (Omron D2F-L)", "#3a3d44"),
 (r"Threaded Insert", "Brass heat-set inserts", "#c9a24a"),
 (r"SHCS|STS", "Screws", "#7c828b"),
]
def classify(n):
    for rx, lab, col in RULES:
        if re.search(rx, n): return lab, col
    return "Other", "#9a9a9a"
def group(n):
    if n.endswith("/Slide") or "ECAS Bowden Collet/" in n or n == "PTFE_IN": return "slide"
    return None
def wanted(n):
    g = group(n)
    if MODE == "static": return True
    if MODE == "base": return g is None
    if MODE == "full": return True
    return g == MODE
def lathe_x(poly, n=96):
    # revolve a closed (r, x) loop about the buffer's filament axis (along X)
    a = np.linspace(0, 2*np.pi, n, endpoint=False); c, sn = np.cos(a), np.sin(a); m = len(poly)
    V = np.concatenate([np.c_[np.full(n, x), AY + r*c, AZ + r*sn] for r, x in poly]); F = []
    for k in range(m):
        k2 = (k + 1) % m
        for i in range(n):
            j = (i + 1) % n; F += [[k*n+i, k2*n+i, k2*n+j], [k*n+i, k2*n+j, k*n+j]]
    F = np.array(F); T = V[F] - [0, AY, AZ]; vol = np.einsum("ij,ij->i", T[:, 0], np.cross(T[:, 1], T[:, 2])).sum()
    return V, (F[:, ::-1] if vol < 0 else F)
d = np.load(D + "cad/tn_parts.npz"); N = json.load(open(D + "cad/tn_names.json")); parts = []
for i, n in enumerate(N):
    V = d["p%03d_V" % i].astype(float)
    if group(n) == "slide": V = V + [SLIDE_DX, 0, 0]
    parts.append((n, V, d["p%03d_F" % i]))
# PTFE (4 x 2 mm). Filament runs right to left: in from the hub through the frame's collet (right), out to the toolhead
# through the slide's collet (left). Measured by ray casting along the axis: the slide has an 8.24 mm collet socket to
# X 21.5, a 4.3 mm counterbore to its shoulder at X 25.25, a 2.35 mm bore, a bevel from X 30 to 32, then the 4.58 mm bore
# the inlet tube telescopes in; the frame has its collet socket from X 75 and a 4.3 mm bore that opens into the slide.
# Seating (repo owner): the outlet tube is pushed in to the slide's shoulder; the inlet tube reaches into the slide to
# just short of its bevel with the neck fully closed. The hub-to-TurtleNeck tube is chamfered (BoxTurtle build guide).
PT_OUT_SEAT = 25.25; PT_IN_END = float(os.environ.get("PT_IN_END", "32.5"))
V, F = lathe_x([(1.0, -80.0), (1.97, -80.0), (1.97, PT_OUT_SEAT), (1.0, PT_OUT_SEAT)]); parts.append(("PTFE_IN", V + [SLIDE_DX, 0, 0], F))
V, F = lathe_x([(1.0, 140.0), (1.97, 140.0), (1.97, PT_IN_END), (1.5, PT_IN_END), (1.0, PT_IN_END + 0.5)]); parts.append(("PTFE_FIX", V, F))
# view from the lid side (+Z), cut at the axis plane: render frame x = X, depth = AZ - Z (keep >= 0), up = Y
parts = [(n, np.c_[V[:, 0], AZ - V[:, 2], V[:, 1]], F) for n, V, F in parts]
CAPOVR = {"PTFE tube, inferred (cut face pink)": "#f4a3c4"}
src = open(D + "tools/section.py").read()
tail = src[src.index("tris, cols, pid = [], [], []"):]
tail = tail.replace("CAPOVR = {", "_unused = {", 1)
tail = re.sub(r"xmin, xmax = [^\n]*", "xmin, xmax = -20.0, 87.0; zmin, zmax = 94.0, 132.0", tail, count=1)   # from just past each collet at full extension
exec(tail)

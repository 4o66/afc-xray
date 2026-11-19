# Render a BoxTurtle v1.1 hub (GPL-3.0, ArmoredTurtle/BoxTurtle) in section through its filament paths, from the side or
# from the top, with the same rasterizer as tools/section.py. Parts above the top view's cut plane (the buffer switches and
# trigger, the hub switch) are drawn uncut in their own layers, so the page can lay them over the section translucently.
# Usage: HUB=combo|loadonly VIEW=side|top MODE=static|base|full|slide|over|overslide python tools/hub_section.py
# Output: build/hub_<HUB>_<VIEW>/. AGPL-3.0 (see LICENSE).
import numpy as np, json, re, os
from PIL import Image
D = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "")
HUB = os.environ.get("HUB", "combo"); VIEW = os.environ.get("VIEW", "top"); MODE = os.environ.get("MODE", "static")
OUT = D + f"build/hub_{HUB}_{VIEW}/"; os.makedirs(OUT, exist_ok=True)
PATHS = json.load(open(D + "tools/hub_paths.json"))[HUB]
AX, AZ = 150.1, PATHS["az"]              # outlet filament axis, along +Y; the inlet channels lie in the plane Z = AZ
Y0 = 0.0; PXMM = 14; SS = 2; S = PXMM * SS; SUF = ""
def hexc(h): return np.array([int(h[i:i+2], 16) for i in (1, 3, 5)], float)
RULES = [
 (r"\[a\]_(buffer_trigger|hub/SOLID|bowden_retainer/SOLID|buffer_tag|cover)|hub_load_only_1\.1/SOLID", "Printed, accent", "#b8142c"),
 (r"load_sense/SOLID|SOLID", "Printed, primary", "#3a3d44"),
 (r"PTFE|bowden_4x2", "PTFE tube, inferred (cut face pink)", "#e9ece4"),
 (r"Plunger|Collet Body|Grab Ring|Seal Retainer", "ECAS04 collets", "#4b6fa8"),
 (r"D2F_Button|D2F_Hinge", "Switch levers", "#c3c9d1"),
 (r"D2F|Omron", "Switches", "#3a3d44"),
 (r"bearing", "Bearing (hub sensor)", "#b4bac3"),
 (r"spring", "Springs", "#9aa1aa"),
 (r"barrel|bushing", "Barrels and bushings", "#a7adb5"),
 (r"Threaded Insert", "Brass heat-set inserts", "#c9a24a"),
 (r"SHCS|STS", "Screws", "#7c828b"),
]
def classify(n):
    if re.search(r"wires|ZIP TIE|Logo", n): return None, None
    for rx, lab, col in RULES:
        if re.search(rx, n): return lab, col
    return "Other", "#9a9a9a"
# combo: the outlet block slides (see tools/btcombo_section.py); the load-only hub has no moving parts
MOVING = r"load_sense|Omron|bearing|ECAS Bowden Collet \(1\)/|buffer_trigger|binding barrel|M3x6 SHCS(001)?$|M3x10 SHCS|PTFE_TOOLHEAD" if HUB == "combo" else r"(?!x)x"
# above the top view's cut plane and worth showing: buffer switches and trigger (combo), the hub switch (both)
OVER = r"D2F|buffer_trigger|Omron"
def group(n): return "slide" if re.search(MOVING, n) else None
BEAR = r"bearing"   # the hub sensor's bearing: its own layer in the side view, lifted by the filament on the page (MODE=bear)
def wanted(n):
    g = group(n)
    if MODE in ("static", "full"): return True
    if MODE == "bear": return bool(re.search(BEAR, n))
    if VIEW == "side" and re.search(BEAR, n): return False
    if MODE == "base": return g is None
    if MODE == "slide": return g == "slide"
    if MODE == "over": return g is None and re.search(OVER, n)
    if MODE == "overslide": return g == "slide" and re.search(OVER, n)
src = "btcombo" if HUB == "combo" else "bthub_loadonly"
d = np.load(D + f"cad/{src}.npz"); N = json.load(open(D + f"cad/{src}.json")); parts = []
for i, n in enumerate(N): parts.append((n, d["p%03d_V" % i].astype(float), d["p%03d_F" % i]))
def lathe(poly, ax, n=96):
    """solid of revolution about the line through ax[0] along unit ax[1]; poly is (radius, distance along the axis)"""
    o, u = np.array(ax[0], float), np.array(ax[1], float); u /= np.linalg.norm(u)
    a1 = np.cross(u, [0, 0, 1.0]); a1 = a1 / np.linalg.norm(a1) if np.linalg.norm(a1) > 1e-6 else np.array([1.0, 0, 0]); a2 = np.cross(u, a1)
    t = np.linspace(0, 2*np.pi, n, endpoint=False); m = len(poly)
    V = np.concatenate([o + s * u + r * (np.cos(t)[:, None] * a1 + np.sin(t)[:, None] * a2) for r, s in poly]); F = []
    for k in range(m):
        k2 = (k + 1) % m
        for i in range(n):
            j = (i + 1) % n; F += [[k*n+i, k2*n+i, k2*n+j], [k*n+i, k2*n+j, k*n+j]]
    F = np.array(F); T = V[F] - o; vol = np.einsum("ij,ij->i", T[:, 0], np.cross(T[:, 1], T[:, 2])).sum()
    return V, (F[:, ::-1] if vol < 0 else F)
tube = [(1.0, 0.0), (1.97, 0.0), (1.97, 1.0), (1.0, 1.0)]
def add_tube(name, p0, p1):
    p0, p1 = np.array(p0, float), np.array(p1, float); L = np.linalg.norm(p1 - p0)
    V, F = lathe([(r, s * L) for r, s in tube], (p0, p1 - p0)); parts.append((name, V, F))
# inferred PTFE: each lane's tube runs in along its inlet axis to where the socket narrows; the outlet tube to the toolhead
add_tube("PTFE_TOOLHEAD" if HUB == "combo" else "PTFE_OUT", [AX, PATHS["out_ptfe"][0], AZ], [AX, PATHS["out_ptfe"][1], AZ])
for k, ln in PATHS["lanes"].items():
    s0, v = np.array(ln["seat"]), np.array(ln["dir"]); add_tube("PTFE_" + k, [*(s0 - v * 40), AZ], [*s0, AZ])
if MODE == "slide" or MODE == "overslide": pass
SLIDE_DY = float(os.environ.get("SLIDE_DY", "0"))
parts = [(n, V + ([0, SLIDE_DY, 0] if group(n) == "slide" else 0), F) for n, V, F in parts]
if VIEW == "side":   # from +X: screen right = +Y, up = Z, depth = AX - X (keep X <= AX)
    parts = [(n, np.c_[V[:, 1], AX - V[:, 0], V[:, 2]], F) for n, V, F in parts]; bounds = "xmin, xmax = 192.0, 292.0; zmin, zmax = -10.0, 48.0"
else:                # from +Z: screen right = +Y, up = -X, depth = AZ - Z (keep Z <= AZ); "over" layers are uncut
    lift = 100.0 if MODE.startswith("over") else 0.0
    parts = [(n, np.c_[V[:, 1], AZ + lift - V[:, 2], -V[:, 0]], F) for n, V, F in parts]; bounds = "xmin, xmax = 192.0, 292.0; zmin, zmax = -178.0, -122.0"
CAPOVR = {"PTFE tube, inferred (cut face pink)": "#f4a3c4"}
src_r = open(D + "tools/section.py").read()
tail = src_r[src_r.index("tris, cols, pid = [], [], []"):].replace("CAPOVR = {", "_unused = {", 1)
tail = re.sub(r"xmin, xmax = [^\n]*", bounds, tail, count=1).replace("if lab is None or", "if lab is None or not len(V) or")
exec(tail)

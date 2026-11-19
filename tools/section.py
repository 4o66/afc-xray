# Render the toolhead section and the animation layers.
# Usage: MODE=static|base|full|arm|slide|guid|dgear|igear python tools/section.py
# AGPL-3.0 (see LICENSE). Input meshes in cad/ are GPL-3.0 (see LICENSE-CAD).
# Front-on section of the toolhead through the filament axis (plane Y = 0, keep Y >= 0, look toward +Y).
# Cut faces are found as back faces seen through the cut (closed solids), drawn flat and hatched.
import numpy as np, json, sys, re, os
BASE = os.environ.get("BASE") == "1"
BODY = os.environ.get("BODY", "dual")     # dual | single | none (FilamATrix CW2) | f25_ecas | f25_collet (FilamATrix 2.5, no switch)
HOTEND = os.environ.get("HOTEND", "rapido_v2_uhf")   # a key of tools/hotends.json
BLADE = os.environ.get("BLADE", "ldo")    # ldo | olfa
F25 = BODY.startswith("f25")
# parts each body leaves out: the single-switch body keeps only the upper switch (tool_start); no-switch bodies have none;
# the FilamATrix 2.5 bodies also replace the CW2 main body, motor plate, guidler A and shuttle with Voron's CW2.5 parts
_NOSW = [r"FilamentSensor", r"M2x10 STS v"]
BODY_SKIP = {"dual": [], "single": [r"FilamentSensor/", r"M2x10 STS v1$", r"M2x10 STS v002$"], "none": _NOSW,
             "f25_ecas": _NOSW + [r"CW2_Printed/(Motor_Plate|Guilder_A|Shuttle)$"],
             "f25_collet": _NOSW + [r"CW2_Printed/(Motor_Plate|Guilder_A|Shuttle)$", r"ECAS Bowden Collet001/"]}[BODY]
MODE = os.environ.get("MODE", "static")   # static | base | full | arm | slide | spring  (animation layers)
def group(n):
    if n.endswith("Cutting_Arm v1 (1)"): return "arm"
    if re.search((r"Blade_Holder$|Full Blade \(LDO\)" if BLADE == "ldo" else r"Blade_Holder_Olaf$|Olfa KB4") + r"|Cutting_Arm v1 \(1\)001$|M2.5x16 SHCS", n): return "slide"
    if re.search(r"BMG_Drive_Gear_Assembly/Drive_Gear$|DIN 913", n): return "dgear"
    if re.search(r"Idler_Gear$|Needle_Bearings", n): return "igear"
    if n.endswith("LDO-36STH20"): return "pinion"
    if re.search(r"Guilder_[AB]$|BMG_Idler_Gear_Assembly/|M3x6 FHCS002$|M3 Threaded Insert00[38]$|M3x16 SHCS001$", n): return "guid"
    if "Compression Spring" in n: return "spring"
    if "5.5mmBall" in n: return "ball"
    if n == "FILAMENT": return "fil"
    return None
def wanted(n):
    g = group(n)
    if MODE == "static": return True
    if MODE == "base": return g is None
    if MODE == "full": return g not in ("ball", "fil", "spring")
    return g == MODE
from PIL import Image
D = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "")   # repo root
# base and full layers depend on body and hotend; the moving layers only on the body (and the blade, for the slide)
OUT = D + "build/" + (BODY + "__" + HOTEND if MODE in ("base", "full", "static") else BODY) + "/"; os.makedirs(OUT, exist_ok=True)
HOT = json.load(open(D + "tools/hotends.json"))[HOTEND]
SUF = "_olfa" if (MODE == "slide" and BLADE == "olfa") else ""
exec(open(D + "tools/binio.py").read())
d = np.load(D + "cad/full_parts.npz"); N = json.load(open(D + "cad/full_names.json"))
Y0 = float(sys.argv[1]) if len(sys.argv) > 1 else 0.0
PXMM = 14; SS = 2; S = PXMM * SS

def hexc(h): return np.array([int(h[i:i+2], 16) for i in (1, 3, 5)], float)
# (regex on part path, label, color)
RULES = [
 ((r"Olfa KB4|Blade_Holder_Olaf" if BLADE == "ldo" else r"Full Blade \(LDO\)|Blade_Holder$") + r"|Stealthburner_Body$", None, None),
 (r"uhf v0(17|29|24|26|30)$", None, None),                # alternates not used
 (r"Guilder_A|Guilder_B|Shuttle|PCB_Spacer|\[a\]_latch|Cutting_Arm|Blade_Holder", "Printed, accent (red)", "#b8142c"),
 (r"PTFE_LINER", "PTFE liner (2 mm ID)", "#e9ece4"),
 (r"BOWDEN", "Bowden tube (4 x 2 mm PTFE)", "#e9ece4"),
 (r"FILAMENT", "Filament", "#2fae4f"),
 (r"Main_Body_(Dual|One|No)|Motor_Plate|Guilder_B|SB_Rapido_UHF_V2_(Front|Rear)|Stealthburner_UHF|x_carriage_frame|COVER_MINE|Cable_Cover|CW25_COVER|Hotends/.*(SB_|Printhead|COMPOUND)", "Printed, main (black)", "#2d2e33"),
 (r"LDO-36STH021", "Motor (LDO-36STH20)", "#5b6068"),
 (r"LDO-36STH20$", "Motor pinion", "#c9ced6"),
 (r"Drive_Gear|Idler_Gear|50T_Drive|Shaft|Needle_Bear|Ballbearing|DIN 913", "Gears, bearings, shafts (steel)", "#b4bac3"),
 (r"Blade \(1\)|Full Blade", "Cutter blade", "#e6e9ee"),
 (r"Spring", "Springs", "#9aa1aa"),
 (r"Threaded|Heatset", "Brass heat-set inserts", "#c9a24a"),
 (r"SHCS|BHCS|FHCS|STS|Thumb Screw|Hext Nut|M3 x 5|DIN EN ISO|Washer", "Screws and nuts", "#7c828b"),
 (r"Magnet", "Magnets", "#8d96a3"),
 (r"5.5mmBall", "Switch balls (steel)", "#d6dbe2"),
 (r"Omron-D2F", "Filament switches (Omron D2F)", "#3a3d44"),
 (r"ECAS|Plunger|Collet|Grab Ring|Seal Retainer", "ECAS04 collet", "#4b6fa8"),
 (r"uhf v015$", "Nozzle (brass)", "#d4a944"),
 (r"uhf v038$", "UHF nozzle extension", "#eadfb4"),
 (r"uhf v011$", "Silicone sock", "#6f7781"),
 (r"uhf v018$|uhf v033$", "Heater block (copper)", "#b8693a"),
 (r"uhf v032$", "Heater core", "#e8e2d4"),
 (r"uhf v027$|uhf v017$", "Hotend heatsink", "#8f9aa6"),
 (r"uhf v012$|uhf v024$|uhf v029$", "Heat break / top coupler", "#c3c9d1"),
 (r"uhf v0(01|02|16|20|22|25|31)$|uhf v1$|uhf v00[4-9]$|uhf v010$|uhf v03[4-7]$|uhf v0(14|19|21|23|26|28|39|13)$", "Hotend wiring, thermistor, clamps", "#8a6f9e"),
 (r"VORON_PCB", "Toolhead PCB (Voron reference)", "#1f6b3a"),
 (r"VORON_CONN", "Toolhead PCB connectors", "#3c4a40"),
 (r"uhf v0", "Hotend (other)", "#b0b6bf"),
 (r"Hotends/.*(?i:nozzle)", "Nozzle (brass)", "#d4a944"),
 (r"Hotends/.*(?i:extender)", "UHF nozzle extension", "#eadfb4"),
 (r"Hotends/.*(?i:sock)", "Silicone sock", "#6f7781"),
 (r"Hotends/.*(?i:heatsink)", "Hotend heatsink", "#8f9aa6"),
 (r"Hotends/.*(?i:heatbr)", "Heat break / top coupler", "#c3c9d1"),
 (r"Hotends/.*(?i:ceramic)", "Heater core", "#e8e2d4"),
 (r"Hotends/.*(?i:block|heater_mount|heater assembly$)", "Heater block (copper)", "#b8693a"),
 (r"Hotends/.*(?i:wiring|thermistor|standoff|grub|clamp|WHS| GS)", "Hotend wiring, thermistor, clamps", "#8a6f9e"),
 (r"Hotends/", "Hotend (other)", "#b0b6bf"),
]
def classify(n):
    for rx, lab, col in RULES:
        if re.search(rx, n): return lab, col
    return "Other", "#9a9a9a"

parts = []
FIL_R = 0.875   # real 1.75 mm filament radius, for the pressed switch position
# Guidler swung open by the filament: pivot is the lower M3x20 (axis along Y at X -5.40, Z 73.16, centre of the 3.2 mm bore
# in guidler A). The idler gear's hob tips (r 3.65 about its centre, X -3.825 Z 86.31) reach X -0.175 in the CAD; rotate
# until they reach the filament surface at X -0.875 (no tooth bite drawn).
PIV = np.array([-5.40, 73.16]); CI = np.array([-3.825, 86.31]); TIP = 3.65
def _rot(th, x, z):
    dx, dz = x - PIV[0], z - PIV[1]; c, sn = np.cos(th), np.sin(th)
    return PIV[0] + dx * c - dz * sn, PIV[1] + dx * sn + dz * c
lo_, hi_ = 0.0, 0.2
for _ in range(60):
    mid = (lo_ + hi_) / 2
    if _rot(mid, *CI)[0] + TIP > -FIL_R: lo_ = mid
    else: hi_ = mid
THETA = (lo_ + hi_) / 2
print("guidler rotation %.3f deg" % np.degrees(THETA), "idler centre moves", np.round(np.array(_rot(THETA, *CI)) - CI, 3), flush=True)
def rot_guidler(V):
    x, z = _rot(THETA, V[:, 0], V[:, 2]); V = V.copy(); V[:, 0], V[:, 2] = x, z; return V
ROT_RX = re.compile(r"(?!x)x") if True else re.compile(r"Guilder_[AB]$|BMG_Idler_Gear_Assembly/|M3x6 FHCS002$|M3 Threaded Insert00[38]$|M3x16 SHCS001$")
for i, n in enumerate(N):
    if n.endswith("Main_Body_Dual_Switch") and BODY != "dual": continue
    if n.startswith("Hotends/"): continue                      # hotend parts come from cad/hotends.npz below
    if any(re.search(rx, n) for rx in BODY_SKIP): continue
    V, F = d["p%03d_V" % i].astype(float), d["p%03d_F" % i]
    if "5.5mmBall" in n:
        V = V + [FIL_R, 0, 0]           # ball pushed out by the filament (CAD shows it touching the axis)
    if ROT_RX.search(n):
        V = rot_guidler(V)
    if "Omron-D2F" in n:
        x0 = V[:, 0].min(); F = F[~(V[F][:, :, 0] < x0 + 0.45).any(1)]   # plunger pressed into the body: drop its 0.5 mm stub
    parts.append((n, V, F))
# single- and no-switch CW2 main bodies and FilamATrix's cable cover, meshed from the same FilamATrix STEP (tools/export_bodies.py)
_bd = np.load(D + "cad/bodies_cw2.npz"); _bn = json.load(open(D + "cad/bodies_cw2.json"))
for _i, _n in enumerate(_bn):
    use = (_n.endswith("Main_Body_One_Switch v1") and BODY == "single") or (_n.endswith("Main_Body_No_Switch") and BODY == "none") \
          or (_n.endswith("Cable_Cover_EBB v1") and not F25)
    if use: parts.append((_n, _bd["p%03d_V" % _i].astype(float), _bd["p%03d_F" % _i]))
# FilamATrix 2.5 (no switch) bodies, shared by the FilamATrix authors, aligned to Voron's CW2.5 bodies; with Voron's CW2.5
# motor plate, guidler A, latch shuttle and cable cover (GPL-3.0)
if F25:
    _fb = np.load(D + "cad/bodies_f25.npz"); _k = BODY.split("_")[1]
    parts.append(("CW25_Main_Body_No_Switch", _fb[_k + "_V"].astype(float), _fb[_k + "_F"]))
    _cp = np.load(D + "cad/cw25_parts.npz")
    for _k2, _nm in [("a_motor_plate", "CW25_Motor_Plate"), ("a_guidler_a", "CW25_Guilder_A"), ("a_shuttle", "CW25_Shuttle"), ("a_cover", "CW25_COVER")] + ([("a_collet", "CW25_Collet")] if BODY == "f25_collet" else []):
        parts.append((_nm, _cp[_k2 + "_V"].astype(float), _cp[_k2 + "_F"]))
# hotend, its printhead front and rear, and their hardware (tools/export_hotends.py). Parts that sit on top of a Rapido
# heatsink (the stock collar, coupler and their screws) are not used in a FilamATrix printhead and are left out.
_hd = np.load(D + "cad/hotends.npz"); _hn = json.load(open(D + "cad/hotends.json"))
for _i, _n in enumerate(_hn):
    if not any(_n.startswith(p) for p in HOT["prefix"]): continue
    _V = _hd["p%03d_V" % _i].astype(float)
    if _V.ndim != 2 or len(_V) == 0: continue                  # one Dragon HF printhead part is empty in the CAD
    printhead = re.search(r"SB_|Printhead|COMPOUND|Hardware", _n)
    if _n.startswith("Rapido") and not printhead and _V[:, 2].min() >= 51.9: continue
    parts.append(("Hotends/" + _n, _V, _hd["p%03d_F" % _i]))
# Toolhead board: Voron Design's Stealthburner toolhead PCB (GPL-3.0, VoronDesign/Voron-Hardware), the reference design the
# build's BTT SB2209 replaces. Placed on the CW2 PCB spacer by its two mounting holes (pure translation, holes match to 0.02 mm).
_vp = np.load(D + "cad/voron_pcb.npz"); _vn = json.load(open(D + "cad/voron_pcb_names.json"))
for _i, _n in enumerate(_vn):
    _V = _vp["p%03d_V" % _i].astype(float) + [18.77, -106.11, 34.48]
    parts.append(("VORON_PCB" if _n.endswith("SB-PCB011") else "VORON_CONN", _V, _vp["p%03d_F" % _i]))

def tube(ro, ri, z0, z1, n=96):
    a = np.linspace(0, 2*np.pi, n, endpoint=False); c, sn = np.cos(a), np.sin(a)
    V = np.concatenate([np.c_[ro*c, ro*sn, np.full(n, z0)], np.c_[ro*c, ro*sn, np.full(n, z1)],
                        np.c_[ri*c, ri*sn, np.full(n, z0)], np.c_[ri*c, ri*sn, np.full(n, z1)]])
    F = []
    for i in range(n):
        j = (i + 1) % n
        F += [[i, j, n+j], [i, n+j, n+i]]                       # outer wall, normal out
        F += [[2*n+i, 3*n+j, 2*n+j], [2*n+i, 3*n+i, 3*n+j]]     # inner wall, normal toward axis
        F += [[n+i, n+j, 3*n+j], [n+i, 3*n+j, 3*n+i]]           # top ring, normal up
        F += [[i, 2*n+j, j], [i, 2*n+i, 2*n+j]]                 # bottom ring, normal down
    return V, np.array(F)
# PTFE liner: FilamATrix Rapido jig length 18 mm, seated on the heatsink bore step (Z 39.5) up to the lower blade insert (Z 57.5)
def lathe(poly, n=96):
    # revolve a closed (r, z) loop about the Z axis; fix winding so normals point out (positive volume)
    a = np.linspace(0, 2*np.pi, n, endpoint=False); c, sn = np.cos(a), np.sin(a); m = len(poly)
    V = np.concatenate([np.c_[r*c, r*sn, np.full(n, z)] for r, z in poly]); F = []
    for k in range(m):
        k2 = (k + 1) % m
        for i in range(n):
            j = (i + 1) % n; F += [[k*n+i, k2*n+i, k2*n+j], [k*n+i, k2*n+j, k*n+j]]
    F = np.array(F); T = V[F]; vol = np.einsum("ij,ij->i", T[:, 0], np.cross(T[:, 1], T[:, 2])).sum()
    return V, (F[:, ::-1] if vol < 0 else F)
# PTFE liner: 2 mm ID, 18 mm (FilamATrix Rapido jig), seated on the heatsink bore step at Z 39.5, top at the lower
# blade insert (Z 57.5). OD drawn at the heatsink bore as modeled (3.74 mm). Blade end chamfered 45 deg to 3 mm.
RO, RI, Z0, Z1, CH = HOT["ro"], 1.0, HOT["seat"], 57.5, 0.5
Vt, Ft = lathe([(RI, Z0), (RO, Z0), (RO, Z1), (RI + CH, Z1), (RI, Z1 - CH)]); parts.append(("PTFE_LINER", Vt, Ft))
# Bowden stub (BoxTurtle 4 x 2 mm PTFE), fully inserted: bottoms on the step at the foot of the body's 4.2 mm bore (Z 105.8),
# up through the ECAS04 collet and out the top. OD drawn 3.94 mm to sit inside the collet plunger bore as modeled.
Vb, Fb = lathe([(1.0, 105.8), (1.97, 105.8), (1.97, 146.0), (1.0, 146.0)]); parts.append(("BOWDEN", Vb, Fb))
def rod(prof, n=64):
    # solid of revolution from (z, r) pairs listed top to bottom; closed with end discs
    a = np.linspace(0, 2*np.pi, n, endpoint=False); c, sn = np.cos(a), np.sin(a)
    V = [np.c_[r*c, r*sn, np.full(n, z)] for z, r in prof]; V = np.concatenate(V + [[[0, 0, prof[0][0]]], [[0, 0, prof[-1][0]]]])
    F = []; m = len(prof); top, bot = m*n, m*n + 1
    for k in range(m - 1):
        for i in range(n):
            j = (i + 1) % n; a0, a1, b0, b1 = k*n+i, k*n+j, (k+1)*n+i, (k+1)*n+j
            F += [[a0, b0, b1], [a0, b1, a1]]
    for i in range(n):
        j = (i + 1) % n; F += [[top, i, j], [bot, (m-1)*n+j, (m-1)*n+i]]
    return V, np.array(F)
# filament: drawn at 1.6 mm so it stays inside the 1.64 mm melt-zone bore as modeled; ends in the nozzle cone
if MODE == "static":
    Vf, Ff = rod([(147.0, 0.8), (-7.0, 0.8), (-8.0, 0.32), (-8.5, 0.14)]); parts.append(("FILAMENT", Vf, Ff))
# Hotend mounting screws (roughed in): 4 x M2.5x6 SHCS, heads on the printhead counterbore floor (Z 58.0), threads into the
# heatsink's 3.5 mm-deep holes (to Z 50.6). Hole centres from the heatsink and printhead geometry.
for hx, hy in ([(6.96, 3.94), (-3.94, 6.96), (3.95, -6.96), (-6.95, -3.95)] if HOT["screws"] else []):
    Vs, Fs = lathe([(0, 59.2), (1.0, 59.2), (1.0, 60.5), (2.25, 60.5), (2.25, 58.0), (1.25, 58.0), (1.25, 52.0), (0, 52.0)], 48)
    parts.append(("M2.5x6 SHCS hotend", Vs + [hx, hy, 0], Fs))

tris, cols, pid = [], [], []
legend = {}
CAPM = {}
CAPOVR = {'PTFE liner (2 mm ID)': '#f4a3c4', 'Bowden tube (4 x 2 mm PTFE)': '#f4a3c4'}
for k, (n, V, F) in enumerate(parts):
    lab, col = classify(n)
    if lab is None or V[:, 1].max() < Y0 or not wanted(n): continue
    T = V[F]; legend.setdefault(lab, col)
    CAPM[k] = hexc(CAPOVR[lab]) if lab in CAPOVR else np.minimum(hexc(col) * 0.9 + 45, 255)
    tris.append(T); cols.append(np.repeat(hexc(col)[None], len(T), 0)); pid.append(np.full(len(T), k))
T = np.concatenate(tris); C = np.concatenate(cols); P = np.concatenate(pid)
# normals before clipping (orientation of the original face)
Nrm = np.cross(T[:, 1] - T[:, 0], T[:, 2] - T[:, 0]); ln = np.linalg.norm(Nrm, axis=1); ok = ln > 1e-14
T, C, P, Nrm = T[ok], C[ok], P[ok], Nrm[ok] / ln[ok][:, None]
ins = T[:, :, 1] >= Y0; nin = ins.sum(1)
keepT = [T[nin == 3]]; keepC = [C[nin == 3]]; keepP = [P[nin == 3]]; keepN = [Nrm[nin == 3]]
for idx in np.where((nin > 0) & (nin < 3))[0]:
    tri = T[idx]; poly = []
    for a in range(3):
        p, q = tri[a], tri[(a + 1) % 3]; pin, qin = p[1] >= Y0, q[1] >= Y0
        if pin: poly.append(p)
        if pin != qin:
            t = (Y0 - p[1]) / (q[1] - p[1]); poly.append(p + t * (q - p))
    for j in range(1, len(poly) - 1):
        keepT.append(np.array([[poly[0], poly[j], poly[j + 1]]])); keepC.append(C[idx][None]); keepP.append(P[idx][None]); keepN.append(Nrm[idx][None])
T = np.concatenate(keepT); C = np.concatenate(keepC); P = np.concatenate(keepP); Nrm = np.concatenate(keepN)
cap = Nrm[:, 1] > 0          # back face seen from -Y: inside of a cut solid
print("triangles", len(T), "cap", cap.sum(), flush=True)

xmin, xmax = -42.0, 40.0; zmin, zmax = -12.0, 146.0
W = int((xmax - xmin) * S); H = int((zmax - zmin) * S)
zb = np.full((H, W), np.inf); img = np.zeros((H, W, 3)) + 255; pb = np.full((H, W), -1); cb = np.zeros((H, W), bool)
L = np.array([-0.45, -0.75, 0.5]); L /= np.linalg.norm(L)
shade = 0.38 + 0.62 * np.abs(Nrm @ L)
SX = (T[:, :, 0] - xmin) * S; SY = (zmax - T[:, :, 2]) * S; SZ = T[:, :, 1]
for k in range(len(T)):
    px, py, pz = SX[k], SY[k], SZ[k]
    x0 = max(int(px.min()), 0); x1 = min(int(px.max()) + 1, W - 1); y0 = max(int(py.min()), 0); y1 = min(int(py.max()) + 1, H - 1)
    if x1 < x0 or y1 < y0: continue
    den = (py[1] - py[2]) * (px[0] - px[2]) + (px[2] - px[1]) * (py[0] - py[2])
    if abs(den) < 1e-12: continue
    xs = np.arange(x0, x1 + 1) + 0.5; ys = np.arange(y0, y1 + 1)[:, None] + 0.5
    w1 = ((py[1] - py[2]) * (xs - px[2]) + (px[2] - px[1]) * (ys - py[2])) / den
    w2 = ((py[2] - py[0]) * (xs - px[2]) + (px[0] - px[2]) * (ys - py[2])) / den
    w3 = 1 - w1 - w2; m = (w1 >= -1e-6) & (w2 >= -1e-6) & (w3 >= -1e-6)
    if not m.any(): continue
    z = w1 * pz[0] + w2 * pz[1] + w3 * pz[2]
    sub = zb[y0:y1 + 1, x0:x1 + 1]; m &= z < sub
    if not m.any(): continue
    sub[m] = z[m]
    if cap[k]:
        img[y0:y1 + 1, x0:x1 + 1][m] = CAPM[P[k]]
    else:
        img[y0:y1 + 1, x0:x1 + 1][m] = C[k] * shade[k]
    pb[y0:y1 + 1, x0:x1 + 1][m] = P[k]; cb[y0:y1 + 1, x0:x1 + 1][m] = cap[k]
# hatching on cut faces
yy, xx = np.mgrid[0:H, 0:W]
hatch = cb & (((xx + yy) // SS) % 9 == 0)
img[hatch] *= 0.55
# outlines: part boundaries and depth steps
edge = np.zeros((H, W), bool)
for dy, dx in [(0, 1), (1, 0)]:
    a = pb[:H - dy, :W - dx]; b = pb[dy:, dx:]
    za = zb[:H - dy, :W - dx]; zb2 = zb[dy:, dx:]
    e = (a != b) | (np.abs(np.nan_to_num(za - zb2, posinf=99, neginf=99)) > 1.2) | (cb[:H - dy, :W - dx] != cb[dy:, dx:])
    edge[:H - dy, :W - dx] |= e
img[edge] = img[edge] * 0.25
if MODE == "static":
    im = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).resize((W // SS, H // SS), Image.LANCZOS); im.save(OUT + "section.png")
else:
    cov = (pb >= 0).astype(float)
    def down(a): return a.reshape(H // SS, SS, W // SS, SS, *a.shape[2:]).mean((1, 3))
    a = down(cov); rgb = down(img * cov[..., None]) / np.maximum(a, 1e-6)[..., None]
    if MODE == "base": a = np.ones_like(a); rgb = down(img)
    rgba = np.dstack([np.clip(rgb, 0, 255), a * 255]).astype(np.uint8)
    Image.fromarray(rgba, "RGBA").save(OUT + f"layer_{MODE}{SUF}.png")
    zd = zb.reshape(H // SS, SS, W // SS, SS).min((1, 3)); np.save(OUT + f"depth_{MODE}{SUF}.npy", zd.astype(np.float32))
    im = None
json.dump({"legend": legend, "px_per_mm": PXMM, "xmin": xmin, "zmax": zmax, "W": W // SS, "H": H // SS}, open(OUT + "section_meta.json", "w"), indent=1)
print("saved", MODE)

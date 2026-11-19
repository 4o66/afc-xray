# Render a BoxTurtle lane (GPL-3.0, ArmoredTurtle/BoxTurtle) in section: the respooler through its filament path (VIEW=spool)
# and the extruder through its filament line (VIEW=ext), with the same rasterizer as tools/section.py. The filament path, the
# gear and bearing positions and the inferred PTFE tubes are measured from the CAD here; MODE=geom writes them to
# build/lane_<VER>_<VIEW>/geom.json without rendering.
# VER: v11 (Lane2, Apex extruder) | v11bmg (Smol-D2HW with the BMG gear kit on Lane2) | v11proto (Smol V2 with the
#      ProtoXtruder gearpack on Lane2) | v10 (v1.0 Lane002, Smol-D2HW with the BMG gear kit)
# MODE: static | base | full | dgear | igear | trig | bear | over | overmove | geom, and in the ext view one pair per turning
#       drive-train group (SPIN below): spin_<name> (cut, as the base shows it) and spin_<name>_see (as the over layer shows it)
# Usage: VER=v11 VIEW=ext MODE=base python tools/lane_section.py. AGPL-3.0 (see LICENSE).
import numpy as np, json, re, os
from PIL import Image
D = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "")
VER = os.environ.get("VER", "v11"); VIEW = os.environ.get("VIEW", "ext"); MODE = os.environ.get("MODE", "static")
OUT = D + f"build/lane_{VER}_{VIEW}/"; os.makedirs(OUT, exist_ok=True)
Y0 = 0.0; PXMM = 14; SS = 2; S = PXMM * SS; SUF = ""
FIL_R = 0.875                        # 1.75 mm filament
def hexc(h): return np.array([int(h[i:i+2], 16) for i in (1, 3, 5)], float)
RULES = [
 (r"wires|Wire|ZIP TIE|Logo|rgbw_led_pcb|Desiccant|lid blank|support00", None, None),
 (r"PTFE_INF", "PTFE tube, inferred (cut face pink)", "#e9ece4"),
 (r"4x3 Bowden|Bowden Tubes", "PTFE tube (cut face pink)", "#e9ece4"),
 (r"Plunger|Collet Body|Grab Ring|Seal Retainer", "ECAS04 collets", "#4b6fa8"),
 (r"D2F_Button|D2F_Hinge", "Switch levers", "#c3c9d1"),
 (r"D2F|Omron", "Switches", "#3a3d44"),
 (r"MR63|MR148|MR85|MR825|Ballbearing|bearing|Bushing|Gearpack0(01|05|08|09|11|12)$", "Bearings", "#b4bac3"),
 (r"T10 SpurGear", "Gears, shafts (metal)", "#a7adb5"),
 (r"N20 DC MOTOR|LDO Stepper", "Motors (stepper, N20)", "#5d6470"),
 (r"Tensioner.*003$", "Springs", "#9aa1aa"),
 (r"Threaded Insert", "Brass heat-set inserts", "#c9a24a"),
 (r"SHCS|BHCS|FHCS|STS|Grub|Washer|idler001/screw|Tensioner", "Screws", "#7c828b"),
 (r"Magnet", "Magnets", "#8a8f96"),
 (r"Drive_Gear|Idler_Orbiter|Idler_Shaft|BMG|SOLID027|T10|Spur Gear 50t|Gearpack|Shaft|shaft|20x3mm Pin", "Gears, shafts (metal)", "#a7adb5"),
 (r"Tire", "Tires", "#4a4d55"),
 (r"\[c\]_", "Printed, clear", "#cfd6dc"),
 (r"\[a\]_|[Gg]uidler|[Gg]uilder|Roller0|spooler_cover|wheel_hub|wheel_endcap|Feed-Trigger_Retainer.*SOLID|Lightbox|LED_Retainer|microswitch|bearing_spacer", "Printed, accent", "#b8142c"),   # accent per the [a]_ STL names
 (r".", "Printed, primary", "#3a3d44"),
]
def classify(n):
    for rx, lab, col in RULES:
        if re.search(rx, n): return lab, col
    return "Other", "#9a9a9a"
CAPOVR = {"PTFE tube, inferred (cut face pink)": "#f4a3c4", "PTFE tube (cut face pink)": "#f4a3c4"}

# ---------------------------------------------------------------- parts
def load(src, tf=None, flip=False, prefix=""):
    d = np.load(D + f"cad/{src}.npz"); N = json.load(open(D + f"cad/{src}.json")); out = []
    for i, n in enumerate(N):
        V = d["p%03d_V" % i].astype(float); F = d["p%03d_F" % i]
        if V.ndim != 2 or not len(V): continue
        if tf is not None: V = tf(V)
        out.append((prefix + n, V, F[:, ::-1] if flip else F))
    return out
FAM = {"v11": "apex", "v11bmg": "bmg", "v11proto": "proto", "v10": "bmg"}[VER]
if VER == "v10":
    parts = load("lane_v10")
else:
    parts = load("lane_v11")
    if VER != "v11":
        parts = [p for p in parts if not p[0].startswith("Apex_A")]
        if VER == "v11bmg":    # lane-4 slot, mirrored onto Lane2 (mirroring flips the winding)
            parts += load("alt_smol_d2hw_bmg_v11", lambda V: V * [-1, 1, 1] + [390, 0, 0], flip=True, prefix="ALT/")
        else:                  # lane-1 slot, moved onto Lane2
            parts += load("alt_smol_v2_protoxtruder_v11", lambda V: V + [90, 0, 0], prefix="ALT/")
def P_(key, all_=False):
    m = [p for p in parts if re.search(key, p[0])]
    assert m, key
    return m if all_ else m[0]
def bbc(V): return (V.min(0) + V.max(0)) / 2
# the 50 mm feeder tube is inserted down to the shoulder of the prep trigger's bore, Z 101.2 (repo owner); the CAD has it
# 4.2 mm short of it. The feeder collar on its top end moves down with it, so the tube stays seated against the collar's
# shoulder (its socket is 4.8 mm deep, Z 150.4 to 155.2 in the CAD; issue #63). Nothing sits under the collar.
_dz = {}
for n, V, F in parts:
    if re.search(r"4x3 Bowden 50mm00[12]$", n): _dz[n.rsplit("/", 1)[0]] = 101.2 - V[:, 2].min()
def _seat(n, V):
    if re.search(r"4x3 Bowden 50mm00[12]$|feeder_x00[56]$", n):
        dz = [d for k, d in _dz.items() if n.startswith(k.rsplit("/", 1)[0])]
        assert len(dz) == 1, (n, _dz); return V + [0, 0, dz[0]]
    return V
parts = [(n, _seat(n, V), F) for n, V, F in parts]

# ---------------------------------------------------------------- measurements
def slice2d(V, F, O, U, Vv, N):
    T = V[F]; d = (T - O) @ N; m = (d.min(1) < 0) & (d.max(1) > 0); pts = []
    for tri, dd in zip(T[m], d[m]):
        for a, b in ((0, 1), (1, 2), (2, 0)):
            if dd[a] * dd[b] < 0: t = dd[a] / (dd[a] - dd[b]); p = tri[a] + (tri[b] - tri[a]) * t; pts.append(((p - O) @ U, (p - O) @ Vv))
    return np.array(pts)
def circfit(P):
    A = np.c_[2 * P, np.ones(len(P))]; b = (P ** 2).sum(1); x = np.linalg.lstsq(A, b, rcond=None)[0]; c = x[:2]; return c, np.sqrt(x[2] + c @ c)
def gear_cut(V, F, O, U, Vv, N):
    """centre (u, v) and outer radius of a round part where the section plane cuts it"""
    P = slice2d(V, F, O + N * 1e-3, U, Vv, N); c, _ = circfit(P)   # nudged off the plane: hob grooves have vertices on it
    for _ in range(4):
        r = np.linalg.norm(P - c, axis=1); c, _ = circfit(P[r > np.percentile(r, 60)])
    r = np.linalg.norm(P - c, axis=1); return c, float(np.percentile(r, 97))
def rays_min(tris, o, dirs):
    """nearest hit distance from o along each of dirs (Moller-Trumbore), inf when nothing is hit"""
    v0, e1, e2 = tris[:, 0], tris[:, 1] - tris[:, 0], tris[:, 2] - tris[:, 0]; out = []
    for d in dirs:
        p = np.cross(d, e2); det = np.einsum("ij,ij->i", e1, p); ok = np.abs(det) > 1e-12; inv = np.where(ok, 1 / np.where(ok, det, 1), 0)
        t0 = o - v0; u = np.einsum("ij,ij->i", t0, p) * inv; q = np.cross(t0, e1); v = (q @ d) * inv; t = np.einsum("ij,ij->i", e2, q) * inv
        h = ok & (u >= 0) & (v >= 0) & (u + v <= 1) & (t > 1e-6); out.append(t[h].min() if h.any() else np.inf)
    return np.array(out)
def printed_tris(p0, p1, rad=6.0):
    """triangles of the printed parts near the segment p0-p1"""
    acc = []; ax = p1 - p0; L = np.linalg.norm(ax); ax = ax / L
    for n, V, F in parts:
        lab, _ = classify(n)
        if not lab or not lab.startswith("Printed"): continue
        lo, hi = V.min(0), V.max(0)
        if (lo > np.maximum(p0, p1) + rad).any() or (hi < np.minimum(p0, p1) - rad).any(): continue
        T = V[F]; c = T.mean(1) - p0; s = c @ ax; d = np.linalg.norm(c - s[:, None] * ax, axis=1)
        acc.append(T[(s > -rad) & (s < L + rad) & (d < rad)])
    return np.concatenate(acc) if acc else np.zeros((0, 3, 3))
def shoulder(p_start, ax, maxd=25.0, r_tube=1.9):
    """walk from p_start along ax inside a socket's bore until the printed bore narrows below the tube (the shoulder that
    stops a pushed-in tube); returns the shoulder point and the bore radius just before it"""
    ax = ax / np.linalg.norm(ax); T = printed_tris(p_start, p_start + ax * maxd)
    e1 = np.cross(ax, [0, 0, 1.0]); e1 = e1 if np.linalg.norm(e1) > 1e-6 else np.cross(ax, [1.0, 0, 0]); e1 /= np.linalg.norm(e1); e2 = np.cross(ax, e1)
    dirs = [np.cos(t) * e1 + np.sin(t) * e2 for t in np.linspace(0, 2 * np.pi, 16, endpoint=False)]; last = None
    for s in np.arange(0.0, maxd, 0.05):
        r = np.median(rays_min(T, p_start + ax * s, dirs))
        if r < r_tube: return p_start + ax * s, last
        last = float(r) if np.isfinite(r) else last
    raise RuntimeError("no shoulder found")
def collet(key, ax):
    """ECAS04 collet: plunger head (outer end on the axis) and seal-retainer inner end, for a collet whose axis points
    along ax from the plunger head inward; the axis passes through the collet's centre line"""
    pl = P_(re.escape(key) + r"Plunger")[1]; sr = P_(re.escape(key) + r"Seal Retainer")[1]
    return pl, sr
def sweep(pts, ro, ri, ch0=0.0, ch1=0.0, n=48):
    """closed tube mesh along a polyline (parallel-transport frames); ch0/ch1: 0.5 mm inner chamfers at the ends"""
    pts = np.asarray(pts, float); seg = np.diff(pts, axis=0); L = np.r_[0, np.cumsum(np.linalg.norm(seg, axis=1))]
    T = np.gradient(pts, axis=0); T /= np.linalg.norm(T, axis=1)[:, None]
    a = np.cross(T[0], [0, 0, 1.0]); a = a if np.linalg.norm(a) > 1e-6 else np.cross(T[0], [1.0, 0, 0]); a /= np.linalg.norm(a); fr = []
    for t in T:
        a = a - (a @ t) * t; a /= np.linalg.norm(a); fr.append((a, np.cross(t, a)))
    th = np.linspace(0, 2 * np.pi, n, endpoint=False); cs, sn = np.cos(th), np.sin(th)
    def rin(l):
        r = ri
        if ch0 and l < ch0: r = ri + (ch0 - l)
        if ch1 and l > L[-1] - ch1: r = max(r, ri + (l - (L[-1] - ch1)))
        return r
    # extra stations so the chamfers are resolved
    extra = [l for l in (ch0, L[-1] - ch1) if 0 < l < L[-1]]
    if extra:
        newL = np.unique(np.r_[L, extra]); pts = np.array([np.interp(newL, L, pts[:, k]) for k in range(3)]).T
        T = np.array([np.interp(newL, L, T[:, k]) for k in range(3)]).T; T /= np.linalg.norm(T, axis=1)[:, None]
        fr2 = []
        a = fr[0][0]
        for t in T:
            a = a - (a @ t) * t; a /= np.linalg.norm(a); fr2.append((a, np.cross(t, a)))
        fr, L = fr2, newL
    m = len(pts); Vo, Vi = [], []
    for k in range(m):
        e1, e2 = fr[k]; ring = cs[:, None] * e1 + sn[:, None] * e2
        Vo.append(pts[k] + ro * ring); Vi.append(pts[k] + rin(L[k]) * ring)
    V = np.concatenate(Vo + Vi); F = []; off = m * n
    for k in range(m - 1):
        for i in range(n):
            j = (i + 1) % n; a0, a1, b0, b1 = k * n + i, k * n + j, (k + 1) * n + i, (k + 1) * n + j
            F += [[a0, b0, b1], [a0, b1, a1]]                                  # outer
            F += [[off + a0, off + b1, off + b0], [off + a0, off + a1, off + b1]]  # inner
    for i in range(n):
        j = (i + 1) % n; e = (m - 1) * n
        F += [[i, off + j, off + i], [i, j, off + j]]                          # start annulus
        F += [[e + i, off + e + i, off + e + j], [e + i, off + e + j, e + j]]  # end annulus
    F = np.array(F); Tt = V[F] - V.mean(0); vol = np.einsum("ij,ij->i", Tt[:, 0], np.cross(Tt[:, 1], Tt[:, 2])).sum()
    return V, (F[:, ::-1] if vol < 0 else F)
def bezier(p0, p1, p2, p3, n=200):
    t = np.linspace(0, 1, n)[:, None]
    return (1 - t) ** 3 * p0 + 3 * (1 - t) ** 2 * t * p1 + 3 * (1 - t) * t ** 2 * p2 + t ** 3 * p3
def plen(P): return float(np.linalg.norm(np.diff(P, axis=0), axis=1).sum())

G = {"ver": VER, "family": FAM}
Z = np.array([0, 0, 1.0])
# --- extruder: filament line along f, gear axes along a (normal to the section plane)
if VER == "v10":
    a = np.array([1.0, 0, 0]); f = np.array([0, -1.0, 0])       # flows -Y; viewer at -X
    inl, outl = "ECAS Bowden Collet (1)002/", "ECAS Bowden Collet004/"
else:
    a = np.array([0.98481, -0.17365, 0]); f = np.array([0.17365, 0.98481, 0])   # flows +Y
    inl, outl = {"apex": ("ECAS Bowden Collet (1) (2)/", "ECAS Bowden Collet (1) (1) (1)/"),
                 "bmg": ("ECAS Bowden Collet (1) (3)/", "ECAS Bowden Collet (2)/"),
                 "proto": ("ECAS Bowden Collet (1) (4)/", "ECAS Bowden Collet (1) (1) (2)/")}[FAM]
# the line: Z and lateral offset from the two extruder collets (mean of their centres: the bounding-box bias of a tilted
# collet cancels between the inlet and the outlet, which face each other)
cs_ = [bbc(np.concatenate([P_(re.escape(k) + r"(Plunger|Collet Body|Seal Retainer)", True)[j][1] for j in range(3)])) for k in (inl, outl)]
cm = (cs_[0] + cs_[1]) / 2; zl = float(cm[2]); ac = float(cm @ a)
def on_line(t): return ac * a + t * f + np.array([0, 0, zl]) - ((ac * a + t * f) @ Z) * Z
def tpar(p): return float(p @ f)
pl_in, sr_in = collet(inl, f); pl_out, sr_out = collet(outl, f)
t_in_head = float(min(pl_in @ f)); t_in_ret = float(max(sr_in @ f))
t_out_ret = float(min(sr_out @ f)); t_out_head = float(max(pl_out @ f))
E_IN, E_INR, E_OUTR, E_OUT = on_line(t_in_head), on_line(t_in_ret), on_line(t_out_ret), on_line(t_out_head)
SH_IN, r_in_bore = shoulder(E_INR, f)              # inlet: tube pushed in past the collet to the shoulder
SH_OUT, r_out_bore = shoulder(E_OUTR, -f)           # outlet: tube pushed in from the other side
NV = np.cross(Z, f)                                  # section normal = V x U (viewer looks along it)
OE = on_line(t_in_head)                              # extruder view origin: inlet plunger head on the line
# gears, cut by the section plane
GR = {"apex": (r"LDO_Orbiter_Gears_BMG/Drive_Gear_Orbiter$", r"Idler_Orbiter_Gear"),
      "bmg": (r"Spur Gear 50t00\d/Spur Gear 50t00[17]$", r"BMG_Idler"),
      "proto": (r"ProtoXtruder Gearpack003$", r"ProtoXtruder Gearpack007$")}[FAM]
gears = {}
for g, rx in zip(("dgear", "igear"), GR):
    _, V, F = P_(rx); c2, r = gear_cut(V, F, OE, f, Z, NV); c3 = OE + c2[0] * f + c2[1] * Z
    gears[g] = {"c": c3.tolist(), "r_cut": round(r, 3), "uv": c2.tolist()}
nip_t = float(np.mean([gears["dgear"]["uv"][0], gears["igear"]["uv"][0]])) + tpar(OE)
NIP = on_line(nip_t)
# gear train, motor to drive gear, as (driving, driven) tooth counts per stage, counted from the CAD's tooth profiles: Apex and
# Smol-D2HW: T10 pinion to the BMG 50 T gear; ProtoXtruder gearpack: T10 to its 44 T gear, whose 17 T pinion turns the 37 T
# drive gear (all module 0.5)
TRAIN = {"apex": [(10, 50)], "bmg": [(10, 50)], "proto": [(10, 44), (17, 37)]}[FAM]
# load-sensor bearing: contact where it rests on 1.75 mm filament; it lifts along the line from the filament axis to its centre
_, Vb, Fb = P_(r"MR63ZZ bearing")
cb = bbc(Vb); tb = tpar(cb); foot = on_line(tb); off = cb - foot; dist = np.linalg.norm(off); ldir = off / dist
LIFT = 3.0 + FIL_R - dist                            # MR63: 6 mm OD
LOAD = foot
G["ext"] = {"a": a.tolist(), "f": f.tolist(), "z_line": zl, "inlet_head": E_IN.tolist(), "inlet_retainer": E_INR.tolist(),
            "inlet_shoulder": SH_IN.tolist(), "inlet_bore_r": r_in_bore, "outlet_retainer": E_OUTR.tolist(), "outlet_shoulder": SH_OUT.tolist(),
            "outlet_bore_r": r_out_bore, "outlet_head": E_OUT.tolist(), "gears": gears, "nip": NIP.tolist(),
            "bearing": {"c": cb.tolist(), "contact": LOAD.tolist(), "dir": ldir.tolist(), "lift_mm": float(LIFT), "axis_dist": float(dist)}}
# --- respooler: vertical filament from the feeder through the prep rollers into the spooler collet
if VER == "v10":
    feeder, bow, trig_rx = r"feeder_x006", r"4x3 Bowden 50mm002", r"motor_mount_x006/trigger_x006$|E-spooler V005/Depressor002$"
    b_mov, b_fix, scol = r"MR63 Bearing004", r"MR63 Bearing005", "ECAS Bowden Collet005/"
    axle_rx, piv_rx = r"Hardware023/M3x8 SHCS032$", r"Hardware023/M3x8 SHCS03[34]$"
else:
    feeder, bow, trig_rx = r"\[a\]_feeder_x005", r"4x3 Bowden 50mm001", r"trigger_depressor_x4"
    b_mov, b_fix, scol = r"MR63 Bearing002", r"MR63 Bearing003", "ECAS Bowden Collet001/"
    axle_rx, piv_rx = r"M3x8 SHCS \(4\)001$", r"M3x8 SHCS \(2\) \((1\) \(1|2)\)001$"
Vbw = P_(bow)[1]; bx, by = bbc(Vbw)[:2]
FEED = np.array([bx, by, P_(feeder)[1][:, 2].max()]); BOW_T = np.array([bx, by, Vbw[:, 2].max()]); BOW_B = np.array([bx, by, Vbw[:, 2].min()])
cm_, cf_ = bbc(P_(b_mov)[1]), bbc(P_(b_fix)[1])
gap0 = np.linalg.norm((cm_ - cf_)[1:]) - 6.0
# with filament in, the moving roller swings clear and the filament runs against the fixed roller
_d = (cm_ - cf_)[1:] / np.linalg.norm((cm_ - cf_)[1:]); PNIP = np.array([bx, *(cf_[1:] + _d * (3.0 + FIL_R))])
spl, ssr = collet(scol, Z)
sc_xy = bbc(np.concatenate([spl, ssr]))[:2]
SC_TOP = np.array([*sc_xy, ssr[:, 2].max()]); SC_HEAD = np.array([*sc_xy, spl[:, 2].min()])
SH_SP, r_sp_bore = shoulder(SC_TOP, Z)                # spooler collet: the tube is pushed up through it to the shoulder
pv = np.mean([bbc(p[1]) for p in P_(piv_rx, True)], axis=0); PIV = np.array([bx, pv[1], pv[2]])
def rotx(P, th, piv=None):
    piv = PIV if piv is None else piv; P = np.atleast_2d(P) - piv; c, s = np.cos(th), np.sin(th)
    return np.c_[P[:, 0], c * P[:, 1] - s * P[:, 2], s * P[:, 1] + c * P[:, 2]] + piv
def gap(th): return np.linalg.norm((rotx(cm_, th)[0] - cf_)[1:]) - 6.0
sgn = 1.0 if gap(1e-3) > gap(0) else -1.0; lo, hi = 0.0, 0.5
for _ in range(60):
    mid = (lo + hi) / 2
    if gap(sgn * mid) < 2 * FIL_R: lo = mid
    else: hi = mid
TH_TRIG = sgn * (lo + hi) / 2
G["spool"] = {"feeder_mouth": FEED.tolist(), "bowden_top": BOW_T.tolist(), "bowden_bottom": BOW_B.tolist(), "prep_nip": PNIP.tolist(),
              "roller_gap_cad": float(gap0), "collet_top": SC_TOP.tolist(), "collet_head": SC_HEAD.tolist(), "collet_shoulder": SH_SP.tolist(),
              "collet_bore_r": r_sp_bore, "pivot": PIV.tolist(), "trig_rot_rad_about_x": float(TH_TRIG), "moving_roller": cm_.tolist(), "fixed_roller": cf_.tolist(),
              "d2f_z": [float(min(V[:, 2].min() for n, V, F in parts if "D2F" in n and ("Feed-Trigger" in n or "E-Spooler" in n))),
                        float(max(V[:, 2].max() for n, V, F in parts if "D2F" in n and ("Feed-Trigger" in n or "E-Spooler" in n)))]}
# prep switch lever: its long axis's two ends; the hinge is the end nearer the switch body, the tip the other
_lv = P_(r"D2F_Hinge")[1]; _lc = _lv.mean(0); _, _, _vt = np.linalg.svd(_lv - _lc, full_matrices=False); _ax = _vt[0]; _t = (_lv - _lc) @ _ax
_e1, _e2 = _lc + _ax * _t.min(), _lc + _ax * _t.max(); _bc = bbc(np.concatenate([V for n, V, F in parts if "D2F_Bottom" in n or "D2F_Top" in n]))
_hinge, _tip = (_e1, _e2) if np.linalg.norm(_e1 - _bc) < np.linalg.norm(_e2 - _bc) else (_e2, _e1)
G["spool"]["lever"] = {"hinge": _hinge.tolist(), "tip": _tip.tolist(), "body": _bc.tolist(), "press_mm": 2.0}
# --- spooler-to-extruder tube and the filament path
def ptube_v10():
    """centre line of the v1.0 CAD tube: start from the survey's guide line; at each station take the vertices in a 1.5 mm
    slab across the local direction (whole rings of the tube mesh) and use their centroid; smooth; repeat"""
    V = P_(r"Spooler Bowden Tubes002")[1]
    g = np.array([np.array(p) for l, p in json.load(open(D + "tools/lane_paths_survey.json"))["v10_Lane002"][5:14]])
    for it in range(4):
        gl = np.r_[0, np.cumsum(np.linalg.norm(np.diff(g, axis=0), axis=1))]; gs = np.linspace(0, gl[-1], int(gl[-1] / 0.5) + 1)
        gp = np.array([np.interp(gs, gl, g[:, k]) for k in range(3)]).T; T = np.gradient(gp, axis=0); T /= np.linalg.norm(T, axis=1)[:, None]
        C = gp.copy()
        for i, (p, t) in enumerate(zip(gp, T)):
            R = V - p; al = R @ t; lat = np.linalg.norm(R - al[:, None] * t, axis=1); m = (np.abs(al) < 0.75) & (lat < 3.0)
            if m.sum() > 20 and 1.5 < i < len(gp) - 3: C[i] = p + (R[m] - (R[m] @ t)[:, None] * t).mean(0)
        for _ in range(12): C[1:-1] = (C[:-2] + 2 * C[1:-1] + C[2:]) / 4
        g = C
    return g
if VER == "v10":
    tc = ptube_v10()
    tc = tc[(tc[:, 2] < SC_HEAD[2]) & (tc @ f < E_IN @ f)]      # below the spooler collet, up to the inlet plunger head
    TUBE = np.r_[[SC_HEAD], tc, [E_IN]]; HTUBE = None
else:
    # inferred 4 x 3 mm tube (the build guide cuts it 80 mm), shoulder to shoulder: straight down out of the spooler
    # collet, a cubic Bezier from its plunger head to the extruder inlet's plunger head, straight in to the inlet shoulder.
    # The Bezier's two (equal) handles are chosen for the gentlest bend (largest minimum bend radius); its length is reported.
    def tube_for(h):
        B = bezier(SC_HEAD, SC_HEAD - Z * h, E_IN - f * h, E_IN); return np.r_[[SH_SP, SC_TOP], B, [E_INR, SH_IN]]
    def min_r(h):
        B = bezier(SC_HEAD, SC_HEAD - Z * h, E_IN - f * h, E_IN, 400); d1 = np.gradient(B, axis=0); d2 = np.gradient(d1, axis=0)
        return float((np.linalg.norm(d1, axis=1) ** 3 / np.maximum(np.linalg.norm(np.cross(d1, d2), axis=1), 1e-12)).min())
    hs = np.arange(5.0, 40.0, 0.25); HTUBE = float(hs[np.argmax([min_r(h) for h in hs])]); MINR = min_r(HTUBE); full_t = tube_for(HTUBE)
    TUBE = bezier(SC_HEAD, SC_HEAD - Z * HTUBE, E_IN - f * HTUBE, E_IN)
    parts.append(("PTFE_INF_spool_ext", *sweep(full_t, 1.97, 1.5)))
    # extruder to hub, 4 x 2 mm, chamfered 0.5 mm inside at each end: from the outlet shoulder straight out along the line
    hub_end = on_line(t_out_head + 30.0)
    parts.append(("PTFE_INF_ext_hub", *sweep(np.array([SH_OUT, hub_end]), 1.97, 1.0, ch0=0.5, ch1=0.5)))
G["tube"] = {"bezier_handle_mm": HTUBE, "min_bend_r_mm": MINR, "length_mm": plen(full_t)} if VER != "v10" else {"cad": True}
PATH = [("feeder_mouth", FEED), ("bowden_top", BOW_T), ("bowden_bottom", BOW_B), ("prep_nip", PNIP), ("spool_tube", SH_SP),
        ("spool_collet", SC_TOP), ("spool_collet_head", SC_HEAD)]
PATH += [(None, p) for p in TUBE[1:-1]]
PATH += [("ext_in", E_IN), ("ext_in_retainer", E_INR), ("ext_in_tube_end", SH_IN), ("nip", NIP), ("load", LOAD),
         ("ext_out_tube_end", SH_OUT), ("ext_out_retainer", E_OUTR), ("ext_out", E_OUT)]
if VER == "v10":   # the CAD tube stops at the spooler collet's top: the filament enters the PTFE there
    PATH = [(k if k != "spool_tube" else None, p) for k, p in PATH if k != "spool_tube"]
pts = np.array([p for _, p in PATH]); s = np.r_[0, np.cumsum(np.linalg.norm(np.diff(pts, axis=0), axis=1))]
EV = {k + "_s": float(si) for (k, _), si in zip(PATH, s) if k}
if VER == "v10": EV["spool_tube_s"] = EV["spool_collet_s"]
G["path"] = {"pts": pts.tolist(), "s": s.tolist(), "events": EV}
# grip radius: drive gear centre to the filament surface (1.75 mm filament on the line), the radius the filament is driven at
G["drive"] = {"r_grip_mm": float(abs(gears["dgear"]["uv"][1]) - FIL_R), "centre_to_line_mm": float(abs(gears["dgear"]["uv"][1])),
              "r_cut_mm": gears["dgear"]["r_cut"], "ratio_motor_to_drive": float(np.prod([b / a_ for a_, b in TRAIN])), "train": TRAIN}

# ---------------------------------------------------------------- views and groups
if VIEW == "ext":
    O, U, VV = OE, f, Z
    bounds = (-14.0, 80.0, -18.0, 26.0)
    MOV = {"apex": {"dgear": r"Drive_Gear_Orbiter|M3x4 Grub_Screw|BMG drive shaft", "igear": r"Idler_Orbiter_Gear", "bear": r"MR63ZZ bearing"},
           "bmg": {"dgear": r"Spur Gear 50t00\d/Spur Gear 50t00[17]$", "igear": r"BMG_Idler", "bear": r"MR63ZZ bearing"},
           "proto": {"dgear": r"Gearpack00[23]$", "igear": r"Gearpack00[47]$", "bear": r"MR63ZZ bearing"}}[FAM]
    OVER = {"apex": r"BMG 50t drive gear/SOLID027|T10 SpurGear|Apex_A/Motor_Plate$|LDO Stepper|MR85ZZ_Bearing(016|101)/|M3x20 SHCS \(3\)00[12]$",
            "bmg": r"Spur Gear 50t00\d/Spur Gear 50t(006)?$|T10 SpurGear|motor_plate|LDO Stepper|MR825",
            "proto": r"Gearpack010$|Gearpack00[15]$|T10 SpurGear|motor_plate|LDO Stepper"}[FAM]
    OVERMOVE = r"(?!x)x"; OM_DEPTH = 0.0
    # the rest of the turning drive train, one sprite group per rigid body (or per bearing set on one shaft), taken out of the
    # base and the over layer. (regex, rate reference, multiplier): canvas rate = the reference gear's rate x multiplier.
    # Meshing gears turn opposite ways at the tooth ratio; a ball bearing is drawn turning at its cage speed, taken as 0.4 x
    # the part it carries. Every part here has its axis along the view normal (checked below).
    (_d, _n), = TRAIN[-1:]
    _m0 = -TRAIN[0][1] / TRAIN[0][0]                    # motor pinion against the gear it drives
    SPIN = {"apex": {"gear50": (r"BMG 50t drive gear/SOLID027", "dgear", 1.0),
                     "pinion": (r"T10 SpurGear", "dgear", _m0),
                     "bear_drive": (r"MR85ZZ_Bearing\d+/", "dgear", 0.4)},
            "bmg": {"gear50": (r"Spur Gear 50t00\d/Spur Gear 50t(006)?$", "dgear", 1.0),
                    "pinion": (r"T10 SpurGear", "dgear", _m0),
                    "bear_drive": (r"MR825 Ballbearing", "dgear", 0.4)},
            # ProtoXtruder: T10 -> 44 T compound gear, whose 17 T pinion drives the 37 T drive gear
            "proto": {"gear44": (r"Gearpack010$", "dgear", -_n / _d),
                      "pinion": (r"T10 SpurGear", "dgear", -_n / _d * _m0),
                      "bear_44": (r"Gearpack00[15]$", "dgear", -_n / _d * 0.4),
                      "bear_drive": (r"Gearpack0(09|12)$", "dgear", 0.4),
                      "bear_idler": (r"Gearpack0(08|11)$", "igear", 0.4)}}[FAM]
    MOV.update({"spin_" + k: v[0] for k, v in SPIN.items()})
else:
    SPIN = {}
    if VER == "v10": O, U, VV = np.array([105.1, 240.0, 0]), np.array([0, -1.0, 0]), Z
    else: O, U, VV = np.array([105.0, 0, 0]), np.array([0, 1.0, 0]), Z
    bounds = (4.0, 66.0, 34.0, 164.0)
    # the feeder bowden sits in the trigger's bore: it and its feeder collar pivot with the trigger (repo owner)
    trig = trig_rx + "|" + b_mov + "|" + axle_rx + "|" + feeder + "|" + bow
    MOV = {"trig": trig, "lever": r"D2F_Hinge"}   # the prep switch's lever: pressed by the trigger arm when the lane is empty
    OVER = (r"Spur Gear \(12 teeth\)|N20 DC MOTOR|gearbox_cover|motor_mount_x007|Tire001|new_wheel_1\.012|spooler_cover|Lightbox v5.*SOLID025|D2F"
            if VER != "v10" else r"helical_gear|gear_30_spacer|gearbox_cover|motor_mount_x006/SOLID022|Wheel v011/.*(Tire004|SOLID024|Drive012)|Lightbox v007/SOLID023|D2F")
    OVERMOVE = trig_rx
    d2f = np.concatenate([V for n, V, F in parts if "D2F_Bottom" in n or "D2F_Top" in n])
    OM_DEPTH = float(np.min((d2f - O) @ np.cross(VV, U)))   # depressor leg drawn where it meets the switch: cut at the switch's near face
NV = np.cross(VV, U)
def _lift(n, Dp):   # how the over layer places a part: viewer-side parts uncut, the gear train over the motor plate
    return Dp + ((50.0 if re.search(GEARTOP, n) else 100.0) if Dp.min() < 0 else 0.0)
def _spin_geom():
    out = []
    for k, (rx, ref, mult) in SPIN.items():
        ps = [(n, V) for n, V, F in parts if re.search(rx, n) and classify(n)[0]]
        assert ps, k
        Q = np.concatenate([np.c_[(V - O) @ U, (V - O) @ VV] for n, V in ps])
        # rotation centre: circle fit to the outermost vertices (gear tips, outer race), started from the bounding box
        c = (Q.min(0) + Q.max(0)) / 2
        for _ in range(4):
            r = np.linalg.norm(Q - c, axis=1); c, R = circfit(Q[r >= np.percentile(r, 90)])
        ext = Q.max(0) - Q.min(0)
        for n, V in ps:   # axis along the view normal: the part's outline is round in the view
            q = np.c_[(V - O) @ U, (V - O) @ VV]; e = q.max(0) - q.min(0)
            if abs(e[0] - e[1]) > 0.06 * e.max() + 0.05: print("WARNING", k, n, "not round in the view", e)
        see = [n for n, V in ps if re.search(OVER, n)]
        dep = [float(np.mean(_lift(n, (V - O) @ NV - 0.01))) for n, V in ps if n in see]
        out.append({"name": k, "mode": "spin_" + k, "ref": ref, "mult": mult, "uv": [float(c[0]), float(c[1])], "r_out_mm": float(R),
                    "parts": [n for n, V in ps], "see_parts": see, "see_depth": max(dep) if dep else None})
    return out
GEARTOP = r"SOLID027|T10 SpurGear|Spur Gear 50t(006)?$|Gearpack010$|Spur Gear \(12 teeth\)|helical_gear"
G["spin"] = _spin_geom() if VIEW == "ext" else []
def group(n):
    for g, rx in MOV.items():
        if re.search(rx, n): return g
    return None
ONLY = os.environ.get("ONLY")         # debugging: render only the parts matching this regex
def wanted(n):
    if ONLY and not re.search(ONLY, n): return False
    g = group(n)
    if MODE in ("static", "full"): return True
    if MODE == "base": return g is None
    if MODE in MOV: return g == MODE
    if MODE == "over": return g is None and bool(re.search(OVER, n))
    if MODE.startswith("spin_") and MODE.endswith("_see"): return g == MODE[:-4] and bool(re.search(OVER, n))
    if MODE == "overmove": return bool(re.search(OVERMOVE, n))
    return False
G["view"] = {"view": VIEW, "O": O.tolist(), "U": U.tolist(), "V": VV.tolist(), "N": NV.tolist(), "xmin": bounds[0], "xmax": bounds[1],
             "vmin": bounds[2], "vmax": bounds[3], "px": PXMM, "groups": list(MOV), "overmove_depth": OM_DEPTH}
json.dump(G, open(OUT + "geom.json", "w"), indent=1)
if MODE == "geom": raise SystemExit
# moving parts are drawn in their CAD (empty) position; the page moves the sprites

# ---------------------------------------------------------------- map to (screen x, depth, screen up) and rasterize
xmin, xmax, zmin, zmax = bounds
mapped = []; CUT_EPS = float(os.environ.get("CUT_EPS", "0.01"))   # the cut sits a hair behind the modeled filament plane, clear of the hob and channel vertices on it
for n, V, F in parts:
    lab, _ = classify(n)
    if lab is None or not wanted(n): continue
    R = V - O; X = R @ U; Dp = R @ NV - CUT_EPS; Up = R @ VV
    if MODE == "over" or MODE.endswith("_see"):   # viewer-side parts uncut, with the gear train drawn over the motor plate; parts behind the cut on top
        Dp = _lift(n, Dp)
    if MODE == "overmove": Dp = Dp - OM_DEPTH
    if MODE == "bear": Dp = Dp + 100.0   # the load-sensor bearing is drawn whole, not cut (repo owner)
    M = np.c_[X, Dp, Up]; T = M[F]
    keep = (T[:, :, 0].max(1) >= xmin - 1) & (T[:, :, 0].min(1) <= xmax + 1) & (T[:, :, 2].max(1) >= zmin - 1) & (T[:, :, 2].min(1) <= zmax + 1) & (T[:, :, 1].max(1) >= 0)
    if keep.any(): mapped.append((n, M, F[keep]))
parts = mapped
if not parts:   # nothing of this group on the drawn side of the cut (a spin group wholly on the viewer side): an empty layer
    _W, _H = int((xmax - xmin) * S) // SS, int((zmax - zmin) * S) // SS
    Image.new("RGBA", (_W, _H)).save(OUT + f"layer_{MODE}{SUF}.png"); np.save(OUT + f"depth_{MODE}{SUF}.npy", np.full((_H, _W), np.inf, np.float32))
    raise SystemExit
bstr = f"xmin, xmax = {xmin}, {xmax}; zmin, zmax = {zmin}, {zmax}"
src_r = open(D + "tools/section.py").read()
tail = src_r[src_r.index("tris, cols, pid = [], [], []"):].replace("CAPOVR = {", "_unused = {", 1)
tail = re.sub(r"xmin, xmax = [^\n]*", bstr, tail, count=1).replace("if lab is None or", "if lab is None or not len(V) or")
# a cut face wins ties: where two parts touch flush, the far part's front face and the near part's back face (the cut face
# seen through the section) share a depth, and rounding let the far part show through in streaks
_z = "z = w1 * pz[0] + w2 * pz[1] + w3 * pz[2]"; assert _z in tail
tail = tail.replace(_z, _z + " - (0.05 if cap[k] else 0.0)")
exec(tail)

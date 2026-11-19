# Trace the filament paths through each BoxTurtle v1.1 hub from its CAD: slice the hub body at its channel plane, then
# march from each inlet socket along the void, re-centering between the channel walls, until the channel meets the outlet
# axis. Writes tools/hub_paths.json (paths and inferred PTFE). AGPL-3.0 (see LICENSE).
import numpy as np, json, os
from PIL import Image, ImageDraw
D = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "")
HUBS = {"combo": {"src": "btcombo", "body": "[a]_hub/SOLID010", "az": 18.2, "out_ptfe": [277.0, 330.0], "outlet_end": 251.0},
        "loadonly": {"src": "bthub_loadonly", "body": "hub_load_only_1.1/SOLID035", "az": 20.65, "out_ptfe": [251.0, 330.0], "outlet_end": 255.2},
        "v10": {"src": "bthub10", "body": "Hubs/Hub_D2HW v2/COMPOUND002/COMPOUND", "az": 20.65, "out_ptfe": [250.5, 330.0], "outlet_end": 255.2}}
# the v1.0 hub's own ECAS04 collets give its socket axes exactly (plunger to seal retainer), lanes numbered by X
V10_COLLETS = {"lane1": "ECAS Bowden Collet (4)/", "lane2": "ECAS Bowden Collet (3)/", "lane3": "ECAS Bowden Collet (1)004/", "lane4": "ECAS Bowden Collet (2)/"}
def collet_axes(src, keys):
    d = np.load(D + f"cad/{src}.npz"); N = json.load(open(D + f"cad/{src}.json")); out = {}
    for lane, key in keys.items():
        c = {}
        for i, n in enumerate(N):
            if key in n:
                for part in ("Plunger", "Seal Retainer"):
                    if "/" + part in n: V = d["p%03d_V" % i]; c[part] = (V.min(0) + V.max(0)) / 2
        a = (c["Seal Retainer"] - c["Plunger"])[:2]; out[lane] = (c["Plunger"][:2].tolist(), (a / np.linalg.norm(a)).tolist())
    return out
AX = 150.1
# first guesses of the inlet axes, from the combo's ECAS04 collets (plunger to seal retainer); lanes numbered by X
GUESS = {"lane1": ([132.65, 204.81], [0.622, 0.783]), "lane2": ([143.77, 200.65], [0.26, 0.966]),
         "lane3": ([156.55, 200.68], [-0.26, 0.966]), "lane4": ([167.75, 204.81], [-0.622, 0.783])}
R = 20.0; X0, Y0 = 120.0, 185.0; Wd, Ht = int(60 * R), int(80 * R)          # raster: x index = (X - X0), y index = (Y - Y0)
def solid_mask(T, z):
    """even-odd fill of the closed loops where the plane Z = z cuts the mesh"""
    tz = T[:, :, 2]; m = (tz.min(1) < z) & (tz.max(1) > z); segs = []
    for tri in T[m]:
        p = []
        for a, b in ((0, 1), (1, 2), (2, 0)):
            A, B = tri[a], tri[b]
            if (A[2] - z) * (B[2] - z) < 0: t = (z - A[2]) / (B[2] - A[2]); p.append(tuple(np.round((A + (B - A) * t)[:2], 4)))
        if len(p) == 2: segs.append(p)
    adj = {}
    for a, b in segs: adj.setdefault(a, []).append(b); adj.setdefault(b, []).append(a)
    seen = set(); acc = np.zeros((Ht, Wd), bool)
    for s in adj:
        if s in seen: continue
        loop = [s]; seen.add(s); prev, cur = None, s
        while True:
            nx = [q for q in adj[cur] if q != prev and q not in seen]
            if not nx: break
            prev, cur = cur, nx[0]; seen.add(cur); loop.append(cur)
        if len(loop) < 3: continue
        im = Image.new("1", (Wd, Ht), 0); ImageDraw.Draw(im).polygon([((x - X0) * R, (y - Y0) * R) for x, y in loop], fill=1)
        acc ^= np.array(im)
    return acc
def void_at(M, x, y):
    i, j = int((y - Y0) * R), int((x - X0) * R)
    return not (0 <= i < Ht and 0 <= j < Wd) or not M[i, j]
def trace(M, p, d):
    p = np.array(p, float); d = np.array(d, float); d /= np.linalg.norm(d); pts = []; inside = False; narrow = False; seat = None
    for _ in range(400):
        n = np.array([-d[1], d[0]]); ext = []
        for sgn in (-1, 1):
            k = 0.0
            while k < 6.0 and void_at(M, *(p + sgn * n * (k + 0.05))): k += 0.05
            ext.append(k)
        w = ext[0] + ext[1]
        if ext[0] < 6.0 and ext[1] < 6.0:
            if w < 3.2 and not narrow: narrow = True; seat = p.round(2).tolist()
            if narrow and w > 3.6: break           # the channel opens into the merge
            inside = True; p = p + n * (ext[1] - ext[0]) / 2
        if inside: pts.append(p.round(2).tolist())
        if inside and abs(p[0] - AX) < 0.6: break
        q = p + d * 0.5
        if inside and len(pts) > 3:            # follow the channel: new heading from the last few centers
            v = np.array(pts[-1]) - np.array(pts[-4]); d = 0.7 * d + 0.3 * v / (np.linalg.norm(v) or 1); d /= np.linalg.norm(d)
        p = q
    return pts, seat
def fit_socket(T, az, centre, a):
    """socket position: least-squares circle through the socket's wall faces (normals square to the axis), in the plane
    normal to the axis a; returns a point on the axis"""
    cen = T.mean(1); nr = np.cross(T[:, 1] - T[:, 0], T[:, 2] - T[:, 0]); ar = np.linalg.norm(nr, axis=1); nr = nr / np.maximum(ar, 1e-12)[:, None]
    a = np.array([a[0], a[1], 0.0]); e1 = np.cross(a, [0, 0, 1.0]); e1 /= np.linalg.norm(e1); e2 = np.cross(a, e1)
    for _ in range(4):
        rel = cen - np.array([centre[0], centre[1], az]); along = rel @ a; radial = np.linalg.norm(rel - np.outer(along, a), axis=1)
        m = (ar > 1e-9) & (np.abs(along) < 4.5) & (radial > 2.2) & (radial < 6.5) & (np.abs(nr @ a) < 0.35)
        x = cen[m] @ e1; y = cen[m] @ e2; cx_, cy_, _ = np.linalg.lstsq(np.c_[2 * x, 2 * y, np.ones_like(x)], x ** 2 + y ** 2, rcond=None)[0]
        p = cx_ * e1 + cy_ * e2; centre = (p + a * ((np.array([centre[0], centre[1], az]) - p) @ a))[:2]
    return np.array(centre)
def floor_on(M, pt, a):
    """walk along the axis, 3 mm to each side of it (clear of the narrow channel), to the socket's floor"""
    n = np.array([-a[1], a[0]]); best = []
    for side in (-1, 1):
        q = np.array(pt, float) + n * 3.0 * side; k = 0.0
        while k < 25 and void_at(M, *(q + a * k)): k += 0.05
        best.append(k)
    return np.array(pt, float) + a * min(best)
COLLETS = {"lane1": "ECAS Bowden Collet (1) (1)003", "lane2": "ECAS Bowden Collet (1) (1)", "lane3": "ECAS Bowden Collet (1) (1)001", "lane4": "ECAS Bowden Collet (1) (1)002"}
out = {"_note": "Filament paths in BoxTurtle CAD coordinates (mm), by tools/hub_paths.py. Each lane (numbered by X, lane1 lowest) runs along its inlet socket axis to the socket floor (seat), then along the channel centre traced from a section of the hub body in the plane of the outlet axis, to the outlet axis (X 150.1). Socket axes: the combo's ECAS04 collet axes; the load-only hub uses the same directions with socket positions fitted from its mesh (mirror-averaged). PTFE tubes are inferred: inlet tubes end at the socket floor; the outlet tube starts at out_ptfe[0]. collet_shift moves the combo's collets onto the load-only hub.", "axis_x": AX}
for h, c in HUBS.items():
    d = np.load(D + f"cad/{c['src']}.npz"); N = json.load(open(D + f"cad/{c['src']}.json")); i = N.index(c["body"])
    T = d["p%03d_V" % i].astype(float)[d["p%03d_F" % i]]; M = solid_mask(T, c["az"]); lanes = {}
    fits = {}; G = collet_axes("bthub10", V10_COLLETS) if h == "v10" else GUESS
    for k, (p, v) in G.items():
        v = np.array(v) / np.linalg.norm(v); pts, seat = trace(M, np.array(p) - v * 6, v)
        # socket axis: the combo's collet axes directly; the load-only hub's sockets point the same way (within 1 degree by
        # a fit of their walls) but sit elsewhere, so their positions are fitted from the mesh
        ctr = np.array(p, float) if h in ("combo", "v10") else fit_socket(T, c["az"], np.array(seat) - v * 4, v)
        fits[k] = (pts, seat, v, ctr)
    if h == "loadonly":   # the hub is mirror-symmetric about X = AX: average each socket with its mirror partner
        for a_, b_ in (("lane1", "lane4"), ("lane2", "lane3")):
            pa, pb = fits[a_][3], fits[b_][3]; m = (pa + np.array([2 * AX - pb[0], pb[1]])) / 2
            fits[a_] = fits[a_][:3] + (m,); fits[b_] = fits[b_][:3] + (np.array([2 * AX - m[0], m[1]]),)
    for k, (pts, seat, v, ctr) in fits.items():
        fl = floor_on(M, ctr, v)
        # path: along the socket axis to its floor, then the traced channel from where it narrows
        si = int(np.argmin([np.hypot(q[0] - seat[0], q[1] - seat[1]) for q in pts])); pts = [fl.round(2).tolist()] + pts[si:]
        end = np.array(pts[-1]); pts.append([AX, round(float(end[1] + abs(end[0] - AX) * 1.5), 2)])   # join the outlet axis
        lanes[k] = {"path": pts, "seat": fl.round(2).tolist(), "dir": v.round(4).tolist()}
    Image.fromarray((~M * 255).astype(np.uint8)).save(D + f"build/hub_{h}_mask.png")
    out[h] = {"az": c["az"], "lanes": lanes, "outlet_end": c["outlet_end"], "out_ptfe": c["out_ptfe"]}
    print(h, {k: (v["seat"], v["dir"]) for k, v in lanes.items()})
# ECAS04 collets for the load-only hub (its STEP has none): the combo's, moved so each sits the same distance from its
# socket floor along the same axis
for k in COLLETS:
    a_, b_ = out["combo"]["lanes"][k], out["loadonly"]["lanes"][k]
    out["loadonly"]["lanes"][k]["collet_shift"] = [round(b_["seat"][0] - a_["seat"][0], 3), round(b_["seat"][1] - a_["seat"][1], 3), round(out["loadonly"]["az"] - out["combo"]["az"], 3)]
out["collets"] = COLLETS
json.dump(out, open(D + "tools/hub_paths.json", "w"), indent=0)

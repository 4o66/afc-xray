# Trace the filament paths through each BoxTurtle v1.1 hub from its CAD: slice the hub body at its channel plane, then
# march from each inlet socket along the void, re-centering between the channel walls, until the channel meets the outlet
# axis. Writes tools/hub_paths.json (paths and inferred PTFE). AGPL-3.0 (see LICENSE).
import numpy as np, json, os, re
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
    p = np.array(p, float); d = np.array(d, float); d /= np.linalg.norm(d); pts = []; inside = False; narrow = False; merging = False; seat = None; mi = None
    for _ in range(400):
        n = np.array([-d[1], d[0]]); ext = []
        for sgn in (-1, 1):
            k = 0.0
            while k < 6.0 and void_at(M, *(p + sgn * n * (k + 0.05))): k += 0.05
            ext.append(k)
        w = ext[0] + ext[1]
        if ext[0] < 6.0 and ext[1] < 6.0:
            if w < 3.2 and not narrow: narrow = True; seat = p.round(2).tolist()
            if narrow and (w > 3.6 or merging):
                # where the channels open into the merge, keep to this channel's outer wall (the side away from the outlet
                # axis), half a channel width off it, so the path keeps the channel's sweep instead of cutting across
                if not merging: mi = len(pts)
                merging = True; so = 1 if n @ np.array([p[0] - AX, 0.0]) > 0 else 0
                off = ext[so] - 1.17 if ext[so] < 5.9 else 0.0; p = p + n * (off if so == 1 else -off)
            else: p = p + n * (ext[1] - ext[0]) / 2
            inside = True
        if inside: pts.append(p.round(2).tolist())
        if inside and merging and abs(p[0] - AX) < 0.15: break
        if inside and not merging and abs(p[0] - AX) < 0.6: break
        q = p + d * 0.5
        if inside and len(pts) > 3:            # follow the channel: new heading from the last few centers
            v = np.array(pts[-1]) - np.array(pts[-4]); d = 0.7 * d + 0.3 * v / (np.linalg.norm(v) or 1); d /= np.linalg.norm(d)
        p = q
    return pts, seat, mi
def widths(M, p, a, maxw=7.0):
    n = np.array([-a[1], a[0]]); e = []
    for sg in (-1, 1):
        k = 0.0
        while k < maxw and void_at(M, *(p + sg * n * (k + 0.05))): k += 0.05
        e.append(k)
    return e
def socket_geom(M, p0, a0):
    """A fitting's socket and the PTFE counterbore behind it are coaxial bores: fit the axis through the mid-points of
    both (socket 7.5-9.5 mm wide, counterbore 3.8-4.8 mm), then find the socket floor and the shoulder where the
    counterbore steps down to the filament channel. Returns a point on the axis, the axis (pointing inward), and the
    floor and shoulder points."""
    p, a = np.array(p0, float), np.array(a0, float) / np.linalg.norm(a0)
    for _ in range(4):
        n = np.array([-a[1], a[0]]); mids = []
        for t in np.arange(-1.0, 12.0, 0.25):
            q = p + a * t; e = widths(M, q, a); w = e[0] + e[1]
            if 7.5 < w < 9.5 or 3.8 < w < 4.8: mids.append(q + n * (e[1] - e[0]) / 2)
        if len(mids) < 6: break
        Q = np.array(mids); c = Q.mean(0); _, _, vt = np.linalg.svd(Q - c); a_new = vt[0] * np.sign(vt[0] @ a)
        p, a = c - a_new * ((c - p) @ a_new), a_new
    prof = [(t, sum(widths(M, p + a * t, a))) for t in np.arange(-2.0, 16.0, 0.05)]
    floor = next(t for t, w in prof if t > 0 and w < 7.0)
    cb = [t for t, w in prof if t > floor and 3.8 < w < 4.8]
    shoulder = next(t for t, w in prof if t > (cb[0] if cb else floor) and w < 3.6)
    return p, a, p + a * floor, p + a * shoulder
def collet_fit(src_, key):
    """centroid and axis of an ECAS04 collet: the axis is the direction square to the normals of its cylindrical faces
    (area-weighted, iterated from the least-spread direction of its vertices)"""
    d = np.load(D + f"cad/{src_}.npz"); N = json.load(open(D + f"cad/{src_}.json"))
    idx = [i for i, n in enumerate(N) if key in n and re.search(r"Collet Body|Plunger|Seal Retainer", n)]
    T = np.concatenate([d["p%03d_V" % i].astype(float)[d["p%03d_F" % i]] for i in idx]); V = T.reshape(-1, 3)
    c = V.mean(0); _, _, vt = np.linalg.svd(V - c, full_matrices=False); a = vt[2]
    nr = np.cross(T[:, 1] - T[:, 0], T[:, 2] - T[:, 0]); ar = np.linalg.norm(nr, axis=1); ok = ar > 1e-12; nr = nr[ok] / ar[ok][:, None]; w = np.sqrt(ar[ok])
    for _ in range(6):
        m = np.abs(nr @ a) < 0.3; _, _, vt2 = np.linalg.svd(nr[m] * w[m][:, None], full_matrices=False); a = vt2[2] * np.sign(vt2[2] @ a)
    a2 = a[:2] / np.linalg.norm(a[:2]); return c, a2
COLLET_KEYS = {"combo": ("btcombo", {"lane1": "ECAS Bowden Collet (1) (1)003/", "lane2": "ECAS Bowden Collet (1) (1)/", "lane3": "ECAS Bowden Collet (1) (1)001/", "lane4": "ECAS Bowden Collet (1) (1)002/", "out": "ECAS Bowden Collet (1)/"}),
               "v10": ("bthub10", {"lane1": "ECAS Bowden Collet (4)/", "lane2": "ECAS Bowden Collet (3)/", "lane3": "ECAS Bowden Collet (1)004/", "lane4": "ECAS Bowden Collet (2)/", "out": "ECAS Bowden Collet008/"})}
out = {"_note": "Filament paths in BoxTurtle CAD coordinates (mm), by tools/hub_paths.py. Lanes are numbered by X, lane1 lowest. Each fitting socket and the PTFE counterbore behind it are coaxial: their axis is fitted through the mid-points of both in a section of the hub body at the plane of the outlet axis. Every ECAS04 collet is set on that axis (turned by angle about the point about, moved to, dz), at its CAD distance from the socket floor; the load-only hub, which has no fittings in its STEP, gets the combo's inlet collets and the v1.0 hub's outlet collet. PTFE is inferred: coaxial with the fitting and inserted to the shoulder where the counterbore steps down to the filament channel (lanes: seat; outlet: shoulder). Each lane path starts there and follows the traced channel centre to the outlet axis (X 150.1).", "axis_x": AX}
REF = {}
for h, c in HUBS.items():
    d = np.load(D + f"cad/{c['src']}.npz"); N = json.load(open(D + f"cad/{c['src']}.json")); i = N.index(c["body"])
    T = d["p%03d_V" % i].astype(float)[d["p%03d_F" % i]]; M = solid_mask(T, c["az"]); lanes = {}
    for k in ("lane1", "lane2", "lane3", "lane4", "out"):
        if h in COLLET_KEYS:                               # start from the hub's own collet
            cc, a0 = collet_fit(COLLET_KEYS[h][0], COLLET_KEYS[h][1][k]); p0 = cc[:2]
        elif k == "out": p0, a0 = np.array([AX, c["outlet_end"] - 3.0]), np.array([0.0, -1.0])
        else: p0, a0 = np.array(GUESS[k][0]), np.array(GUESS[k][1])
        a0 = np.array(a0, float)
        if (k == "out" and a0[1] > 0) or (k != "out" and a0[1] < 0): a0 = -a0          # inward
        if h == "combo" and k == "out":
            # the combo's outlet fitting sits in the sliding load-sensor block, whose mesh does not slice into closed outlines;
            # measured by ray casting along the outlet axis instead: socket 8.33 mm from Y 282.5 to 277.5, counterbore 4.4 mm
            # from 276.5 to 274.5, then the 2.34 mm filament bore
            a = np.array([0.0, -1.0]); fl, sh = np.array([AX, 277.0]), np.array([AX, 274.3])
        else: pa, a, fl, sh = socket_geom(M, p0, a0)
        if h in COLLET_KEYS:   # the collet's own axis (to turn it onto the socket's) and its centroid's depth from the socket floor
            a_own = np.array(a0, float) / np.linalg.norm(a0); a_own = a_own if a_own @ a > 0 else -a_own
            REF[(h, k)] = (cc, a_own, float((fl - cc[:2]) @ a))
        if k == "out":   # the hubs are mirror-symmetric about their outlet axis: keep its fitted position, square its direction to -Y
            a = np.array([0.0, -1.0]); fl = np.array([fl[0], fl[1]]); sh = np.array([fl[0], sh[1]])
            lanes["out"] = {"shoulder": sh.round(3).tolist(), "floor": fl.round(3).tolist(), "dir": a.round(4).tolist()}; continue
        pts, seat, mi = trace(M, sh - a * 0.5, a)
        si = int(np.argmin([np.hypot(q[0] - seat[0], q[1] - seat[1]) for q in pts])) if seat else 0
        if k == "lane2" and mi is not None and "lane1" in lanes:
            # the inner channel opens into the outer one before the merge: past that opening, a smooth (Hermite) curve
            # leaving along the channel and arriving tangent to the outlet axis where the outer lane's sweep meets it
            P0 = np.array(pts[mi - 1]); t0 = P0 - np.array(pts[max(si + 1, mi - 6)]); t0 /= np.linalg.norm(t0)
            P1 = np.array([AX, lanes["lane1"]["path"][-2][1]]); L = np.linalg.norm(P1 - P0); m0, m1 = t0 * L, np.array([0.0, 1.0]) * L
            tt = np.linspace(0, 1, 24)[1:, None]
            H = (2*tt**3 - 3*tt**2 + 1) * P0 + (tt**3 - 2*tt**2 + tt) * m0 + (-2*tt**3 + 3*tt**2) * P1 + (tt**3 - tt**2) * m1
            pts = pts[:mi] + H.round(3).tolist()
        pts = [sh.round(2).tolist()] + pts[si + 1:]
        P = np.array(pts, float)
        for _ in range(3):                         # light smoothing of the traced centre line (ends kept)
            P[1:-1] = (P[:-2] + 2 * P[1:-1] + P[2:]) / 4
        P[-1, 0] = AX; pts = P.round(2).tolist(); pts.append([AX, round(float(P[-1, 1] + 4.0), 2)])
        lanes[k] = {"path": pts, "seat": sh.round(3).tolist(), "floor": fl.round(3).tolist(), "dir": a.round(4).tolist()}
    # the hubs are mirror-symmetric about the outlet axis: lanes 3 and 4 are lanes 2 and 1 mirrored, which keeps the
    # traced sweeps identical on both sides
    mir = lambda q: [round(2 * AX - q[0], 3), q[1]]
    for src_k, dst_k in (("lane1", "lane4"), ("lane2", "lane3")):
        L1 = lanes[src_k]; lanes[dst_k] = {"path": [mir(q) for q in L1["path"]], "seat": mir(L1["seat"]), "floor": mir(L1["floor"]), "dir": [-L1["dir"][0], L1["dir"][1]]}
    Image.fromarray((~M * 255).astype(np.uint8)).save(D + f"build/hub_{h}_mask.png")
    out[h] = {"az": c["az"], "lanes": {k: v for k, v in lanes.items() if k != "out"}, "outlet": lanes["out"], "outlet_end": c["outlet_end"]}
    print(h, {k: (v.get("seat", v.get("shoulder")), v["dir"]) for k, v in lanes.items()})
def place(ref, lo, az_from, az_to):
    cc, a_ref, s_ref = ref; a_new = np.array(lo["dir"]); new_c = np.array(lo["floor"]) - a_new * s_ref
    ang = np.arctan2(a_new[1], a_new[0]) - np.arctan2(a_ref[1], a_ref[0])
    return {"about": [round(float(cc[0]), 3), round(float(cc[1]), 3)], "angle": round(float(ang), 5), "to": [round(float(new_c[0]), 3), round(float(new_c[1]), 3)], "dz": round(az_to - az_from, 3)}
for h in HUBS:
    for k in ("lane1", "lane2", "lane3", "lane4", "out"):
        src_h = h if h in COLLET_KEYS else ("v10" if k == "out" else "combo")      # the load-only hub borrows fittings
        tgt = out[h]["outlet"] if k == "out" else out[h]["lanes"][k]
        tgt["collet"] = {"src": COLLET_KEYS[src_h][0], "key": COLLET_KEYS[src_h][1][k], **place(REF[(src_h, k)], tgt, HUBS[src_h]["az"], HUBS[h]["az"])}
json.dump(out, open(D + "tools/hub_paths.json", "w"), indent=0)

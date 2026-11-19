# Trace the filament paths through each BoxTurtle v1.1 hub from its CAD: slice the hub body at its channel plane, then
# march from each inlet socket along the void, re-centering between the channel walls, until the channel meets the outlet
# axis. Writes tools/hub_paths.json (paths and inferred PTFE). AGPL-3.0 (see LICENSE).
import numpy as np, json, os
from PIL import Image, ImageDraw
D = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "")
HUBS = {"combo": {"src": "btcombo", "body": "[a]_hub/SOLID010", "az": 18.2, "out_ptfe": [277.0, 330.0], "outlet_end": 251.0},
        "loadonly": {"src": "bthub_loadonly", "body": "hub_load_only_1.1/SOLID035", "az": 20.65, "out_ptfe": [251.0, 330.0], "outlet_end": 255.2}}
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
out = {"_note": "Filament paths in BoxTurtle CAD coordinates (mm), traced from the hub bodies by tools/hub_paths.py: inlet axes start from the combo's ECAS04 collet axes (lanes numbered by X, lane1 lowest) and follow each channel's centre in the plane of the outlet axis until it meets the outlet axis (X 150.1). PTFE tubes are inferred: inlet tubes end in each inlet socket; the outlet tube to the toolhead starts at out_ptfe[0].", "axis_x": AX}
for h, c in HUBS.items():
    d = np.load(D + f"cad/{c['src']}.npz"); N = json.load(open(D + f"cad/{c['src']}.json")); i = N.index(c["body"])
    T = d["p%03d_V" % i].astype(float)[d["p%03d_F" % i]]; M = solid_mask(T, c["az"]); lanes = {}
    for k, (p, v) in GUESS.items():
        v = np.array(v) / np.linalg.norm(v); pts, seat = trace(M, np.array(p) - v * 6, v)
        # the socket is the first stretch whose walls are wider than the channel; the PTFE ends where it narrows
        end = np.array(pts[-1]); pts.append([AX, round(float(end[1] + abs(end[0] - AX) * 1.5), 2)])   # join the outlet axis
        lanes[k] = {"path": pts, "seat": seat, "dir": v.round(4).tolist()}
    Image.fromarray((~M * 255).astype(np.uint8)).save(D + f"build/hub_{h}_mask.png")
    out[h] = {"az": c["az"], "lanes": lanes, "outlet_end": c["outlet_end"], "out_ptfe": c["out_ptfe"]}
    print(h, {k: (len(v["path"]), v["path"][0], v["path"][-1]) for k, v in lanes.items()})
json.dump(out, open(D + "tools/hub_paths.json", "w"), indent=0)

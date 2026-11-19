# Move the BoxTurtle v1.0 hub (cad/bthub10_raw, from tools/export_bthub10.py) into the frame of the v1.1 hubs: a rigid fit
# (Kabsch) of the hardware both hubs share (bearing, D2HW switch body and its two levers, M3x10 screw) onto the v1.1
# load-only hub's. Writes cad/bthub10.{npz,json}. AGPL-3.0 (see LICENSE).
import numpy as np, json, os
D = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "")
r = np.load(D + "cad/bthub10_raw.npz"); rn = json.load(open(D + "cad/bthub10_raw.json"))
t = np.load(D + "cad/bthub_loadonly.npz"); tn = json.load(open(D + "cad/bthub_loadonly.json"))
PAIRS = [("Hardware033/MR63ZZ bearing020/MR63ZZ bearing004", "Hardware (13)/MR63ZZ bearing (5)016/MR63ZZ bearing (5)"),
         ("Hardware033/M3x10 SHCS008", "Hardware (13)/M3x10 SHCS (6)"),
         ("Omron D2HW-C201H008/Omron D2HW-C201H", "Omron D2HW-C201H (1)008/Omron D2HW-C201H (1)"),
         ("Omron D2HW-C201H008/Omron D2HW-C201H006", "Omron D2HW-C201H (1)008/Omron D2HW-C201H (1)006"),
         ("Omron D2HW-C201H008/Omron D2HW-C201H007", "Omron D2HW-C201H (1)008/Omron D2HW-C201H (1)007")]
def centre(z, names, key):
    i = [k for k, n in enumerate(names) if n.endswith(key)]; assert len(i) == 1, (key, i); V = z["p%03d_V" % i[0]]; return (V.min(0) + V.max(0)) / 2
A = np.array([centre(r, rn, a) for a, b in PAIRS]); B = np.array([centre(t, tn, b) for a, b in PAIRS])
ca, cb = A.mean(0), B.mean(0); U, S, Vt = np.linalg.svd((A - ca).T @ (B - cb)); d = np.sign(np.linalg.det(Vt.T @ U.T))
Rm = Vt.T @ np.diag([1, 1, d]) @ U.T; tr = cb - Rm @ ca
res = np.linalg.norm((A @ Rm.T + tr) - B, axis=1); print("fit residuals mm", res.round(3))
out = {}
for i, n in enumerate(rn):
    out["p%03d_V" % i] = (r["p%03d_V" % i].astype(float) @ Rm.T + tr).astype(np.float32); out["p%03d_F" % i] = r["p%03d_F" % i]
np.savez_compressed(D + "cad/bthub10.npz", **out); json.dump(rn, open(D + "cad/bthub10.json", "w"), indent=0)
print("rotation\n", Rm.round(4), "\ntranslation", tr.round(3))

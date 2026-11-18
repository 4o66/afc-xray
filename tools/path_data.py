# Filament path through the toolhead (deflected centerline, squeeze width at the gears, bore diameters), for the page.
# Writes build/path.json. AGPL-3.0 (see LICENSE). Geometry measured from the CAD in cad/.
import numpy as np, json, os
from scipy.interpolate import PchipInterpolator
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
# Balls push the filament to the far wall of the 2.4 mm guide bore; between the gears it sits midway between the hob roots
# (drive root r 3.627 about X 4.675, idler root r 3.672 about X -3.825, both at Z 86.31).
GZ = 86.31; DR = (4.675, 3.627); IR = (-3.825, 3.672)
ctrl = [(-9.0, 0), (66.1, 0), (76.19, -0.325), (GZ, (DR[0] - DR[1] + IR[0] + IR[1]) / 2), (99.12, -0.325), (105.8, 0), (150, 0)]
f = PchipInterpolator([c[0] for c in ctrl], [c[1] for c in ctrl])
z = np.round(np.arange(-9.0, 150.01, 0.1), 2); xc = f(z)
def gap(zz):
    dz = zz - GZ; g = np.full_like(zz, 9.0); m = np.abs(dz) < min(DR[1], IR[1])
    g[m] = (DR[0] - np.sqrt(DR[1] ** 2 - dz[m] ** 2)) - (IR[0] + np.sqrt(IR[1] ** 2 - dz[m] ** 2)); return g
w = np.minimum(1.75, gap(z))
cone = z < -6.5
b0 = np.full_like(z, 9.0); b0[(z >= -6.5) & (z < 3.5)] = 1.88; b0[(z >= 3.5) & (z < 20.5)] = 1.64; b0[(z >= 20.5) & (z < 35.1)] = 1.88
b0[cone] = np.interp(z[cone], [-9, -8.5, -8.0, -7.0, -6.5], [0.0, 0.28, 0.64, 1.8, 1.88]); w = np.minimum(w, b0)
bore = np.full_like(z, 2.4)                      # FilamATrix guide bore
bore[z >= 105.8] = 2.0                           # inside the bowden stub (2 mm ID)
bore[(z >= 39.5) & (z < 57.5)] = 2.0             # PTFE liner (2 mm ID, 18 mm)
bore[(z >= 57.5) & (z < 66.1)] = 2.88            # blade inserts
bore[(z >= 35.1) & (z < 39.5)] = 1.75            # heatsink bore above the heat break
bore[(z >= 20.5) & (z < 35.1)] = 1.88            # heat break
bore[(z >= 3.5) & (z < 20.5)] = 1.75             # block, UHF extension
bore[(z >= -6.5) & (z < 3.5)] = 1.88             # nozzle
bore[cone] = b0[cone]
json.dump(dict(px=14, xmin=-42.0, zmax=146.0, z0=-9.0, dz=0.1, xc=np.round(xc, 3).tolist(), w=np.round(w, 3).tolist(),
               bore=np.round(bore, 3).tolist()), open(os.path.join(ROOT, "build/path.json"), "w"))
print("path written")

# Cut the moving layers into sprites for one body x hotend combination, keeping only what is visible in that
# combination's full render, plus the spring occluder layer. Inputs from tools/section.py: build/<BODY>__<HOTEND>/ (base,
# full) and build/<BODY>/ (arm, slide, slide_olfa, guid, dgear, igear). Writes assets/<BODY>__<HOTEND>/. AGPL-3.0 (see LICENSE).
import numpy as np, json, os
from PIL import Image
from scipy.ndimage import binary_dilation
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
BODY = os.environ.get("BODY", "dual"); HOTEND = os.environ.get("HOTEND", "rapido_v2_uhf")
C = os.path.join(ROOT, "build", BODY + "__" + HOTEND) + "/"; M = os.path.join(ROOT, "build", BODY) + "/"
A = os.path.join(ROOT, "assets", BODY + "__" + HOTEND) + "/"; os.makedirs(A, exist_ok=True)
full = np.load(C + "depth_full.npy"); out = {}
for m in ["arm", "slide", "slide_olfa", "guid", "dgear", "igear"]:
    im = np.array(Image.open(M + f"layer_{m}.png")).astype(float); z = np.load(M + f"depth_{m}.npy")
    vis = (z <= full + 0.05) & np.isfinite(z)
    if m == "slide_olfa":    # the full render carries the LDO blade; let the Olfa layer show wherever the LDO slide layer did
        zl = np.load(M + "depth_slide.npy"); vis |= np.isfinite(z) & np.isfinite(zl) & (zl <= full + 0.05)
    im[..., 3] *= binary_dilation(vis, iterations=1)
    ys, xs = np.where(im[..., 3] > 0); x0, x1, y0, y1 = xs.min(), xs.max() + 1, ys.min(), ys.max() + 1
    Image.fromarray(im[y0:y1, x0:x1].astype(np.uint8), "RGBA").save(A + f"sprite_{m}.png"); out[m] = dict(x=int(x0), y=int(y0), w=int(x1 - x0), h=int(y1 - y0))
PX, xmin, zmax = 14, -42, 146     # static parts in front of the cutter spring (nearer than its front, Y 1.45), in its swept box
zb = np.load(C + "depth_base.npy"); base = np.array(Image.open(C + "layer_base.png").convert("RGBA"))
x0, x1 = int((-34.5 - xmin) * PX), int((-14.5 - xmin) * PX); y0, y1 = int((zmax - 60.5) * PX), int((zmax - 50.5) * PX)
mk = np.zeros(zb.shape, bool); mk[y0:y1, x0:x1] = zb[y0:y1, x0:x1] < 1.45
spr = base.copy(); spr[..., 3] = np.where(mk, 255, 0); ys, xs = np.where(mk); a, b, c, d = xs.min(), xs.max() + 1, ys.min(), ys.max() + 1
Image.fromarray(spr[c:d, a:b]).save(A + "sprite_socc.png"); out["socc"] = dict(x=int(a), y=int(c), w=int(b - a), h=int(d - c))
json.dump(out, open(A + "sprites.json", "w")); Image.open(C + "layer_base.png").convert("RGB").save(A + "base.webp", quality=90, method=6)
print("sprites", BODY, HOTEND)

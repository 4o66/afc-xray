# Cut the moving layers into sprites, keeping only what is visible in the full render, plus the spring occluder layer.
# Run after tools/section.py with MODE=base, full, arm, slide, guid, dgear, igear. Writes build/sprite_*.png, build/sprites.json,
# build/base.webp. AGPL-3.0 (see LICENSE).
import numpy as np, json, os
from PIL import Image
from scipy.ndimage import binary_dilation
B = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "build") + "/"
full = np.load(B + "depth_full.npy"); out = {}
for m in ["arm", "slide", "guid", "dgear", "igear"]:
    im = np.array(Image.open(B + f"layer_{m}.png")).astype(float); z = np.load(B + f"depth_{m}.npy")
    vis = (z <= full + 0.05) & np.isfinite(z); im[..., 3] *= binary_dilation(vis, iterations=1)
    ys, xs = np.where(im[..., 3] > 0); x0, x1, y0, y1 = xs.min(), xs.max() + 1, ys.min(), ys.max() + 1
    Image.fromarray(im[y0:y1, x0:x1].astype(np.uint8), "RGBA").save(B + f"sprite_{m}.png"); out[m] = dict(x=int(x0), y=int(y0), w=int(x1 - x0), h=int(y1 - y0))
# static parts in front of the cutter spring (nearer than its front, Y 1.45) inside its swept box
PX, xmin, zmax = 14, -42, 146
zb = np.load(B + "depth_base.npy"); base = np.array(Image.open(B + "layer_base.png").convert("RGBA"))
x0, x1 = int((-34.5 - xmin) * PX), int((-14.5 - xmin) * PX); y0, y1 = int((zmax - 60.5) * PX), int((zmax - 50.5) * PX)
mk = np.zeros(zb.shape, bool); mk[y0:y1, x0:x1] = zb[y0:y1, x0:x1] < 1.45
spr = base.copy(); spr[..., 3] = np.where(mk, 255, 0); ys, xs = np.where(mk); a, b, c, d = xs.min(), xs.max() + 1, ys.min(), ys.max() + 1
Image.fromarray(spr[c:d, a:b]).save(B + "sprite_socc.png"); out["socc"] = dict(x=int(a), y=int(c), w=int(b - a), h=int(d - c))
json.dump(out, open(B + "sprites.json", "w")); Image.open(B + "layer_base.png").convert("RGB").save(B + "base.webp", quality=90, method=6)
print("sprites", out)

# Turn the buffer section layers (build/buffer_<kind>/) into the page's assets (assets/buffer_<kind>/): the fixed base as WebP,
# the moving layer cropped to its visible pixels, and sprites.json. Usage: python tools/buffer_assets.py bt. AGPL-3.0 (see LICENSE).
import numpy as np, json, os, sys
from PIL import Image
from scipy.ndimage import binary_dilation
K = sys.argv[1]; D = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "")
META = {"bt": {"xmin": 192.0, "zmax": 48.0, "axisY": 18.2, "filFrom": 205.0}}[K]
B = D + f"build/buffer_{K}/"; A = D + f"assets/buffer_{K}/"; os.makedirs(A, exist_ok=True)
full = np.load(B + "depth_full.npy"); im = np.array(Image.open(B + "layer_slide.png")).astype(float); z = np.load(B + "depth_slide.npy")
vis = (z <= full + 0.05) & np.isfinite(z); im[..., 3] *= binary_dilation(vis, iterations=1)
ys, xs = np.where(im[..., 3] > 0); x0, x1, y0, y1 = xs.min(), xs.max() + 1, ys.min(), ys.max() + 1
Image.fromarray(im[y0:y1, x0:x1].astype(np.uint8), "RGBA").save(A + "sprite_slide.png")
Image.open(B + "layer_base.png").convert("RGB").save(A + "base.webp", quality=90, method=6)
W, H = Image.open(B + "layer_base.png").size
j = {"slide": dict(x=int(x0), y=int(y0), w=int(x1 - x0), h=int(y1 - y0)), "W": W, "H": H, **META}
if os.path.exists(B + "layer_bear.png"):   # hub sensor bearing (combo): lift = filament top - bearing bottom, from the CAD
    im = np.array(Image.open(B + "layer_bear.png")).astype(float); zb = np.load(B + "depth_bear.npy"); im[..., 3] *= binary_dilation((zb <= full + 0.05) & np.isfinite(zb), iterations=1)
    ys, xs = np.where(im[..., 3] > 0); bx0, bx1, by0, by1 = xs.min(), xs.max() + 1, ys.min(), ys.max() + 1
    Image.fromarray(im[by0:by1, bx0:bx1].astype(np.uint8), "RGBA").save(A + "sprite_bear.png"); j["bear"] = dict(x=int(bx0), y=int(by0), w=int(bx1 - bx0), h=int(by1 - by0), lift=2.38, y_mm=267.57)
json.dump(j, open(A + "sprites.json", "w"))
print("assets", K, W, H)

# Turn the buffer section layers (build/buffer_<kind>/) into the page's assets (assets/buffer_<kind>/): the fixed base as WebP,
# the moving layer cropped to its visible pixels, and sprites.json. Usage: python tools/buffer_assets.py bt. AGPL-3.0 (see LICENSE).
import numpy as np, json, os, sys
from PIL import Image
from scipy.ndimage import binary_dilation
K = sys.argv[1]; D = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "")
META = {"bt": {"xmin": 192.0, "zmax": 48.0, "axisY": 18.2, "filFrom": 205.0}, "tn": {"xmin": -20.0, "zmax": 132.0, "axisY": 115.9, "filFrom": -20.0}}[K]
B = D + f"build/buffer_{K}/"; A = D + f"assets/buffer_{K}/"; os.makedirs(A, exist_ok=True)
full = np.load(B + "depth_full.npy"); im = np.array(Image.open(B + "layer_slide.png")).astype(float); z = np.load(B + "depth_slide.npy")
# the moving layer is kept whole (masking it to what shows at the rest position would cut a permanent hole wherever a
# fixed part covers it there); the fixed parts that sit in front of it anywhere along its travel become an occluder
# layer the page draws on top of it
ys, xs = np.where(im[..., 3] > 0); x0, x1, y0, y1 = xs.min(), xs.max() + 1, ys.min(), ys.max() + 1
Image.fromarray(im[y0:y1, x0:x1].astype(np.uint8), "RGBA").save(A + "sprite_slide.png")
TRAVEL = {"bt": 10.0, "tn": -30.0}[K]; zb = np.load(B + "depth_base.npy"); mz = np.full(z.shape, np.inf)
for o in np.linspace(0, TRAVEL * 14, 41).round().astype(int):        # the slide drawn shifted o px along x
    sh = np.full(z.shape, np.inf)
    if o > 0: sh[:, o:] = z[:, :z.shape[1] - o]
    elif o < 0: sh[:, :o] = z[:, -o:]
    else: sh = z.copy()
    mz = np.minimum(mz, sh)
occ = np.isfinite(mz) & np.isfinite(zb) & (zb < mz - 0.05)
base_rgba = np.array(Image.open(B + "layer_base.png").convert("RGBA")).astype(float); base_rgba[..., 3] = occ * 255.0
OCC = None
if occ.any():
    oy, ox = np.where(occ); ox0, ox1, oy0, oy1 = ox.min(), ox.max() + 1, oy.min(), oy.max() + 1
    Image.fromarray(base_rgba[oy0:oy1, ox0:ox1].astype(np.uint8), "RGBA").save(A + "sprite_occ.png")
    OCC = dict(x=int(ox0), y=int(oy0), w=int(ox1 - ox0), h=int(oy1 - oy0))
Image.open(B + "layer_base.png").convert("RGB").save(A + "base.webp", **({"lossless": True} if os.environ.get("MASK") == "1" else {"quality": 90, "method": 6}))
W, H = Image.open(B + "layer_base.png").size
j = {"slide": dict(x=int(x0), y=int(y0), w=int(x1 - x0), h=int(y1 - y0)), "W": W, "H": H, **META}
if OCC: j["occ"] = OCC
# TurtleNeck switches: lever (rotates about its hinge) and button (pushed in) per switch; R = trailing, L = advance.
# Hinge points from the CAD: the right switch's lever is hinged at its left end, the left switch's at its right end.
if K == "tn":
    PIV = {"R": (49.95, 105.45), "L": (31.25, 105.45)}
    for m, kind in (("levR", "lev"), ("levL", "lev"), ("btnR", "btn"), ("btnL", "btn")):
        if not os.path.exists(B + f"layer_{m}.png"): continue
        im = np.array(Image.open(B + f"layer_{m}.png")).astype(float); ys, xs = np.where(im[..., 3] > 0)
        bx0, bx1, by0, by1 = xs.min(), xs.max() + 1, ys.min(), ys.max() + 1
        Image.fromarray(im[by0:by1, bx0:bx1].astype(np.uint8), "RGBA").save(A + f"sprite_{m}.png")
        e = dict(x=int(bx0), y=int(by0), w=int(bx1 - bx0), h=int(by1 - by0)); side = m[-1]
        if kind == "lev": px, py = PIV[side]; e.update(px=round((px - META["xmin"]) * 14, 1), py=round((META["zmax"] - py) * 14, 1), sign=1 if side == "R" else -1, deg=10.0)
        else: e.update(dy=0.6 * 14)
        j[m] = e
if os.path.exists(B + "layer_bear.png"):   # the combo's sensor bearing, whole; it rises straight up 2.375 mm onto the filament
    im = np.array(Image.open(B + "layer_bear.png")).astype(float)
    ys, xs = np.where(im[..., 3] > 0); bx0, bx1, by0, by1 = xs.min(), xs.max() + 1, ys.min(), ys.max() + 1
    Image.fromarray(im[by0:by1, bx0:bx1].astype(np.uint8), "RGBA").save(A + "sprite_bear.png")
    j["bear"] = dict(x=int(bx0), y=int(by0), w=int(bx1 - bx0), h=int(by1 - by0), lift=2.375, dx=0.0, dy=-2.375 * 14, y_mm=267.57)
json.dump(j, open(A + "sprites.json", "w"))
print("assets", K, W, H)

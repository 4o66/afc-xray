# Render both BoxTurtle v1.1 hubs, top and side views, and cut the page assets into assets/hub_<hub>_<view>/:
# base.webp (fixed parts, cut), sprite_slide.png (the combo's sliding outlet block, cut, masked to what is visible),
# sprite_over.png / sprite_overslide.png (top view only: switches and trigger above the cut plane, uncut, for a translucent
# overlay) and sprites.json. Usage: PY=python3 python tools/hub_assets.py. AGPL-3.0 (see LICENSE).
import numpy as np, json, os, subprocess, sys
from PIL import Image
from scipy.ndimage import binary_dilation
D = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "")
def run(env): subprocess.run([sys.executable, D + "tools/hub_section.py"], env={**os.environ, **env}, check=True, stdout=subprocess.DEVNULL)
def crop(im, mask=None):
    im = np.array(im).astype(float)
    if mask is not None: im[..., 3] *= mask
    ys, xs = np.where(im[..., 3] > 0)
    if not len(xs): return None, None
    x0, x1, y0, y1 = xs.min(), xs.max() + 1, ys.min(), ys.max() + 1
    return Image.fromarray(im[y0:y1, x0:x1].astype(np.uint8), "RGBA"), dict(x=int(x0), y=int(y0), w=int(x1 - x0), h=int(y1 - y0))
import shutil; shutil.copy(D + "tools/hub_paths.json", D + "assets/hub_paths.json")   # the page reads the filament paths from here
for hub in ("combo", "loadonly"):
    for view in ("top", "side"):
        modes = ["base"] + (["full", "slide"] if hub == "combo" else ["full"] if view == "side" else []) + (["over"] + (["overslide"] if hub == "combo" else []) if view == "top" else ["bear"])
        for m in modes: run({"HUB": hub, "VIEW": view, "MODE": m})
        B = D + f"build/hub_{hub}_{view}/"; A = D + f"assets/hub_{hub}_{view}/"; os.makedirs(A, exist_ok=True)
        Image.open(B + "layer_base.png").convert("RGB").save(A + "base.webp", quality=90, method=6)
        W, H = Image.open(B + "layer_base.png").size; j = {"W": W, "H": H, "view": view, "xmin": 192.0, "zmax": 48.0 if view == "side" else -122.0}
        if "slide" in modes:
            full = np.load(B + "depth_full.npy"); z = np.load(B + "depth_slide.npy"); vis = (z <= full + 0.05) & np.isfinite(z)
            im, j["slide"] = crop(Image.open(B + "layer_slide.png"), binary_dilation(vis, iterations=1)); im.save(A + "sprite_slide.png")
        if "bear" in modes:   # hub sensor bearing: lift = filament top - bearing bottom, from the CAD
            full = np.load(B + "depth_full.npy"); zb = np.load(B + "depth_bear.npy")
            im, j["bear"] = crop(Image.open(B + "layer_bear.png"), binary_dilation((zb <= full + 0.05) & np.isfinite(zb), iterations=1)); im.save(A + "sprite_bear.png")
            j["bear"].update({"lift": 2.38, "y_mm": 267.57} if hub == "combo" else {"lift": 2.48, "y_mm": 242.3})
        for m in ("over", "overslide"):
            if m in modes:
                im, box = crop(Image.open(B + f"layer_{m}.png"))
                if im: im.save(A + f"sprite_{m}.png"); j[m] = box
        json.dump(j, open(A + "sprites.json", "w")); print(hub, view, modes, flush=True)

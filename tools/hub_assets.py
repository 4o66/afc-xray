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
def sensor_travel(hub, view):
    """The sensor bearing rests in a slot whose line runs from the filament axis through the bearing's centre (straight
    up on the combo, 45 degrees off vertical on the v1.0 and load-only hubs). With filament under it, it moves out along
    that line until it touches the filament: travel = bearing radius + filament radius - its centre's distance from
    the axis. Returned as the move in this view's pixels, the travel in mm and the bearing's position along the axis."""
    src = {"combo": "btcombo", "loadonly": "bthub_loadonly", "v10": "bthub10"}[hub]; P = json.load(open(D + "tools/hub_paths.json"))[hub]
    z = np.load(D + f"cad/{src}.npz"); N = json.load(open(D + f"cad/{src}.json"))
    V = np.concatenate([z["p%03d_V" % i] for i, n in enumerate(N) if "bearing" in n.lower()]).astype(float)
    c = (V.min(0) + V.max(0)) / 2; r = (V[:, 2].max() - V[:, 2].min()) / 2
    v = np.array([c[0] - P["outlet"]["shoulder"][0], c[2] - P["az"]]); d0 = np.linalg.norm(v); u = v / d0; t = r + 0.875 - d0
    dx, dy = (0.0, -t * u[1] * 14) if view == "side" else (0.0, t * u[0] * 14)
    return {"lift": round(float(t), 3), "dx": round(dx, 2), "dy": round(dy, 2), "y_mm": round(float(c[1]), 2), "angle_deg": round(float(np.degrees(np.arctan2(u[0], u[1]))), 1)}
def switch_lever(m):
    """Hinge (pivot, in top-view pixels) and press direction of a combo buffer switch lever: its two ends along its length
    (Y); the tip is the end raised further toward the outlet axis (+X), the hinge the other. Pressed, the tip swings
    toward the switch body (-X), about 8 degrees, as the TurtleNeck's levers do."""
    z = np.load(D + "cad/btcombo.npz"); N = json.load(open(D + "cad/btcombo.json")); key = {"levT": "D2F-L v1/", "levA": "D2F-L v002/"}[m]
    V = np.concatenate([z["p%03d_V" % i] for i, n in enumerate(N) if key in n and "D2F_Hinge" in n]).astype(float)
    y0, y1 = V[:, 1].min(), V[:, 1].max(); e0 = V[V[:, 1] < y0 + 1.0]; e1 = V[V[:, 1] > y1 - 1.0]
    tip, hinge = (e0, e1) if e0[:, 0].max() > e1[:, 0].max() else (e1, e0)
    hx, hy = float(hinge[:, 1].mean()), float(hinge[:, 0].min()); tx, ty = float(tip[:, 1].mean()), float(tip[:, 0].max())
    px_, py_ = (hx - 192) * 14, (hy - 122) * 14; dx = (tx - hx) * 14
    return {"cx": round(px_, 2), "cy": round(py_, 2), "press_deg": round(float(-np.sign(dx) * 8.0), 1)}   # tip up the screen
for hub in ("combo", "loadonly", "v10"):
    for view in ("top", "side"):
        modes = ["base"] + (["full", "slide"] if hub == "combo" else ["full"] if view == "side" else []) + (["over"] + (["overslide", "hwfix", "hwslide", "levT", "levA", "btnT", "btnA"] if hub == "combo" else []) if view == "top" else []) + ["bear"]
        for m in modes: run({"HUB": hub, "VIEW": view, "MODE": m})
        B = D + f"build/hub_{hub}_{view}/"; A = D + f"assets/hub_{hub}_{view}/"; os.makedirs(A, exist_ok=True)
        Image.open(B + "layer_base.png").convert("RGB").save(A + "base.webp", quality=90, method=6)
        W, H = Image.open(B + "layer_base.png").size; j = {"W": W, "H": H, "view": view, "xmin": 192.0, "zmax": 48.0 if view == "side" else -122.0}
        if "slide" in modes:
            full = np.load(B + "depth_full.npy"); z = np.load(B + "depth_slide.npy"); vis = (z <= full + 0.05) & np.isfinite(z)
            im, j["slide"] = crop(Image.open(B + "layer_slide.png"), binary_dilation(vis, iterations=1)); im.save(A + "sprite_slide.png")
        if "bear" in modes:   # the sensor bearing, whole; its travel along its slot when filament is under it
            im, j["bear"] = crop(Image.open(B + "layer_bear.png")); im.save(A + "sprite_bear.png"); j["bear"].update(sensor_travel(hub, view))
        for m in ("levT", "levA", "btnT", "btnA"):   # combo buffer switches: whole layers, the lever pivoting about its hinge
            if m not in modes: continue
            im, box = crop(Image.open(B + f"layer_{m}.png"))
            if im is None: continue
            im.save(A + f"sprite_{m}.png"); j[m] = box
            if m.startswith("lev"): j[m].update(switch_lever(m))
            else: j[m].update(dy=round(-0.6 * 14, 2))   # pushed in toward the switch body (-X: up the screen)
        for m in ("over", "overslide", "hwfix", "hwslide"):
            if m in modes:
                im, box = crop(Image.open(B + f"layer_{m}.png"))
                if im: im.save(A + f"sprite_{m}.png"); j[m] = box
        json.dump(j, open(A + "sprites.json", "w")); print(hub, view, modes, flush=True)

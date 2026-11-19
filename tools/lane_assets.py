# Render every BoxTurtle lane version and view with tools/lane_section.py and cut the page assets into
# assets/lane_<VER>_<VIEW>/: base.webp (fixed parts, cut), sprite_<group>.png for the moving and see-through groups, and
# sprites.json (CAD-to-pixel mapping, sprite boxes, pivots and motions, the filament path in pixels with its 3D arc length).
# Also writes assets/lane_paths.json (the 3D filament path per version, events, drive grip radius and gear ratio).
# Usage: python tools/lane_assets.py [VER ...]. CHECK=<dir> also writes composites at the empty and filament-present
# positions there. AGPL-3.0 (see LICENSE).
import numpy as np, json, os, subprocess, sys
from PIL import Image, ImageDraw
from scipy.ndimage import binary_dilation
D = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "")
VERS = sys.argv[1:] or ["v11", "v11bmg", "v11proto", "v10"]
MODES = {"ext": ["base", "full", "dgear", "igear", "bear", "over"], "spool": ["base", "full", "trig", "over", "overmove"]}
FIL_R = 0.875
def run(env): subprocess.run([sys.executable, D + "tools/lane_section.py"], env={**os.environ, **env}, check=True, stdout=subprocess.DEVNULL)
def crop(im, mask=None):
    im = np.array(im).astype(float)
    if mask is not None: im[..., 3] *= mask
    ys, xs = np.where(im[..., 3] > 0)
    if not len(xs): return None, None
    x0, x1, y0, y1 = xs.min(), xs.max() + 1, ys.min(), ys.max() + 1
    return Image.fromarray(im[y0:y1, x0:x1].astype(np.uint8), "RGBA"), dict(x=int(x0), y=int(y0), w=int(x1 - x0), h=int(y1 - y0))
paths_out = json.load(open(D + "assets/lane_paths.json")) if os.path.exists(D + "assets/lane_paths.json") else {}
for ver in VERS:
    for view in ("spool", "ext"):
        for m in MODES[view]: run({"VER": ver, "VIEW": view, "MODE": m})
        B = D + f"build/lane_{ver}_{view}/"; A = D + f"assets/lane_{ver}_{view}/"; os.makedirs(A, exist_ok=True)
        G = json.load(open(B + "geom.json")); vw = G["view"]
        O, U, V = (np.array(vw[k]) for k in ("O", "U", "V")); px = vw["px"]; xmin, vmax = vw["xmin"], vw["vmax"]
        def topx(P): P = np.atleast_2d(P) - O; return np.c_[(P @ U - xmin) * px, (vmax - P @ V) * px]
        Image.open(B + "layer_base.png").convert("RGB").save(A + "base.webp", quality=90, method=6)
        W, H = Image.open(B + "layer_base.png").size
        j = {"W": W, "H": H, "px": px, "view": view, "O": vw["O"], "U": vw["U"], "V": vw["V"], "xmin": xmin, "vmax": vmax,
             "u0": xmin, "v0": vmax, "map": "x_px = ((P - O).U - xmin) * px; y_px = (vmax - (P - O).V) * px  (P in CAD mm)"}
        full = np.load(B + "depth_full.npy")
        for g in [m for m in MODES[view] if m not in ("base", "full")]:
            im = Image.open(B + f"layer_{g}.png")
            if g in ("over", "bear"): spr, box = crop(im)   # see-through layer, and the uncut sensor bearing: whole
            elif g == "overmove":   # only the depressor leg where it meets the prep switch, 3 mm either side of the switch
                z0, z1 = G["spool"]["d2f_z"]; rows = np.zeros((H, W)); a_, b_ = int((vmax - (z1 + 3 - O @ V)) * px), int((vmax - (z0 - 3 - O @ V)) * px)
                rows[max(a_, 0):max(b_, 0)] = 1; spr, box = crop(im, rows)
            else:
                z = np.load(B + f"depth_{g}.npy"); spr, box = crop(im, binary_dilation((z <= full + 0.05) & np.isfinite(z), iterations=1))
            if spr is None: continue
            spr.save(A + f"sprite_{g}.png"); j[g] = box
        if view == "ext":
            e = G["ext"]
            for g in ("dgear", "igear"):
                if g not in j: continue
                gc = e["gears"][g]; c = topx(gc["c"])[0]; r = abs(gc["uv"][1]) - FIL_R
                # filament moving +U (left to right): the gear above the line turns counterclockwise on screen, the one
                # below clockwise; canvas angles are clockwise-positive
                j[g].update(cx=round(float(c[0]), 2), cy=round(float(c[1]), 2), r_grip_mm=round(r, 3),
                            canvas_deg_per_mm=round((-1 if gc["uv"][1] > 0 else 1) * 180 / np.pi / r, 4))
            if "bear" in j:
                b = e["bearing"]; d = np.array(b["dir"]) * b["lift_mm"]
                j["bear"].update(dx_px=round(float(d @ U * px), 2), dy_px=round(float(-(d @ V) * px), 2), lift_mm=round(b["lift_mm"], 3),
                                 lift_out_of_plane_mm=round(float(d @ np.array(vw["N"])), 3))
        else:
            sp = G["spool"]; piv = np.array(sp["pivot"]); th = sp["trig_rot_rad_about_x"]; mr = np.array(sp["moving_roller"])
            c = topx(piv)[0]; p0 = topx(mr)[0]
            m2 = mr - piv; ct, st = np.cos(th), np.sin(th); p1 = topx(piv + np.array([m2[0], ct * m2[1] - st * m2[2], st * m2[1] + ct * m2[2]]))[0]
            ang = np.degrees(np.arctan2(p1[1] - c[1], p1[0] - c[0]) - np.arctan2(p0[1] - c[1], p0[0] - c[0]))
            for g in ("trig", "overmove"):
                if g in j: j[g].update(cx=round(float(c[0]), 2), cy=round(float(c[1]), 2), angle_deg_with_filament=round(float(ang), 3))
        # filament centre line in pixels, resampled every 0.5 mm of 3D path, kept where it is inside the image
        pts = np.array(G["path"]["pts"]); s = np.array(G["path"]["s"]); ss = np.r_[np.arange(0, s[-1], 0.5), s[-1]]
        P3 = np.array([np.interp(ss, s, pts[:, k]) for k in range(3)]).T; Q = topx(P3)
        ins = (Q[:, 0] >= -2) & (Q[:, 0] <= W + 2) & (Q[:, 1] >= -2) & (Q[:, 1] <= H + 2)
        idx = np.where(ins)[0]; runs = np.split(idx, np.where(np.diff(idx) > 1)[0] + 1); run_ = max(runs, key=len)
        j["path"] = [[round(float(x), 1), round(float(y), 1)] for x, y in Q[run_]]; j["s_mm"] = [round(float(v), 2) for v in ss[run_]]
        j["events"] = {k: round(v, 2) for k, v in G["path"]["events"].items()}
        json.dump(j, open(A + "sprites.json", "w"))
        print(ver, view, W, H, sorted(k for k in j if isinstance(j[k], dict) and "w" in j[k]), flush=True)
        if os.environ.get("CHECK"):   # composites: empty (CAD) and filament present
            C = os.environ["CHECK"]; os.makedirs(C, exist_ok=True)
            for state in ("empty", "loaded"):
                im = Image.open(A + "base.webp").convert("RGBA")
                for g in [m for m in MODES[view] if m not in ("base", "full")]:
                    if g not in j: continue
                    spr = Image.open(A + f"sprite_{g}.png"); bx = j[g]; x, y = bx["x"], bx["y"]
                    if g in ("over", "overmove"):
                        a = np.array(spr); a[..., 3] = (a[..., 3] * 0.45).astype(np.uint8); spr = Image.fromarray(a)
                    if state == "loaded" and "angle_deg_with_filament" in bx:
                        # rotate about the pivot: pad the sprite onto a canvas centred on the pivot
                        cx, cy = bx["cx"] - x, bx["cy"] - y; R = int(np.ceil(max(np.hypot(cx - a_, cy - b_) for a_ in (0, bx["w"]) for b_ in (0, bx["h"])))) + 2
                        cv = Image.new("RGBA", (2 * R, 2 * R)); cv.paste(spr, (int(round(R - cx)), int(round(R - cy))))
                        spr = cv.rotate(-bx["angle_deg_with_filament"], resample=Image.BICUBIC, center=(R, R)); x, y = int(round(bx["cx"] - R)), int(round(bx["cy"] - R))
                    if state == "loaded" and g == "bear": x, y = int(round(x + bx["dx_px"])), int(round(y + bx["dy_px"]))
                    im.alpha_composite(spr, (x, y)) if x >= 0 and y >= 0 else im.paste(spr, (x, y), spr)
                if state == "loaded":
                    dr = ImageDraw.Draw(im); dr.line([tuple(p) for p in j["path"]], fill=(47, 174, 79, 230), width=int(2 * FIL_R * px), joint="curve")
                    for k, v in j["events"].items():
                        i = int(np.argmin(np.abs(np.array(j["s_mm"]) - v)))
                        if abs(j["s_mm"][i] - v) < 0.6: x_, y_ = j["path"][i]; dr.ellipse([x_ - 5, y_ - 5, x_ + 5, y_ + 5], outline=(255, 200, 0, 255), width=2); dr.text((x_ + 7, y_ - 7), k, fill=(255, 140, 0, 255))
                    for g in ("dgear", "igear", "trig"):
                        if g in j: cx, cy = j[g]["cx"], j[g]["cy"]; dr.line([cx - 8, cy, cx + 8, cy], fill="cyan", width=2); dr.line([cx, cy - 8, cx, cy + 8], fill="cyan", width=2)
                im.convert("RGB").save(f"{C}/lane_{ver}_{view}_{state}.png")
    g = json.load(open(D + f"build/lane_{ver}_ext/geom.json"))
    paths_out[ver] = {"pts": [[round(v, 3) for v in p] for p in g["path"]["pts"]], "s": [round(v, 3) for v in g["path"]["s"]],
                      "events": {k: round(v, 3) for k, v in g["path"]["events"].items()},
                      "r_grip_mm": round(g["drive"]["r_grip_mm"], 3), "drive_centre_to_line_mm": round(g["drive"]["centre_to_line_mm"], 3),
                      "ratio_motor_to_drive": round(g["drive"]["ratio_motor_to_drive"], 4), "gear_train": g["drive"]["train"],
                      "inferred_tube": g["tube"], "trig_rot_deg": round(float(np.degrees(g["spool"]["trig_rot_rad_about_x"])), 3),
                      "load_bearing_lift_mm": round(g["ext"]["bearing"]["lift_mm"], 3)}
json.dump(paths_out, open(D + "assets/lane_paths.json", "w"), indent=1)

# Render every BoxTurtle lane version and view with tools/lane_section.py and cut the page assets into
# assets/lane_<VER>_<VIEW>/: base.webp (fixed parts, cut), sprite_<group>.png for the moving and see-through groups, and
# sprites.json (CAD-to-pixel mapping, sprite boxes, pivots and motions, the filament path in pixels with its 3D arc length).
# In the ext view sprites.json also has "spin": the rest of the turning drive train (gears and ball bearings other than
# dgear/igear), back to front, each {name, x, y, w, h, cx, cy, canvas_deg_per_mm, see, file}. Draw order: base, the
# see=false entries (cut parts, opaque, each followed by a non-turning "_front" patch of the base that sits in front of it),
# dgear, igear, bear, over, then the see=true entries (from the see-through layer, at its opacity).
# Also writes assets/lane_paths.json (the 3D filament path per version, events, drive grip radius and gear ratio).
# Usage: python tools/lane_assets.py [VER ...]. CHECK=<dir> also writes composites at the empty and filament-present
# positions there, and spin_<VER>_{0,q}.png: the ext view with every turning part at rest and after a quarter turn
# of the drive gear. AGPL-3.0 (see LICENSE).
import numpy as np, json, os, subprocess, sys
from PIL import Image, ImageDraw
from scipy.ndimage import binary_dilation
D = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "")
VERS = sys.argv[1:] or ["v11", "v11bmg", "v11proto", "v10"]
MODES = {"ext": ["base", "full", "dgear", "igear", "bear", "over"], "spool": ["base", "full", "trig", "lever", "over", "overmove"]}
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
        B = D + f"build/lane_{ver}_{view}/"; A = D + f"assets/lane_{ver}_{view}/"; os.makedirs(A, exist_ok=True)
        run({"VER": ver, "VIEW": view, "MODE": "geom"}); SP = json.load(open(B + "geom.json")).get("spin", [])
        spin_modes = [s["mode"] for s in SP] + [s["mode"] + "_see" for s in SP if s["see_parts"]]
        for m in MODES[view] + spin_modes: run({"VER": ver, "VIEW": view, "MODE": m})
        for f in os.listdir(A):   # drop sprites left from an earlier grouping
            if f.startswith("sprite_spin_"): os.remove(A + f)
        G = json.load(open(B + "geom.json")); vw = G["view"]
        O, U, V = (np.array(vw[k]) for k in ("O", "U", "V")); px = vw["px"]; xmin, vmax = vw["xmin"], vw["vmax"]
        def topx(P): P = np.atleast_2d(P) - O; return np.c_[(P @ U - xmin) * px, (vmax - P @ V) * px]
        Image.open(B + "layer_base.png").convert("RGB").save(A + "base.webp", quality=90, method=6)
        W, H = Image.open(B + "layer_base.png").size
        j = {"W": W, "H": H, "px": px, "view": view, "O": vw["O"], "U": vw["U"], "V": vw["V"], "xmin": xmin, "vmax": vmax,
             "u0": xmin, "v0": vmax, "map": "x_px = ((P - O).U - xmin) * px; y_px = (vmax - (P - O).V) * px  (P in CAD mm)"}
        full = np.load(B + "depth_full.npy")
        # the see-through layer used to be one z-buffered render: where a turning see-through part sat in front of another
        # see-through part, only the near one showed. Keep that with hold-outs that do not change as the part turns: inside
        # the near part's outer circle (tip circle, outer race), drop the pixels of the over layer, and of any part on the same
        # axis, that lie behind the near part's nearest point; the bore (inside the part's smallest radius) stays open. Parts
        # on other axes are left to overlap.
        yy, xx = np.mgrid[0:H, 0:W] + 0.5; seeinfo = []
        if os.path.exists(B + "depth_base.npy"): zbase = np.load(B + "depth_base.npy"); base_rgba = Image.open(A + "base.webp").convert("RGBA")   # the patch must match the base as the page shows it
        for sg in SP:
            if sg["mode"] + "_see" not in spin_modes: continue
            z = np.load(B + f"depth_{sg['mode']}_see.npy"); fin = np.isfinite(z)
            if not fin.any(): continue
            rr = np.hypot(xx - (sg["uv"][0] - xmin) * px, yy - (vmax - sg["uv"][1]) * px)
            disk = (rr <= sg["r_out_mm"] * px + 1) & (rr > rr[fin].min() + 0.5)
            seeinfo.append((sg["mode"], sg, disk, float(z[fin].min())))
        def holdout(z, sg=None):
            keep = np.ones((H, W))
            for m2, sg2, disk2, zmin2 in seeinfo:
                if sg is not None and (m2 == sg["mode"] or np.hypot(*np.subtract(sg["uv"], sg2["uv"])) > 0.3): continue
                keep[disk2 & (z > zmin2)] = 0
            return keep
        for g in [m for m in MODES[view] if m not in ("base", "full")]:
            im = Image.open(B + f"layer_{g}.png")
            if g == "over": spr, box = crop(im, holdout(np.load(B + "depth_over.npy")))   # see-through layer: whole, less the hold-outs
            elif g in ("bear", "lever"): spr, box = crop(im)   # the uncut sensor bearing, the prep lever: whole
            elif g == "overmove":   # only the depressor leg where it meets the prep switch, 3 mm either side of the switch
                z0, z1 = G["spool"]["d2f_z"]; rows = np.zeros((H, W)); a_, b_ = int((vmax - (z1 + 3 - O @ V)) * px), int((vmax - (z0 - 3 - O @ V)) * px)
                rows[max(a_, 0):max(b_, 0)] = 1; spr, box = crop(im, rows)
            else:
                z = np.load(B + f"depth_{g}.npy"); spr, box = crop(im, binary_dilation((z <= full + 0.05) & np.isfinite(z), iterations=1))
            if spr is None: continue
            spr.save(A + f"sprite_{g}.png"); j[g] = box
        spin = []
        for sg in SP:
            for m, see in ((sg["mode"], False), (sg["mode"] + "_see", True)):
                if m not in spin_modes: continue
                im = Image.open(B + f"layer_{m}.png")
                if see: spr, box = crop(im, holdout(np.load(B + f"depth_{m}.npy"), sg))   # as the over layer draws it: whole, less the hold-outs
                else:   # as the base draws it, cut: whole, so it can turn behind a window in the base; the static base parts in
                        # front of it, inside its outer circle, are put back over it by a non-turning "<name>_front" patch
                    z = np.load(B + f"depth_{m}.npy"); fin = np.isfinite(z)
                    vis = (z <= full + 0.05) & fin
                    if vis.sum() < 4: continue    # hidden at rest: the base never showed it
                    spr, box = crop(im); zmin = float(z[fin].min())
                    # the part's nearest depth on each 1 px ring about its axis does not change as it turns: a base pixel nearer
                    # than that ring depth is in front of the part at every angle (rings the part never covers: no patch)
                    rr = np.hypot(xx - (sg["uv"][0] - xmin) * px, yy - (vmax - sg["uv"][1]) * px); ri = np.round(rr).astype(int)
                    zring = np.full(ri.max() + 2, np.inf); np.minimum.at(zring, ri[fin], z[fin]); zring[~np.isfinite(zring)] = -np.inf
                    occ = binary_dilation((rr <= sg["r_out_mm"] * px + 1) & (zbase < zring[ri] - 1e-3), iterations=1)
                if spr is None or box["w"] * box["h"] < 4 or np.array(spr)[..., 3].sum() < 255 * 4: continue
                name = m[5:]; spr.save(A + f"sprite_{m}.png")
                key = -(sg["see_depth"] or 0.0) if see else -zmin
                spin.append((see, key, 0, dict(name=name, **box, file=f"sprite_{m}.png", sg=sg, see=see)))
                if not see and occ.any():
                    fs, fb = crop(base_rgba, occ)
                    fs.save(A + f"sprite_{m}_front.png")
                    spin.append((see, key, 1, dict(name=name + "_front", **fb, file=f"sprite_{m}_front.png", sg=dict(sg, mult=0.0), see=see)))
        # cut parts first (each followed by its front patch), then the see-through ones; each set far to near
        spin.sort(key=lambda t: (t[0], t[1], t[2])); spin = [(a, b, d) for a, b, c, d in spin]
        if view == "ext":
            e = G["ext"]
            for g in ("dgear", "igear"):
                if g not in j: continue
                gc = e["gears"][g]; c = topx(gc["c"])[0]; r = abs(gc["uv"][1]) - FIL_R
                # filament moving +U (left to right): the gear above the line turns counterclockwise on screen, the one
                # below clockwise; canvas angles are clockwise-positive
                j[g].update(cx=round(float(c[0]), 2), cy=round(float(c[1]), 2), r_grip_mm=round(r, 3),
                            canvas_deg_per_mm=round((-1 if gc["uv"][1] > 0 else 1) * 180 / np.pi / r, 4))
            for _, _, sp in spin:
                sg = sp.pop("sg"); cu, cv = sg["uv"]
                # rate: the reference gear's rate times the train multiplier (sign flips per mesh); same convention as dgear
                sp.update(cx=round((cu - xmin) * px, 2), cy=round((vmax - cv) * px, 2),
                          canvas_deg_per_mm=round(j[sg["ref"]]["canvas_deg_per_mm"] * sg["mult"], 4) + 0.0, ref=sg["ref"], mult=round(sg["mult"], 4))
            j["spin"] = [dict(name=sp["name"], x=sp["x"], y=sp["y"], w=sp["w"], h=sp["h"], cx=sp["cx"], cy=sp["cy"],
                              canvas_deg_per_mm=sp["canvas_deg_per_mm"], see=sp["see"], file=sp["file"], ref=sp["ref"], mult=sp["mult"]) for _, _, sp in spin]
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
            if "lever" in j:   # pressed in by the trigger arm when the lane is empty (the CAD shows them about 2 mm into each other)
                lv = sp["lever"]; h_, t_, b_ = topx(np.array(lv["hinge"]))[0], topx(np.array(lv["tip"]))[0], topx(np.array(lv["body"]))[0]
                L_ = np.hypot(*(t_ - h_)) / px; cr = (t_[0] - h_[0]) * (b_[1] - h_[1]) - (t_[1] - h_[1]) * (b_[0] - h_[0])
                j["lever"].update(cx=round(float(h_[0]), 2), cy=round(float(h_[1]), 2), press_deg=round(float(np.sign(cr) * np.degrees(np.arctan2(lv["press_mm"], L_))), 3))
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
            if view == "ext":   # every turning part at rest (0) and after a quarter turn of the drive gear (q)
                def rot(spr, bx, deg):
                    cx, cy = bx["cx"] - bx["x"], bx["cy"] - bx["y"]; R = int(np.ceil(max(np.hypot(cx - a_, cy - b_) for a_ in (0, bx["w"]) for b_ in (0, bx["h"])))) + 2
                    cv = Image.new("RGBA", (2 * R, 2 * R)); cv.paste(spr, (int(round(R - cx)), int(round(R - cy))))
                    return cv.rotate(-deg, resample=Image.BICUBIC, center=(R, R)), (int(round(bx["cx"] - R)), int(round(bx["cy"] - R)))
                def put(im, spr, xy):
                    lay = Image.new("RGBA", im.size); lay.paste(spr, xy); im.alpha_composite(lay)
                def see(spr):
                    a = np.array(spr); a[..., 3] = (a[..., 3] * 0.45).astype(np.uint8); return Image.fromarray(a)
                for tag, mm in (("0", 0.0), ("q", 90.0 / abs(j["dgear"]["canvas_deg_per_mm"]))):
                    im = Image.open(A + "base.webp").convert("RGBA")
                    for sp in [s for s in j["spin"] if not s["see"]]: put(im, *rot(Image.open(A + sp["file"]), sp, sp["canvas_deg_per_mm"] * mm))
                    for g in ("dgear", "igear"):
                        if g in j: put(im, *rot(Image.open(A + f"sprite_{g}.png"), j[g], j[g]["canvas_deg_per_mm"] * mm))
                    if "bear" in j: put(im, Image.open(A + "sprite_bear.png"), (j["bear"]["x"], j["bear"]["y"]))
                    if "over" in j: put(im, see(Image.open(A + "sprite_over.png")), (j["over"]["x"], j["over"]["y"]))
                    for sp in [s for s in j["spin"] if s["see"]]: put(im, *rot(see(Image.open(A + sp["file"])), sp, sp["canvas_deg_per_mm"] * mm))
                    if tag == "q":
                        dr = ImageDraw.Draw(im)
                        for sp in j["spin"]: cx, cy = sp["cx"], sp["cy"]; dr.line([cx - 6, cy, cx + 6, cy], fill="magenta", width=2); dr.line([cx, cy - 6, cx, cy + 6], fill="magenta", width=2)
                    im.convert("RGB").save(f"{C}/spin_{ver}_{tag}.png")
    g = json.load(open(D + f"build/lane_{ver}_ext/geom.json"))
    paths_out[ver] = {"pts": [[round(v, 3) for v in p] for p in g["path"]["pts"]], "s": [round(v, 3) for v in g["path"]["s"]],
                      "events": {k: round(v, 3) for k, v in g["path"]["events"].items()},
                      "r_grip_mm": round(g["drive"]["r_grip_mm"], 3), "drive_centre_to_line_mm": round(g["drive"]["centre_to_line_mm"], 3),
                      "ratio_motor_to_drive": round(g["drive"]["ratio_motor_to_drive"], 4), "gear_train": g["drive"]["train"],
                      "inferred_tube": g["tube"], "trig_rot_deg": round(float(np.degrees(g["spool"]["trig_rot_rad_about_x"])), 3),
                      "load_bearing_lift_mm": round(g["ext"]["bearing"]["lift_mm"], 3)}
json.dump(paths_out, open(D + "assets/lane_paths.json", "w"), indent=1)

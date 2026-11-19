# AFC X-ray

**Live page: https://4o66.github.io/afc-xray/**

Animated, narrated, to-scale sections of what an [AFC](https://github.com/AFCProject/AFC-Klipper-Add-On) (Armored
Turtle BoxTurtle) system does with the filament: in a Voron Stealthburner toolhead, in the BoxTurtle hub and buffer, and
in a lane. Every move follows AFC v1.2.0-5's source and shipped settings, and every drawing is rendered from the
projects' own CAD.

It started as one question: **where does the hot plastic go during the cut retract, and how much retraction is too
much?** It came out of chasing repeated jams at the top of the heat break, and has grown to cover the rest of what AFC
does to a filament: loading, jam detection, and loading and ejecting a spool.

## The operations

One tab each. The hardware choices at the top of the page apply to all of them.

- **Toolchange unload:** from the last printed line, through the slicer retract, the cut retract, the cut, pushback
  and the toolhead unload, to the lane pulled back clear of the hub. The question it answers: how high softened and
  liquid plastic reach, relative to the top of the heat break.
- **Toolhead load:** TOOL_LOAD, from the hub empty and the new lane parked 65 mm short of the hub switch, through the
  hub, the bowden, the toolhead sensors (or the buffer, with no toolhead sensor) and `tool_stn`, to the purge, wipe and
  kick. It starts where the unload ends, so the new filament meets the previous lane's cut-off piece in the hotend, and
  shows how much of it is pushed out before the purge.
- **Jam detection:** AFC's buffer fault check while printing, over a moving print bed. Part I: a jam at the heat break
  (or a nozzle clog): the printed line fails, the extruder keeps turning, and the buffer opens to its advance switch.
  Part II: a tangled spool: the feed stops, extrusion pulls the buffer closed. With `filament_error_sensitivity` above 0
  the check counts extruder travel and pauses with CLOG DETECTED or AFC NOT FEEDING. AFC's default, 0, turns it off.
- **Spool load and eject:** on sections of the lane's respooler and lane extruder: the spool's end pushed in through
  the feeder and the prep rollers to the gears, the lane homing to the load sensor, `dist_hub` to its parking spot short
  of the hub switch, through the hub at the next toolchange, back after an unload, LANE_UNLOAD, and out. The prep
  trigger swings, the gears turn, the load sensor's bearing moves, and the hub view follows the same filament.

## Hardware choices

- **Extruder body:** FilamATrix Clockwork 2 with two switches, one switch (top only) or none; or FilamATrix 2.5 (no
  switch) with an ECAS04 or a collet. With no toolhead switch AFC uses the buffer as its sensor, and the page follows
  that path in every tab.
- **Hotend:** Phaetus Rapido HF, V2 HF, UHF and V2 UHF; Phaetus Dragon HF, UHF and UHF Mini; E3D Revo Voron; Bambu Lab.
  Each has its own printhead, liner and heat zones.
- **Blade:** LDO full-length or Olfa KB4-F.
- **Lane:** BoxTurtle v1.1 with the Apex lane extruder (LDO Orbiter gears), the Smol-D2HW (BMG gears) or the Smol V2
  (ProtoXtruder gears), or BoxTurtle v1.0 (Smol-D2HW, BMG gears); the respooler follows the version.
- **Hub and buffer:** BoxTurtle v1.0 hub or v1.1 load-only hub, each with a TurtleNeck (optionally with a rubber band,
  a community mod that pulls it closed once the filament is free; while printing, the filament is held at both ends and
  the buffer's switch feedback keeps it mid-travel either way); or the v1.1 hub/buffer combo, whose outlet block slides up to 10 mm on two
  spring-loaded binding barrels. The combo's switch trigger points are estimated.

## What the drawings show

- **Toolhead:** a front-on section through the filament axis. Moving parts: the cutter arm driven by the head stroke
  onto the pin, the blade holder, the bent and preloaded return spring, both extruder gears, the guidler swinging in
  when the gears are empty, and the filament-switch balls.
- **Filament:** a chain of 0.25 mm pieces, each carrying its own temperature, colored from 40 °C (green) through the
  glass transition (yellow) to print temperature (red). Liquid plastic stretches on a pull instead of lifting out as a
  solid. Faint tick marks move with the material. The previous lane's cut-off piece is outlined in purple; a jam at the
  heat break is drawn swollen, in magenta.
- **Buffer:** a section of the TurtleNeck or of the combo's outlet block, moving with the lane's feed and the
  extruder's pull, with the switch states.
- **Hub:** top and side sections of each hub through its channels, with the lane's filament, the inlet PTFE on its
  socket axis, the ECAS04 collets, the sensor bearing riding on the filament, the combo's barrels with their springs
  compressing, and the switches above the cut drawn see-through (with an opacity slider).
- **Print bed** (Jam detection): a textured bed 0.2 mm under the nozzle and the printed line moving off with it, with a
  magnified inset.
- **Readouts:** each step's moves (extruder, lane), totals, sensor and switch states, how high softened (above the
  glass transition) and liquid plastic reach relative to the heat-break top, and the clog counter.
- **Layout:** the hardware bar first, then the tabs; the drawing, narration, timeline and buffer fit on one 1080p
  screen, with the settings below.

## Settings

- Material preset (PLA, ABS, PETG, ASA): print temperature, glass transition and liquid threshold for the heat model.
- `retract_length`, `pushback_length`, `cut_move_dist`, the slicer's toolchange retract and the heat model's time
  constant, starting at AFC's shipped defaults (red arrows), or at Armored Turtle's table values for the hotend where
  it lists them. With `cut_move_dist`, the narration says where the blade crosses the filament, and whether it gets
  through at all.
- `filament_error_sensitivity` and where the jam happens (Jam detection); the lane shown in the hub views.
- A "Where do I find these settings?" pop-up names the file, section and variable for each setting and how to try a
  value without editing the file.

## The heat model is an estimate

The temperatures come from a simple model, not measurements:

- **Wall temperatures:** the material's print temperature in the block, falling to 90 °C across the exposed heat break, 55–90 °C up the heat
  break inside the heatsink, 50 °C in the heatsink above it, and 40 °C above the heatsink.
- **Heating and cooling:** each piece of filament relaxes toward the local wall temperature with a time constant,
  3 s by default.
- **Starting state:** steady printing at 2.5 mm/s of filament (Toolchange unload, Jam detection); the state the unload
  leaves (Toolhead load).
- **Liquid:** material above the preset's liquid threshold stretches on a pull and flows out on a push past the tip, keeping its volume. The tip moves 6 % of the pull.

Use the numbers to rank settings against each other, not as exact limits. Checking the model against a measured
heat-break temperature, or against cut remnants pulled from the hotend, would make them firmer.

### Result for this toolhead

The largest `retract_length` that keeps softened plastic (at or above the glass transition) below the top of the heat
break, from `tools/sweep/run_sweep.py`. It uses the page's material presets and AFC's other defaults. The slicer's 1.5 mm
and AFC's 2 mm quick pull come first and are included.

| Material preset (print °C, Tg °C) | Max `retract_length` (time constant 2–5 s) | Softened plastic at AFC's default 20 mm |
|---|---|---|
| PLA (210, 60) | 0.5–2 mm | 18 mm above the heat break top |
| PETG (240, 80) | 4.5–5.5 mm | 14 mm above |
| ABS (250, 105) | 6.5–7 mm | 13 mm above |
| ASA (260, 100) | 6–6.5 mm | 13 mm above |

The print temperature hardly matters in this model. What sets the limit is each plastic's glass transition against the
heat break's temperature profile, which is an estimate, the same for every material. So low-Tg plastics come out the
most sensitive.

## Repository layout

| Path | What it is |
|---|---|
| `index.html` | The page. GitHub Pages serves it. |
| `assets/<body>__<hotend>/` | The render layers for each extruder body and hotend, which the page loads on demand. |
| `assets/buffer_tn/`, `assets/buffer_bt/` | The TurtleNeck and BoxTurtle hub/buffer combo layers. |
| `assets/hub_<hub>_<view>/`, `assets/hub_paths.json` | Top and side sections of the three BoxTurtle hubs (v1.0, v1.1 load-only, v1.1 combo), and the traced filament paths. |
| `page/template.html` | The page source: layout, the four operations' narration and timelines, the heat model, buffer and hub models, and the animation. |
| `tools/export_*.py` | Mesh the source STEP files with FreeCAD: toolhead, bodies and cover, hotends, Voron board, BoxTurtle combo. |
| `tools/hotends.json` | Per-hotend geometry: nozzle tip, heat zones, liner seat and length, Armored Turtle starting values. |
| `tools/buffer_section.py`, `tools/btcombo_section.py`, `tools/buffer_assets.py` | Render the TurtleNeck and the BoxTurtle hub/buffer combo; cut the combo's page assets. |
| `tools/hub_section.py`, `tools/hub_paths.py`, `tools/hub_assets.py`, `tools/import_hub_stl.py`, `tools/export_bthub10.py`, `tools/place_bthub10.py` | Hub sections (top and side), channel and socket fitting, hub page assets, the load-only hub's body from Armored Turtle's STL, and the v1.0 hub's export and placement. |
| `build_all.sh` | Renders every body variant and assembles the page. |
| `tools/section.py` | Render the section and the moving layers. A NumPy z-buffer renderer that draws cut faces hatched. |
| `tools/path_data.py`, `tools/sprites.py`, `tools/build_page.py` | Filament path data, sprite cutting, and page assembly. |
| `tools/sweep/` | Runs the page's heat model headless and sweeps `retract_length` per material. |
| `cad/` | Meshes extracted from the CAD (see licenses). |

### Rebuilding

Python 3 with NumPy, SciPy and Pillow. FreeCAD is only needed to re-extract meshes from the STEP files.

```zsh
PY=python3 ./build_all.sh
python3 tools/sweep/run_sweep.py
```

The source STEP files are not in this repository. They are:

- `Stealthburner_FilamATrix.step` from [thunderkeys/FilamATrix](https://github.com/thunderkeys/FilamATrix) (`CAD/`);
- `Toolhead PCBs.step` from
  [VoronDesign/Voron-Hardware](https://github.com/VoronDesign/Voron-Hardware) (`Stealthburner_Toolhead_PCB/CAD/`);
- `BT_V1.1_release.step` (`CAD/Cad.zip`) and `STLs/Modules/Hub/hub_load_only/hub_load_only.stl` from
  [ArmoredTurtle/BoxTurtle](https://github.com/ArmoredTurtle/BoxTurtle), and `BoxTurtle.step` (`CAD/Cad.zip`) from its
  `BT-1.0` tag;
- the TurtleNeck CAD from [ArmoredTurtle/TurtleNeck](https://github.com/ArmoredTurtle/TurtleNeck);
- the FilamATrix 2.5 no-switch bodies, shared by the FilamATrix authors on the Armored Turtle Discord.

## Licenses and credits

- **Code** (`page/`, `tools/`, and the code in `index.html`): [AGPL-3.0](LICENSE).
- **CAD-derived data** (`cad/`, `assets/`): [GPL-3.0](LICENSE-CAD). It is derived from GPL-3.0 sources:
  - [FilamATrix](https://github.com/thunderkeys/FilamATrix) by thunderkeys. The FilamATrix 2.5 no-switch bodies
    (ECAS04 and collet) were shared by the FilamATrix authors on the Armored Turtle Discord.
  - Voron Design's [Stealthburner and Clockwork 2](https://github.com/VoronDesign/Voron-Stealthburner), the Clockwork 2.5
    parts (motor plate, guidler A, latch shuttle, cable cover, collet), and the
    [Stealthburner toolhead PCB](https://github.com/VoronDesign/Voron-Hardware).
  - Armored Turtle's [TurtleNeck](https://github.com/ArmoredTurtle/TurtleNeck) and
    [BoxTurtle](https://github.com/ArmoredTurtle/BoxTurtle) v1.0 (hub, from the `BT-1.0` release) and v1.1 (load-only hub,
    hub/buffer combo).
- **Vendor models** included in that CAD are credited to their makers: Phaetus (Rapido, Dragon), E3D (Revo), Bambu Lab
  (hotend), LDO (stepper motor), Omron (switches), and standard hardware.
- The toolhead board drawn is Voron's reference Stealthburner PCB. Boards such as BTT's SB2209 mount in the same place.
- The sequence and default values come from
  [AFC-Klipper-Add-On](https://github.com/AFCProject/AFC-Klipper-Add-On) and
  [Armored Turtle's documentation](https://github.com/ArmoredTurtle/AT-Documentation).

GPL-3.0 allows combining its material with AGPL-3.0 code, and each part keeps its own license.

See [ai-usage.md](ai-usage.md) for how this was made.

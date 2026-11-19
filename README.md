# AFC X-ray

**Live page: https://4o66.github.io/afc-xray/**

An animated, narrated section of a Voron Stealthburner toolhead showing what happens inside it during an
[AFC](https://github.com/AFCProject/AFC-Klipper-Add-On) (Armored Turtle BoxTurtle) toolchange. It runs from the last
extrusion of the old color until the filament leaves the top filament sensor.

It was built to answer one question: **where does the hot plastic go during the cut retract, and how much retraction is
too much?** It came out of chasing repeated jams at the top of the heat break.

## What it shows

- A front-on section through the filament axis. The section is to scale, rendered from the FilamATrix and Voron CAD.
  The toolhead is a Stealthburner with a FilamATrix dual-switch Clockwork 2, a Phaetus Rapido V2 UHF and a FilamATrix
  cutter.
- Every extruder move of the sequence, with its exact distance and speed. The moves come from AFC v1.2.0-5's
  `TOOL_UNLOAD` and its `AFC_CUT` macro, using AFC's shipped default settings. Moves are shown slowed down and waits sped up, and each
  step says by how much.
- The filament as a chain of 0.25 mm pieces, each carrying its own temperature. The colors run from 40 °C (green)
  through the glass transition (yellow) to print temperature (red).
- Liquid plastic stretching when it is pulled, instead of lifting out of the nozzle as a solid.
- The moving parts:
  - the cutter arm, driven by the head stroke onto the pin;
  - the blade holder;
  - the bent, preloaded return spring;
  - both extruder gears;
  - the guidler swinging in when the gears are empty;
  - the filament-switch balls.
- Readouts of how high softened (above 100 °C) and liquid (above 200 °C) plastic reaches, relative to the top of the
  heat break.
- An extruder-body choice: FilamATrix CW2 dual switch, single switch (top switch only), or no switch; or FilamATrix 2.5
  (no switch) with an ECAS04 or a collet. With no switch,
  AFC uses the buffer as its sensor, and the page follows that path: the lane pulls back until the buffer reads trailing,
  then the 100 mm unload runs with no toolhead check.
- A hotend choice: Phaetus Rapido HF, V2 HF, UHF and V2 UHF; Phaetus Dragon HF, UHF and UHF Mini; E3D Revo Voron;
  Bambu Lab. Each has its own printhead, liner and heat zones.
- A blade choice: LDO full-length or Olfa KB4-F.
- Four operations, one tab each, all on the same section drawings and heat model:
  - **Toolchange unload:** from the last printed line to the filament leaving the toolhead, with the cut.
  - **Toolhead load:** TOOL_LOAD from the lane parked at the hub to the purge, starting where the unload ends, so the
    new filament meets the previous lane's cut-off piece (outlined) in the hotend.
  - **Jam detection:** the buffer's clog check for a nozzle clog or a spool tangle, with `filament_error_sensitivity`
    (AFC's default, 0, turns it off).
  - **Spool load and eject:** a new spool from the prep sensor to its parking spot short of the hub switch, through the hub
    at the next toolchange, back, and LANE_UNLOAD, on top and side sections of the hub.
- A hardware bar: extruder body, hotend, blade, and the hub and buffer: the BoxTurtle v1.1 load-only hub with a
  TurtleNeck (optional rubber band, a community mod that holds it collapsed, so the no-switch unload skips the lane
  pull-back), or the v1.1 hub/buffer combo, whose outlet block slides up to 10 mm on two spring-loaded binding barrels.
  The combo's switch trigger points are estimated.
- Starting values: AFC's defaults, or Armored Turtle's table values for the chosen hotend where it lists them.
- A slider for the slicer's toolchange retract.
- A material preset (PLA, ABS, PETG, ASA). It sets the print temperature, glass transition and liquid threshold
  in the heat model, and the color scale follows it.
- Sliders for `retract_length`, `pushback_length`, `cut_move_dist` and the heat model's time constant. They start at
  AFC's shipped defaults, which red arrows mark. With `cut_move_dist`, the narration says where the blade crosses the
  filament, and whether it gets through at all.
- A "Where do I find these settings?" pop-up. It names the file, section and variable for each setting, says how to try a
  value without editing the file, and points to the slicer setting behind the toolchange retract.

## The heat model is an estimate

The temperatures come from a simple model, not measurements:

- **Wall temperatures:** 265 °C in the block, falling to 90 °C across the exposed heat break, 55–90 °C up the heat
  break inside the heatsink, 50 °C in the heatsink above it, and 40 °C above the heatsink.
- **Heating and cooling:** each piece of filament relaxes toward the local wall temperature with a time constant,
  3 s by default.
- **Starting state:** steady printing at 2.5 mm/s of filament.
- **Liquid:** material above 200 °C stretches on a pull, keeping its volume. The tip moves 6 % of the pull.

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
| `assets/hub_<hub>_<view>/`, `assets/hub_paths.json` | Top and side sections of both BoxTurtle v1.1 hubs, and the traced filament paths. |
| `page/template.html` | The page source: layout, narration, heat model and animation. |
| `tools/export_*.py` | Mesh the source STEP files with FreeCAD: toolhead, bodies and cover, hotends, Voron board, BoxTurtle combo. |
| `tools/hotends.json` | Per-hotend geometry: nozzle tip, heat zones, liner seat and length, Armored Turtle starting values. |
| `tools/buffer_section.py`, `tools/btcombo_section.py`, `tools/buffer_assets.py` | Render the TurtleNeck and the BoxTurtle hub/buffer combo; cut the combo's page assets. |
| `tools/hub_section.py`, `tools/hub_paths.py`, `tools/hub_assets.py`, `tools/import_hub_stl.py` | Hub sections (top and side), channel tracing, hub page assets, and the load-only hub's body from Armored Turtle's STL. |
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
  [VoronDesign/Voron-Hardware](https://github.com/VoronDesign/Voron-Hardware) (`Stealthburner_Toolhead_PCB/CAD/`).

## Licenses and credits

- **Code** (`page/`, `tools/`, and the code in `index.html`): [AGPL-3.0](LICENSE).
- **CAD-derived data** (`cad/`, `assets/`): [GPL-3.0](LICENSE-CAD). It is derived from GPL-3.0 sources:
  - [FilamATrix](https://github.com/thunderkeys/FilamATrix) by thunderkeys. The FilamATrix 2.5 no-switch bodies
    (ECAS04 and collet) were shared by the FilamATrix authors on the Armored Turtle Discord.
  - Voron Design's [Stealthburner and Clockwork 2](https://github.com/VoronDesign/Voron-Stealthburner), the Clockwork 2.5
    parts (motor plate, guidler A, latch shuttle, cable cover, collet), and the
    [Stealthburner toolhead PCB](https://github.com/VoronDesign/Voron-Hardware).
  - Armored Turtle's [TurtleNeck](https://github.com/ArmoredTurtle/TurtleNeck) and
    [BoxTurtle](https://github.com/ArmoredTurtle/BoxTurtle) v1.1 (hub/buffer combo).
- **Vendor models** included in that CAD are credited to their makers: Phaetus (Rapido, Dragon), E3D (Revo), Bambu Lab
  (hotend), LDO (stepper motor), Omron (switches), and standard hardware.
- The toolhead board drawn is Voron's reference Stealthburner PCB. Boards such as BTT's SB2209 mount in the same place.
- The sequence and default values come from
  [AFC-Klipper-Add-On](https://github.com/AFCProject/AFC-Klipper-Add-On) and
  [Armored Turtle's documentation](https://github.com/ArmoredTurtle/AT-Documentation).

GPL-3.0 allows combining its material with AGPL-3.0 code, and each part keeps its own license.

See [ai-usage.md](ai-usage.md) for how this was made.

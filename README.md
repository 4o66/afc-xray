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

The largest `retract_length` that keeps softened plastic below the top of the heat break. It is from
`tools/sweep/run_sweep.py`, and is in addition to the slicer's 1.5 mm and AFC's 2 mm quick pull:

| Material (print °C, Tg °C) | Max `retract_length` | Softened plastic at 18 mm | At AFC's default 20 mm |
|---|---|---|---|
| ASA (265, ~100) | 6 mm (6.5–7 with slower cooling) | 11 mm above the heat break | 13 mm above |
| PETG (240, ~80) | 5 mm | 12 mm above | 14 mm above |
| PLA (210, ~60) | 1–2 mm | 16 mm above | 18 mm above |

## Repository layout

| Path | What it is |
|---|---|
| `index.html` | The page, self-contained. GitHub Pages serves it. |
| `page/template.html` | The page source: layout, narration, heat model and animation. |
| `tools/export_full.py`, `tools/export_voron.py` | Mesh the source STEP files with FreeCAD. |
| `tools/section.py` | Render the section and the moving layers. A NumPy z-buffer renderer that draws cut faces hatched. |
| `tools/path_data.py`, `tools/sprites.py`, `tools/build_page.py` | Filament path data, sprite cutting, and page assembly. |
| `tools/sweep/` | Runs the page's heat model headless and sweeps `retract_length` per material. |
| `cad/` | Meshes extracted from the CAD (see licenses). |

### Rebuilding

Python 3 with NumPy, SciPy and Pillow. FreeCAD is only needed to re-extract meshes from the STEP files.

```zsh
for m in base full arm slide guid dgear igear; do MODE=$m python3 tools/section.py; done
python3 tools/path_data.py && python3 tools/sprites.py && python3 tools/build_page.py
python3 tools/sweep/run_sweep.py
```

The source STEP files are not in this repository. They are:

- `Stealthburner_FilamATrix.step` from [thunderkeys/FilamATrix](https://github.com/thunderkeys/FilamATrix) (`CAD/`);
- `Toolhead PCBs.step` from
  [VoronDesign/Voron-Hardware](https://github.com/VoronDesign/Voron-Hardware) (`Stealthburner_Toolhead_PCB/CAD/`).

## Licenses and credits

- **Code** (`page/`, `tools/`, and the code in `index.html`): [AGPL-3.0](LICENSE).
- **CAD-derived data** (`cad/`, and the rendered images embedded in `index.html`): [GPL-3.0](LICENSE-CAD). It is
  derived from GPL-3.0 sources:
  - [FilamATrix](https://github.com/thunderkeys/FilamATrix) by thunderkeys;
  - Voron Design's [Stealthburner and Clockwork 2](https://github.com/VoronDesign/Voron-Stealthburner);
  - Voron Design's [Stealthburner toolhead PCB](https://github.com/VoronDesign/Voron-Hardware).
- **Vendor models** included in that CAD are credited to their makers: the Phaetus Rapido V2 UHF hotend, the LDO
  stepper motor, the Omron D2F switches, and standard hardware.
- The cable cover is the author's own design and is included under GPL-3.0.
- The toolhead board drawn is Voron's reference Stealthburner PCB. Boards such as BTT's SB2209 mount in the same place.
- The sequence and default values come from
  [AFC-Klipper-Add-On](https://github.com/AFCProject/AFC-Klipper-Add-On) and
  [Armored Turtle's documentation](https://github.com/ArmoredTurtle/AT-Documentation).

GPL-3.0 allows combining its material with AGPL-3.0 code, and each part keeps its own license.

See [ai-usage.md](ai-usage.md) for how this was made.

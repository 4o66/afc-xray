# AI usage

## Model

Claude Opus 5.5 (Anthropic), working through Claude Code. It did all of the following, in one working session
directed by the repository owner:

- extracting and rendering the CAD;
- reading the AFC source and config to build the sequence;
- the heat model;
- writing the page, the scripts and these docs.

## Constraints

- **The owner directed the work and made the decisions:**
  - what to show and what the page is for;
  - the corrections to the mechanism, including that the blade inserts are real, the PTFE liner and its chamfer, the
    preloaded and bent cutter spring, and which parts move;
  - the licensing split;
  - the parts left out of the drawing.
- **Downloads:** the AI downloaded third-party CAD only with the owner's approval per file. It did not use the
  toolhead board vendor's unlicensed model; it used Voron's GPL-3.0 reference board instead.
- **Printer changes:** the AI could not change the modeled printer without the owner's go-ahead.
- **Content:** no personal data, network addresses or local paths are in the repository.

## Checks

- **The sequence:** every extruder move was traced in AFC v1.2.0-5's Python source (`TOOL_UNLOAD`,
  `unload_sequence`) and its `AFC_CUT` macro, and in the printer's config, which was compared with its backup. The
  slicer's toolchange retract was checked against a real multi-color G-code file.
- **Geometry:** measured from the CAD meshes. The measurements include:
  - bores along the filament path;
  - the heatsink step where the PTFE liner seats;
  - gear tip and root radii;
  - the cutter-arm pivot and pin contact;
  - the spring pockets;
  - the mounting holes used to place the board, which match to 0.02 mm.
- **Liner length:** from the FilamATrix cutting jig list.
- **Variants:**
  - All 45 body and hotend combinations were rendered by the same pipeline; four were spot-checked as still images.
  - Every hotend was simulated headless with the dual-switch and no-switch bodies.
  - The FilamATrix 2.5 bodies were placed by a best fit against Voron's CW2.5 bodies (median 0.23 mm; the difference is
    the cutter slot).
  - Hotend heat zones come from part positions. Where the CAD has a hotend as one solid, they are estimated, and the page
    says so.
- **Buffer:** the TurtleNeck PTFE layout is inferred from the CAD bores. The fixed tube end is chosen so it stays inside
  the slide over the full 30 mm travel. The switch trigger points (2.5 mm before each stop, 25 mm apart) are from the
  TurtleNeck README.
- **BoxTurtle hub/buffer combo:** which parts move came from the owner: the hub is fixed; the outlet block, its barrels
  and trigger slide; the PTFE wear tube, its retainer ring and the bushings stay in the hub. The 10 mm travel is the
  owner's figure and matches the trigger moving from one switch to the other in the CAD. The trigger points (2 mm from
  each stop) are an estimate. Both end positions were composited and checked as still images.
- **Load, jam and spool timelines:** every move was traced in AFC v1.2.0-5's source (`TOOL_LOAD` and `load_sequence`,
  `AFC_buffer.py`'s fault check and multipliers, `prep_load`, `prep_post_load`, `eject_lane`, `unload_sequence`) by a
  separate AI agent, with file and line references, and its report was checked against the source where the page
  depends on it. Shipped template values are used where they differ from code defaults, and the page says which. Every
  tab was run headless for every body and buffer, and played in a browser.
- **Hubs:** the load-only hub's body in the STEP release has no filament channels, so Armored Turtle's printable STL is
  used instead (same size; it is turned 180° to match and placed by its bounding box). The channel centerlines are traced
  from a cross-section of each hub body; PTFE in the inlets and outlet is inferred. Which parts move, the 10 mm travel and
  the choice of hubs came from the owner.
- **Rendering:** every layer was composited at rest and compared with the full render. Visual problems the owner
  reported were fixed and checked again, among them a rotating part that should not rotate, holes in a layer, and the
  spring's shape.
- **Page:** the script was syntax-checked, and the heat model was run headless (`tools/sweep/`) to confirm the
  numbers in the README. The page was loaded in a browser to check for console errors.

## Known limits

- The heat model's wall temperatures and time constant are estimates and have not been validated against
  measurements.
- Melt behavior is a simple volume-keeping stretch rule.
- Head travel times are estimates.
- Some vendor geometry was identified by shape, not by name.
- The jam timeline uses a steady 2.5 mm/s print rate; the spool timeline's prep-to-load distance and the no-switch load's
  gap at the gears are examples, marked as such on the page.

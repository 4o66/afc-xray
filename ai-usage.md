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
- The page shows one printer's configuration.

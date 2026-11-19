#!/bin/zsh
# Render every extruder body x hotend combination and cut its sprites, then assemble the page.
# PY can point at a Python with NumPy, SciPy and Pillow. Takes about half an hour.
set -e; cd "${0:a:h}"; PY=${PY:-python3}
BODIES=(dual single none f25_ecas f25_collet)
HOTENDS=($($PY -c 'import json; print(" ".join(k for k in json.load(open("tools/hotends.json")) if not k.startswith("_")))'))
for b in $BODIES; do
  for m in arm slide guid dgear igear; do BODY=$b MODE=$m $PY tools/section.py >/dev/null; done
  BODY=$b MODE=slide BLADE=olfa $PY tools/section.py >/dev/null
  for h in $HOTENDS; do
    for m in base full; do BODY=$b HOTEND=$h MODE=$m $PY tools/section.py >/dev/null; done
    BODY=$b HOTEND=$h $PY tools/sprites.py
    rm -f build/${b}__${h}/depth_*.npy
  done
done
for m in base full slide; do SIDE=a MODE=$m $PY tools/btcombo_section.py >/dev/null; done
$PY tools/buffer_assets.py bt
$PY tools/path_data.py && $PY tools/build_page.py

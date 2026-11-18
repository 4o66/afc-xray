#!/bin/zsh
# Render every body variant and cut its sprites. PY can point at a Python with NumPy, SciPy and Pillow.
set -e; cd "${0:a:h}"; PY=${PY:-python3}
for b in dual single none; do
  for m in base full arm slide guid dgear igear; do BODY=$b MODE=$m $PY tools/section.py | grep -E "saved|Error"; done
  BODY=$b $PY tools/sprites.py
done
$PY tools/path_data.py && $PY tools/build_page.py

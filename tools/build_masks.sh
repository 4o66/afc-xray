#!/bin/zsh
# Build the recolor masks (issue #7): the whole render pipeline again with MASK=1, in a mirror root that shares cad/ and
# tools/ but has its own build/ and assets/, so every mask comes out with exactly the crops, offsets and visibility of the
# real sprite. Each mask is copied next to its sprite as m_<file>: red = printed primary, green = printed accent, blue =
# cut face. Run after build_all.sh and tools/lane_assets.py. PY as in build_all.sh.
set -e; cd "${0:a:h}/.."; ROOT=$PWD; R=$ROOT/build_mask_root; PY=${PY:-python3}
mkdir -p $R/build $R/assets
# tools/ is a real directory of symlinked files: the scripts find the root as tools/.., which would resolve through a
# symlinked tools/ back to the real repo
[[ -e $R/cad ]] || ln -s $ROOT/cad $R/cad
[[ -L $R/tools ]] && rm $R/tools; mkdir -p $R/tools
for f in $ROOT/tools/*(.N); do ln -sf $f $R/tools/${f:t}; done
sed '$d' build_all.sh > $R/build_all_masks.sh               # every step but the last (data and page)
( cd $R && MASK=1 PY=$PY zsh build_all_masks.sh && MASK=1 $PY tools/lane_assets.py )
n=0
for f in $R/assets/*/(base.webp|sprite_*.png)(N); do
  d=${f:h:t}; [[ -d $ROOT/assets/$d ]] || { echo "no such asset dir: $d"; exit 1; }
  cp $f $ROOT/assets/$d/m_${f:t}; n=$((n + 1))
done
echo "masks copied: $n"

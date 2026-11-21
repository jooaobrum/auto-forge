#!/usr/bin/env bash
HERE=$(cd "$(dirname "$0")" && pwd)
source "$HERE/../common.sh"
W=.specs/features/short-slice
exp freeze short-slice
"$PY" model.py --all 3 --out $W/base.json
exp baseline short-slice --from $W/base.json
exp select short-slice --variant t045
echo '{"threshold": 0.45}' > model/config.json
mkdir -p $W/runs/t045
"$PY" model.py --selection $W/selection.json --out $W/runs/t045/seeds.json
exp gate short-slice --variant t045 --confirm
git commit -qam "tune(model): threshold 0.45 for the short slice"
exp deliver short-slice --decision adopt

#!/usr/bin/env bash
HERE=$(cd "$(dirname "$0")" && pwd)
source "$HERE/../common.sh"
W=.specs/features/orders
route freeze orders
lean validate_checks orders
contract compile orders --dialect sqlite
"$PY" pipeline.py fixture/orders_raw.csv dev.db
mkdir -p $W/runs/main
"$PY" run_contract.py $W/contract.sql dev.db $W/runs/main/contract.csv
contract gate orders
verify orders
route deliver orders

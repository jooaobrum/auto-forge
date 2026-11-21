#!/usr/bin/env bash
HERE=$(cd "$(dirname "$0")" && pwd)
source "$HERE/../common.sh"
rl brief orders
rl freeze orders
rl contract orders contracts/orders.yaml --golden golden.csv --dialect sqlite
"$PY" pipeline.py fixture/orders_raw.csv dev.db
mkdir -p .lanes/work/orders/runs/main
"$PY" run_contract.py .lanes/work/orders/contract.sql dev.db .lanes/work/orders/runs/main/contract.csv
rl gate orders
rl deliver orders

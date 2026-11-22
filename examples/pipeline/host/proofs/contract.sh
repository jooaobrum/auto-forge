#!/usr/bin/env bash
# The contract gate at HEAD: compile, run the pipeline on the fixture, run the contract, gate it.
set -euo pipefail
SCRIPTS="${AUTO_FORGE_SKILLS:?set AUTO_FORGE_SKILLS to the skills folder}/agent-spec-pipeline/scripts"
W=.specs/features/orders
python3 "$SCRIPTS/contract.py" compile orders --dialect sqlite
python3 pipeline.py fixture/orders_raw.csv dev.db
mkdir -p $W/runs/main
python3 run_contract.py $W/contract.sql dev.db $W/runs/main/contract.csv
python3 "$SCRIPTS/contract.py" gate orders

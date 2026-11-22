#!/usr/bin/env bash
# The production standard at HEAD: the tests' JUnit, then validate_prod.py (D1-D10).
set -euo pipefail
SCRIPTS="${AUTO_FORGE_SKILLS:?set AUTO_FORGE_SKILLS to the skills folder}/agent-spec-mlops/scripts"
mkdir -p .specs/features/churn-mlops/runs/main
python3 -m pytest -q -p no:cacheprovider tests --junitxml .specs/features/churn-mlops/runs/main/tests.xml >/dev/null
python3 "$SCRIPTS/validate_prod.py" churn-mlops

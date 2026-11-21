#!/usr/bin/env bash
HERE=$(cd "$(dirname "$0")" && pwd)
source "$HERE/../common.sh"
W=.specs/features/churn-mlops
route freeze churn-mlops
expect_fail mlops validate_prod churn-mlops
PYTHONPATH=src "$PY" -m pytest -q -p no:cacheprovider tests --junitxml $W/runs/main/tests.xml
PYTHONPATH=src "$PY" -m churn.pipelines.train --env dev
mlops model_card
mlops validate_prod churn-mlops
git add -A && git commit -qm "feat(churn): train in dev, with its trace and model card"
route deliver churn-mlops

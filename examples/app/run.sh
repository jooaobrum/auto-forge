#!/usr/bin/env bash
HERE=$(cd "$(dirname "$0")" && pwd)
source "$HERE/../common.sh"
route freeze sum
"$PY" -m pytest -q -p no:cacheprovider e2e --junitxml=.specs/features/sum/runs/main/e2e.xml >/dev/null
route junit sum
route deliver sum

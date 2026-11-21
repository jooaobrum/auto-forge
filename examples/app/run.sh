#!/usr/bin/env bash
HERE=$(cd "$(dirname "$0")" && pwd)
source "$HERE/../common.sh"
rl brief sum
rl freeze sum
"$PY" -m pytest -q -p no:cacheprovider e2e --junitxml=.lanes/work/sum/runs/main/junit.xml >/dev/null
rl gate sum
rl deliver sum

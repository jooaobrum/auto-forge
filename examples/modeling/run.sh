#!/usr/bin/env bash
HERE=$(cd "$(dirname "$0")" && pwd)
source "$HERE/../common.sh"
W=.specs/features/secom
route problem
modeling validate_plan secom --approved
expect_fail modeling validate_round secom
git rm -q notebooks/peek.py && git commit -qm "chore: drop the notebook that read the OOT weeks"
modeling validate_round secom
expect_fail modeling validate_verification secom
cp verify/verification.md $W/verification.md
git add -A && git commit -qm "verify(secom): fresh-context verification on OOT"
modeling validate_verification secom
modeling deliver secom --decision promote
test -f .specs/features/secom-mlops/spec.md

#!/usr/bin/env bash
HERE=$(cd "$(dirname "$0")" && pwd)
source "$HERE/../common.sh"
W=.specs/features/cite-history
exp freeze cite-history
"$PY" agent.py --all 3 --out $W/base.json
exp baseline cite-history --from $W/base.json

# Hypothesis 1: read in full - expected to break q02 and the token guardrail
exp select cite-history --variant full-read
echo "Read every history record in full and summarize it." > prompts/history.md
mkdir -p $W/runs/full-read
"$PY" agent.py --selection $W/selection.json --out $W/runs/full-read/runs.json
expect_fail exp gate cite-history --variant full-read

# Hypothesis 2: cite ids
exp select cite-history --variant cite-ids
echo "Summarize the history records relevant to the question and cite the id of every record you used." \
  > prompts/history.md
mkdir -p $W/runs/cite-ids
"$PY" agent.py --selection $W/selection.json --out $W/runs/cite-ids/runs.json
exp gate cite-history --variant cite-ids
"$PY" agent.py --selection $W/selection.json --tier stable --out $W/runs/cite-ids/confirm.json
exp gate cite-history --variant cite-ids --confirm
exp budget cite-history
git commit -qam "prompt(history): cite the id of every record used"
exp deliver cite-history --decision adopt

#!/usr/bin/env bash
HERE=$(cd "$(dirname "$0")" && pwd)
source "$HERE/../common.sh"
W=.lanes/work/cite-history
rl brief cite-history
rl freeze cite-history
"$PY" agent.py --all 3 --out $W/base.json
rl baseline cite-history --from $W/base.json

# Variant 1 (hypothesis 1): read in full - expected to break q02 and the token guardrail
rl select cite-history --variant full-read
echo "Read every history record in full and summarize it." > prompts/history.md
mkdir -p $W/runs/full-read
"$PY" agent.py --selection $W/selection.json --out $W/runs/full-read/runs.json
expect_fail rl gate cite-history --variant full-read

# Variant 2 (hypothesis 2): cite ids
rl select cite-history --variant cite-ids
echo "Summarize the history records relevant to the question and cite the id of every record you used." \
  > prompts/history.md
mkdir -p $W/runs/cite-ids
"$PY" agent.py --selection $W/selection.json --out $W/runs/cite-ids/runs.json
rl gate cite-history --variant cite-ids
"$PY" agent.py --selection $W/selection.json --tier stable --out $W/runs/cite-ids/confirm.json
rl gate cite-history --variant cite-ids --confirm
rl budget cite-history
git commit -qam "prompt(history): cite the id of every record used"
rl deliver cite-history --decision adopt

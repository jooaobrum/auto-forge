# Sourced by each example: copy its host into a fresh git repo and define `rl`.
set -euo pipefail
export PYTHONDONTWRITEBYTECODE=1
PY=${PYTHON:-python3}
HOST=$(mktemp -d)
[ "${KEEP:-0}" = 1 ] && echo "host kept at $HOST" || trap 'rm -rf "$HOST"' EXIT
cp -R "$HERE/host/." "$HOST/"
cd "$HOST"
git init -q -b main
git config user.email example@example.com
git config user.name example
git add -A
git commit -q -m "initial"
SK="$(cd "$HERE/../../skills" && pwd)"
export AUTO_FORGE_SKILLS="$SK"
exp() { "$PY" "$SK/agent-spec-experiment/scripts/experiment.py" "$@"; }
contract() { "$PY" "$SK/agent-spec-pipeline/scripts/contract.py" "$@"; }
route() { "$PY" "$SK/agent-spec-router/scripts/route.py" "$@"; }
expect_fail() { if "$@"; then echo "expected a failing gate"; exit 1; fi; }
modeling() { "$PY" "$SK/agent-spec-modeling/scripts/$1.py" "${@:2}"; }
mlops() { "$PY" "$SK/agent-spec-mlops/scripts/$1.py" "${@:2}"; }
lean() { "$PY" "$SK/agent-spec-lean/scripts/$1.py" "${@:2}"; }
# The Verifier (agents/verifier.md) chooses the mutations and writes verification.md; here they come from verify/.
verify() {
  cp "$HERE/verify/mutations.json" ".specs/features/$1/"
  lean check_proofs "$1" --mutations ".specs/features/$1/mutations.json"
  expect_fail route deliver "$1"   # no verification yet: refused
  cp "$HERE/verify/verification.md" ".specs/features/$1/"
  lean validate_verification "$1"
}

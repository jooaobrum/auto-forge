#!/usr/bin/env bash
# Every Profile, shape output (brief.md) to delivery.md, on local engines.
set -euo pipefail
DIR=$(cd "$(dirname "$0")" && pwd)
for profile in app pipeline model agent modeling mlops; do
  echo "=== $profile"
  bash "$DIR/$profile/run.sh"
done
echo "all profiles delivered"

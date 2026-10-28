#!/usr/bin/env bash
set -euo pipefail
name=${1:?unique job name required}
timeout=${2:?wall timeout required}
shift 2
tools=$(cd -- "$(dirname -- "$0")" && pwd)
mkdir -p "${VES_RELEASE_LOG_DIR:-$tools/native}"
exec systemd-run --user --unit="ves-release-$name" --wait --pipe \
  -p CPUQuota=25% -p Nice=19 -p IOWeight=10 -p MemoryMax=384M \
  -p MemorySwapMax=0 -p 'InaccessiblePaths=-/dev/dri -/dev/kfd' \
  --setenv=OPENBLAS_NUM_THREADS=1 --setenv=OMP_NUM_THREADS=1 \
  --setenv=MKL_NUM_THREADS=1 --setenv=VESUVIUS_THREADS=1 --setenv=OMP_THREAD_LIMIT=1 \
  --setenv=PYTHONDONTWRITEBYTECODE=1 \
  --setenv="VES_RELEASE_LOG_DIR=${VES_RELEASE_LOG_DIR:-$tools/native}" \
  python3 "$tools/run_native_guarded.py" --name "$name" --timeout "$timeout" -- "$@"

#!/usr/bin/env bash
set -euo pipefail
task_name=$1
task_timeout=$2
shift 2
research_dir=$(cd -- "$(dirname -- "$0")" && pwd)
exec systemd-run --user --unit="ves-${task_name}" --wait --pipe \
  -p CPUQuota=25% -p Nice=19 -p IOWeight=10 -p MemoryMax=384M \
  -p MemorySwapMax=0 -p 'InaccessiblePaths=-/dev/dri -/dev/kfd' \
  --setenv=OPENBLAS_NUM_THREADS=1 --setenv=OMP_NUM_THREADS=1 \
  --setenv=MKL_NUM_THREADS=1 --setenv=VESUVIUS_THREADS=1 --setenv=OMP_THREAD_LIMIT=1 \
  python3 "$research_dir/run_native_guarded.py" --name "$task_name" \
  --timeout "$task_timeout" -- "$@"

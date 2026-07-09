#!/usr/bin/env bash
# Stage-1 (gmx -pbc whole) + stage-2 (fix_viz_gromacs.py greedy assembly + CA fit)
# for the GROMACS viz systems. Backs up traj.xtc before overwriting.
# Usage: run_gmx_fix.sh SYS TPR TRR
set -euo pipefail
SYS=$1; TPR=$2; TRR=$3
ROOT=/MDdata/data02/jxhuang/gpcr_g/gpcr_g_server
W=/tmp/claude-1001/-MDdata-data02-jxhuang-gpcr-g-gpcr-g-server/2b04bb95-6e84-4bf5-9eff-30987eb656e6/scratchpad
TRAJ=$ROOT/data/viz/$SYS/traj.xtc
WHOLE=$W/${SYS}_whole.xtc

echo "=== $SYS: stage1 gmx -pbc whole -skip 4 ==="
printf '0\n' | gmx trjconv -s "$TPR" -f "$TRR" -pbc whole -skip 4 -o "$WHOLE" >/dev/null 2>&1

echo "=== $SYS: backup + stage2 assembly/fit ==="
cp -n "$TRAJ" "$TRAJ.broken_pbc_$(date +%Y%m%d_%H%M%S)" || true
python3 "$ROOT/scripts/fix_viz_gromacs.py" "$SYS" "$TPR" "$WHOLE" --stride 1

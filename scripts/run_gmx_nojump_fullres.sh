#!/usr/bin/env bash
# Full-resolution nojump fix for NPT trajectories whose per-frame box fluctuates,
# so the historical PBC wrap is NOT recoverable by current-box integer shifts.
# gmx -pbc whole then -pbc nojump on the FULL-RES trajectory uses each frame's own
# box + inter-frame continuity from the compact starting frame -> chains stay
# together throughout. (Decimated nojump fails: 200 ps spacing breaks continuity.)
# Usage: run_gmx_nojump_fullres.sh SYS TPR TRR
set -euo pipefail
SYS=$1; TPR=$2; TRR=$3
ROOT=/MDdata/data02/jxhuang/gpcr_g/gpcr_g_server
W=/tmp/claude-1001/-MDdata-data02-jxhuang-gpcr-g-gpcr-g-server/2b04bb95-6e84-4bf5-9eff-30987eb656e6/scratchpad
WHOLE=$W/${SYS}_whole_full.xtc
NOJ=$W/${SYS}_nojump_full.xtc
DEC=$W/${SYS}_nojump_dec.xtc

echo "=== $SYS: full-res -pbc whole ==="
printf '0\n' | gmx trjconv -s "$TPR" -f "$TRR" -pbc whole -o "$WHOLE" >/dev/null 2>&1
echo "=== $SYS: full-res -pbc nojump ==="
printf '0\n' | gmx trjconv -s "$TPR" -f "$WHOLE" -pbc nojump -o "$NOJ" >/dev/null 2>&1
rm -f "$WHOLE"
echo "=== $SYS: decimate stride 4 ==="
printf '0\n' | gmx trjconv -s "$TPR" -f "$NOJ" -skip 4 -o "$DEC" >/dev/null 2>&1
rm -f "$NOJ"
echo "=== $SYS: select protein+lig, CA-fit, fix structure ==="
python3 "$ROOT/scripts/finish_nojump.py" "$SYS" "$TPR" "$DEC"
rm -f "$DEC"
echo "DONE $SYS"

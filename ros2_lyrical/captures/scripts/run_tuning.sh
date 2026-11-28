#!/usr/bin/env bash
# Experiment 13 (docs/03 §4.4): Fast DDS tuning variants + Cyclone DDS on the 640x480 image workload,
# under the default veth and under the tc tbf1g shaping, BEST_EFFORT and RELIABLE.
# A thin driver around run_rcvbuf_sweep.sh (arms noxml, largedata, mtu1400, cyclone; optional flowctl):
# one invocation per (shape, qos), each under its own EXCLUSIVE lock so other experiments get turns.
#
# Usage: ./run_tuning.sh [--reps N] [--cyc-reps M] [--shapes "none tbf1g"] [--qos "be rel"] [--extra-arms LIST]
#                        [--out DIR] [--summary-only]
#   defaults: --reps 4 (Fast DDS arms), --cyc-reps 3 (cyclone arm), 20 images per run, keep 1 pcap per arm,
#             out ./out/tuning/<shape>/ ; summary -> ../results/tuning_*.csv
# Image: lyrical-wire:exp-extra for every arm (Fast DDS 3.6.2 is the same package version as in
# lyrical-wire:exp; the extra image adds rmw_cyclonedds_cpp), recorded in <out>/<shape>/env.txt.
set -euo pipefail
cd "$(dirname "$0")"
export IMG=lyrical-wire:exp-extra
REPS=4; CREPS=3; SHAPES="none tbf1g"; QOSS="be rel"; XARMS=""; OUT="$PWD/out/tuning"; SONLY=0
while [ $# -gt 0 ]; do
  case "$1" in
    --reps) REPS="$2"; shift 2;; --cyc-reps) CREPS="$2"; shift 2;;
    --shapes) SHAPES="$2"; shift 2;; --qos) QOSS="$2"; shift 2;;
    --extra-arms) XARMS="$2"; shift 2;; --out) OUT="$2"; shift 2;;
    --summary-only) SONLY=1; shift;;
    -h|--help) sed -n '2,/^set -euo/p' "$0" | sed '$d; s/^# \{0,1\}//'; exit 0;;
    *) echo "unknown option $1" >&2; exit 2;;
  esac
done
LOCK="$PWD/out/exp.lock"; mkdir -p "$OUT"
if [ "$SONLY" = 0 ]; then
  for shape in $SHAPES; do
    for q in $QOSS; do
      arms="$q:noxml*$REPS,$q:largedata*$REPS,$q:mtu1400*$REPS,$q:cyclone*$CREPS"
      [ -n "$XARMS" ] && arms="$arms,$XARMS"
      flock -x "$LOCK" ./run_rcvbuf_sweep.sh --shape "$shape" --arms "$arms" --keep-pcap 1 \
        --seed "$([ "$q" = be ] && echo 11 || echo 12)" --out "$OUT/$shape"
    done
  done
fi
R=../results
files=(); for d in "$OUT"/*/; do [ -f "$d/runs.csv" ] && files+=("$d/runs.csv"); done
python3 rcvbuf_sweep.py summary "$R/tuning_summary.csv" "${files[@]}"
python3 - "$R/tuning_runs.csv" "${files[@]}" <<'PY'
import csv, sys
rows = []
for fn in sys.argv[2:]:
    rows += list(csv.DictReader(open(fn, newline='')))
with open(sys.argv[1], 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
print(f'wrote {sys.argv[1]} ({len(rows)} runs)')
PY
for d in "$OUT"/*/; do
  [ -f "$d/runs.csv" ] && python3 rcvbuf_sweep.py lost "$d/lost.csv" "$d/runs.csv" >/dev/null
done
{ head -1 "$(ls "$OUT"/*/lost.csv | head -1)"; for f in "$OUT"/*/lost.csv; do tail -n +2 "$f"; done; } > "$R/tuning_lost_images.csv"
d0=$(ls -d "$OUT"/*/ | head -1); sed "s/$(hostname)/<host>/g" "$d0/env.txt" > "$R/tuning_env.txt"
echo "summary: $R/tuning_summary.csv"

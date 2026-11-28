#!/usr/bin/env bash
# Experiment 10 (docs/03 §13): demo talker -> listener with RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
# across two containers, captured on the listener's eth0 (the Cyclone equivalent of experiment 1).
# The image part of §13 runs through run_tuning.sh / run_rcvbuf_sweep.sh (arm "cyclone").
#
# Usage: ./run_cyclone.sh [--talker-s 6] [--out DIR]
#   Output (default ./out/cyclone/): exp10_cyclone_default.{raw.pcap,pcap,listener.log,talker.log,tcpdump.log},
#   ss_B.txt (ss -uamn in the listener while running), cyclone_config_B.txt (Cyclone's effective config
#   dumped by CYCLONEDDS_URI tracing 'config' category), env.txt
# Image: lyrical-wire:exp-extra (needs rmw_cyclonedds_cpp). Light functional run: use a SHARED lock:
#   flock -s out/exp.lock ./run_cyclone.sh
set -euo pipefail
cd "$(dirname "$0")"
export IMG=lyrical-wire:exp-extra
# shellcheck source=lib.sh
source ./lib.sh
TALK=6; OUT="$PWD/out/cyclone"
while [ $# -gt 0 ]; do
  case "$1" in
    --talker-s) TALK="$2"; shift 2;; --out) OUT="$2"; shift 2;;
    -h|--help) sed -n '2,/^set -euo/p' "$0" | sed '$d; s/^# \{0,1\}//'; exit 0;;
    *) echo "unknown option $1" >&2; exit 2;;
  esac
done
mkdir -p "$OUT"; chmod 777 "$OUT"; OUT="$(realpath "$OUT")"
ensure_net
B=a_hostB; A=a_hostA
trap 'clean $A $B; fix_owner "$OUT" || true' EXIT
[ -f "$OUT/env.txt" ] || write_env "$OUT"
n=exp10_cyclone_default
clean $A $B; rm -f "$OUT/$n".*
wait_ips_free 60 "$IP_B" "$IP_A"
# Listener side additionally writes Cyclone's configuration trace (Tracing/Category=config) to a file,
# so the effective defaults (MaxMessageSize, FragmentSize, SocketReceiveBufferSize, ...) are recorded.
CFG='<CycloneDDS><Domain><Tracing><Category>config</Category><OutputFile>/out/cyclone_config_B.txt</OutputFile></Tracing></Domain></CycloneDDS>'
docker run -d --name $B --net "$NET" --ip "$IP_B" -v "$OUT:/out" -e RMW_IMPLEMENTATION=rmw_cyclonedds_cpp \
  -e CYCLONEDDS_URI="$CFG" "$IMG" bash -c "$ROS_SRC
  tcpdump -i eth0 -U -w /out/$n.raw.pcap 2>/out/$n.tcpdump.log &
  $(ctr_wait_pcap "/out/$n.raw.pcap")
  touch /out/$n.started
  timeout $((TALK + 5)) ros2 run demo_nodes_cpp listener > /out/$n.listener.log 2>&1 &
  sleep $((TALK / 2 + 2)); ss -uamn > /out/ss_B.txt; wait %2
  cat /proc/net/snmp > /out/$n.snmp.txt; kill %1; sleep 1" >/dev/null
wait_pcap "$OUT/$n.raw.pcap" 10; wait_file "$OUT/$n.started" 0 10; sleep 1
docker run -d --name $A --net "$NET" --ip "$IP_A" -e RMW_IMPLEMENTATION=rmw_cyclonedds_cpp "$IMG" \
  bash -c "$ROS_SRC; timeout $TALK ros2 run demo_nodes_cpp talker" >/dev/null
echo "A exit $(wait_exit $A 60)" > "$OUT/$n.exit.txt"; docker logs $A > "$OUT/$n.talker.log" 2>&1 || true
echo "B exit $(wait_exit $B 60)" >> "$OUT/$n.exit.txt"
rm -f "$OUT/$n.started"
filter_pcap "$OUT/$n.raw.pcap" "$OUT/$n.pcap"
log "done -> $OUT/$n.pcap ($(stat -c %s "$OUT/$n.pcap") B), listener got $(grep -c 'I heard' "$OUT/$n.listener.log" || true)"

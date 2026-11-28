#!/usr/bin/env bash
# Experiments 11-12 (docs/03 §6 and §4.5), rmw_zenoh_cpp with one router, each node in its own container.
#
# Usage: ./run_zenoh_extra.sh kill  [--reps 3] [--down-s 10]     experiment 11: router SIGKILL mid-stream
#        ./run_zenoh_extra.sh image [--qos "be rel"] [--images 20] experiment 12: 640x480 image over Zenoh/TCP
#        common: [--out DIR]   (default ./out/zenoh_extra)
#
# kill, per repetition (fresh containers):
#   a_zrouter 172.20.0.2  rmw_zenohd (default router config)
#   a_zsub    172.20.0.3  tcpdump on eth0 + zsub_seq.py           (the capture point)
#   a_zpub    172.20.0.4  zpub_seq.py 300  (std_msgs/String "n=<k>" at 10 Hz, 30 s)
#   at pub n=40 (~4 s): `docker kill a_zrouter` (SIGKILL); +3 s: start a NEW subscriber a_zsub2 (172.20.0.5)
#   while the router is down; at +DOWN s: start rmw_zenohd again at 172.20.0.2; run until the publisher ends.
#   events.txt holds host timestamps (date +%s.%N) of kill / sub2 start / router restart.
# image: router + a_zsub (tcpdump + img_sub.py <qos>) + a_zpub (img_pub.py <qos> N), sender TCP counters.
# Nodes use ZENOH_CONFIG_OVERRIDE connect/endpoints=["tcp/172.20.0.2:7447"];listen/endpoints=["tcp/0.0.0.0:0"]
# (as exp3 in run_experiments.sh, but the router as an IP, not the container name, because the name stops
# resolving while the router container is gone; without the listen override the peers advertise
# tcp/[::1]:<port> and cannot reach each other); everything else is
# the default DEFAULT_RMW_ZENOH_SESSION_CONFIG.json5 of the image.
# Image: lyrical-wire:exp-extra. kill gives recovery times -> EXCLUSIVE lock: flock -x out/exp.lock ...
# Analysis: zenoh_extra_analyze.py kill|image <out dir>
set -euo pipefail
cd "$(dirname "$0")"
export IMG=lyrical-wire:exp-extra
# shellcheck source=lib.sh
source ./lib.sh
MODE="${1:-}"; shift || true
REPS=3; DOWN=10; QOSS="be rel"; NIMG=20; OUT="$PWD/out/zenoh_extra"
while [ $# -gt 0 ]; do
  case "$1" in
    --reps) REPS="$2"; shift 2;; --down-s) DOWN="$2"; shift 2;; --qos) QOSS="$2"; shift 2;;
    --images) NIMG="$2"; shift 2;; --out) OUT="$2"; shift 2;;
    *) echo "unknown option $1" >&2; exit 2;;
  esac
done
case "$MODE" in kill|image) ;; *) sed -n '2,/^set -euo/p' "$0" | sed '$d; s/^# \{0,1\}//'; exit 2;; esac
mkdir -p "$OUT/$MODE"; chmod 777 "$OUT" "$OUT/$MODE"; OUT="$(realpath "$OUT")"
ensure_net
IPR=172.20.0.2; IPS=172.20.0.3; IPP=172.20.0.4; IPS2=172.20.0.5
NAMES=(a_zrouter a_zsub a_zpub a_zsub2)
trap 'clean "${NAMES[@]}"; fix_owner "$OUT" || true' EXIT
[ -f "$OUT/env.txt" ] || write_env "$OUT"
cp zpub_seq.py zsub_seq.py img_pub.py img_sub.py "$OUT/$MODE/"
ZENV=(-e RMW_IMPLEMENTATION=rmw_zenoh_cpp -e "ZENOH_CONFIG_OVERRIDE=connect/endpoints=[\"tcp/$IPR:7447\"];listen/endpoints=[\"tcp/0.0.0.0:0\"]")
now() { date +%s.%N; }
start_router() { docker run -d --name a_zrouter --net "$NET" --ip "$IPR" "$IMG" bash -c "$ROS_SRC; exec ros2 run rmw_zenoh_cpp rmw_zenohd" >/dev/null; wait_tcp_listen a_zrouter 7447 15; }
start_sub() {  # <prefix-in-/o> <cmd>   tcpdump + subscriber in a_zsub
  docker run -d --name a_zsub --net "$NET" --ip "$IPS" "${ZENV[@]}" -v "$OUT/$MODE:/o" "$IMG" bash -c "$ROS_SRC
    cat /proc/net/snmp > $1.snmp0_sub.txt
    tcpdump -i eth0 -U -w $1.raw.pcap 2> $1.tcpdump.log &
    $(ctr_wait_pcap "$1.raw.pcap")
    $2 > $1.sub.log 2>&1 & SP=\$!
    while [ ! -e $1.stop ]; do sleep 0.1; done
    kill -INT \$SP; wait \$SP; cat /proc/net/snmp > $1.snmp1_sub.txt; ss -tin > $1.ss_sub.txt; kill -INT %1; wait %1; exit 0" >/dev/null
}
start_pub() {  # <prefix> <cmd>
  docker run -d --name a_zpub --net "$NET" --ip "$IPP" "${ZENV[@]}" -v "$OUT/$MODE:/o" "$IMG" bash -c "$ROS_SRC
    cat /proc/net/snmp > $1.snmp0_pub.txt; $2 > $1.pub.log 2>&1; RC=\$?
    cat /proc/net/snmp > $1.snmp1_pub.txt; exit \$RC" >/dev/null
}

if [ "$MODE" = kill ]; then
  for rep in $(seq "$REPS"); do
    id=$(printf 'kill_%s_r%02d' "$(date +%m%d%H%M%S)" "$rep"); P="$OUT/kill/$id"; C="/o/$id"
    log "[kill $rep/$REPS] $id"
    clean "${NAMES[@]}"; wait_ips_free 60 $IPR $IPS $IPP $IPS2
    start_router
    start_sub "$C" "python3 /o/zsub_seq.py"
    wait_log "$P.sub.log" 'subscription ready' 30
    start_pub "$C" "python3 /o/zpub_seq.py 300"
    wait_log "$P.pub.log" 'pub n=40' 30
    echo "kill $(now)" > "$P.events.txt"; docker kill a_zrouter >/dev/null; docker rm -f a_zrouter >/dev/null
    sleep 3
    docker run -d --name a_zsub2 --net "$NET" --ip "$IPS2" "${ZENV[@]}" -v "$OUT/kill:/o" "$IMG" \
      bash -c "$ROS_SRC; timeout -s INT 40 python3 /o/zsub_seq.py > $C.sub2.log 2>&1" >/dev/null
    echo "sub2_start $(now)" >> "$P.events.txt"
    sleep "$((DOWN - 3))"
    echo "restart $(now)" >> "$P.events.txt"; start_router; echo "router_listening $(now)" >> "$P.events.txt"
    wait_exit a_zpub 60 > "$P.exit.txt" || echo timeout > "$P.exit.txt"
    echo "pub_end $(now)" >> "$P.events.txt"
    sleep 1; touch "$P.stop"; wait_exit a_zsub 30 >/dev/null || docker kill -s INT a_zsub >/dev/null 2>&1 || true; sleep 1
    docker kill -s INT a_zsub2 >/dev/null 2>&1 || true; sleep 1
    docker logs a_zrouter > "$P.router2.log" 2>&1 || true
    clean "${NAMES[@]}"; rm -f "$P.stop"
  done
else
  for q in $QOSS; do
    id=$(printf 'image_%s_%s' "$(date +%m%d%H%M%S)" "$q"); P="$OUT/image/$id"; C="/o/$id"
    log "[image $q] $id"
    clean "${NAMES[@]}"; wait_ips_free 60 $IPR $IPS $IPP
    start_router
    start_sub "$C" "python3 /o/img_sub.py $q"
    wait_log "$P.sub.log" 'subscription ready' 30
    start_pub "$C" "python3 /o/img_pub.py $q $NIMG"
    wait_exit a_zpub 120 > "$P.exit.txt" || echo timeout > "$P.exit.txt"
    sleep 1.5; touch "$P.stop"; wait_exit a_zsub 30 >/dev/null || docker kill -s INT a_zsub >/dev/null 2>&1 || true; sleep 1
    clean "${NAMES[@]}"; rm -f "$P.stop"
  done
fi
fix_owner "$OUT" || true
for f in "$OUT/$MODE"/*.raw.pcap; do [ -e "$f" ] && filter_pcap "$f" "${f%.raw.pcap}.pcap"; done
log "done -> $OUT/$MODE"

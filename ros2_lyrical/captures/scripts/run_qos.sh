#!/usr/bin/env bash
# Experiment 16 (docs/03 section 18, docs/02 section 1.6): how ROS 2 QoS shows up on the wire.
# Two containers on the Docker network qosnet (172.21.0.0/16): q_pub (172.21.0.3) runs
# qos_pub.py, q_sub (172.21.0.2) runs qos_sub.py and tcpdump -i eth0 udp. Default RMW
# (rmw_fastrtps_cpp, Fast DDS 3.6.2) over UDPv4 (separate containers, so no SHM).
# Light functional runs: wrap every invocation in the SHARED lock, a few cases at a time:
#   flock -s out/exp.lock ./run_qos.sh tl_d1 tl_d10 tl_all vol_d10
# Raw output : ./out/qos/<case>.{raw.pcap,pcap,pub.log,sub.log}
# Committed  : ../exp16_qos_<case>.pcap (filtered like lib.sh filter_pcap), ../results/qos_*
#              (made by qos_summary.py, see --summary)
set -euo pipefail

usage() {
  cat <<'EOF2'
Usage: run_qos.sh [--summary] [case ...]

Cases (each: fresh ROS_DOMAIN_ID, capture of ~5-10 s):
  tl_d1     TRANSIENT_LOCAL KEEP_LAST 1   writer publishes 20 samples, reader joins late
  tl_d10    TRANSIENT_LOCAL KEEP_LAST 10  same
  tl_all    TRANSIENT_LOCAL KEEP_ALL      same
  vol_d10   VOLATILE        KEEP_LAST 10  same (late joiner gets nothing)
  live_auto LIVELINESS AUTOMATIC lease 1.5 s on both ends, 3 samples then 6 s idle
  live_man  LIVELINESS MANUAL_BY_TOPIC lease 1.5 s, assert_liveliness() every 0.5 s for 3 s,
            then stop asserting (reader should see liveliness lost)
  dl_ls     DEADLINE 0.5 s + LIFESPAN 2 s on the writer, DEADLINE 0.5 s on the reader
  mm_rel    BEST_EFFORT writer + RELIABLE reader (incompatible)
  mm_dur    VOLATILE writer + TRANSIENT_LOCAL reader (incompatible)
  loss_d1   RELIABLE VOLATILE KEEP_LAST 1, 50 samples at 200 Hz, tc netem loss 20% on the
            publisher's eth0 (container netns only): NACKed samples no longer in history -> GAP
  loss_d50  same with KEEP_LAST 50 (every NACKed sample still in history -> resent)
            (netem loss is random: GAP/resend counts differ from run to run)
All cases use RELIABLE unless stated, std_msgs/String "q<seq>", topic /qos_demo.
--summary  only (re)build ../results/qos_* and copy the filtered pcaps to ../exp16_qos_*.pcap
No case = all cases (takes ~2 min: too long for one shared-lock hold, run in groups).
EOF2
}

export NET=qosnet SUBNET=172.21.0.0/16 GATEWAY=172.21.0.1 IP_B=172.21.0.2 IP_A=172.21.0.3
source "$(dirname "$0")/lib.sh"
cd "$(dirname "$0")"
HERE=$PWD
OUT="$HERE/out/qos"; RES="$(cd .. && pwd)/results"; CAP="$(cd .. && pwd)"
mkdir -p "$OUT" "$RES"; chmod 777 "$OUT"
ALL="tl_d1 tl_d10 tl_all vol_d10 live_auto live_man dl_ls mm_rel mm_dur loss_d1 loss_d50"

summary() {
  local c
  for c in $ALL; do
    [ -f "$OUT/$c.pcap" ] && cp "$OUT/$c.pcap" "$CAP/exp16_qos_$c.pcap"
  done
  python3 "$HERE/qos_summary.py" --out "$OUT" --res "$RES" --cap "$CAP" --host "$(hostname)"
}

SUMMARY=0; CASES=()
for x in "$@"; do
  case "$x" in
    -h|--help) usage; exit 0;;
    --summary) SUMMARY=1;;
    *) CASES+=("$x");;
  esac
done
if [ "$SUMMARY" = 1 ]; then summary; exit 0; fi
[ ${#CASES[@]} -eq 0 ] && read -r -a CASES <<<"$ALL"

docker image inspect "$IMG" >/dev/null   # never pulls or builds
ensure_net
trap 'clean q_pub q_sub; fix_owner "$OUT" >/dev/null 2>&1 || true' EXIT

start_containers() {
  clean q_pub q_sub
  wait_ips_free 10 "$IP_A" "$IP_B"
  docker run -d --name q_sub --net "$NET" --ip "$IP_B" -v "$HERE:/exp:ro" -v "$OUT:/out" "$IMG" sleep infinity >/dev/null
  docker run -d --name q_pub --cap-add NET_ADMIN --net "$NET" --ip "$IP_A" -v "$HERE:/exp:ro" -v "$OUT:/out" "$IMG" sleep infinity >/dev/null
}

# run_case <case> <domain> <order: late|subfirst> <sub_duration> "<pub args>" "<sub args>"
run_case() {
  local c=$1 dom=$2 order=$3 sdur=$4 pargs=$5 sargs=$6 env
  env="$ROS_SRC; export ROS_DOMAIN_ID=$dom PYTHONUNBUFFERED=1; cd /exp"
  rm -f "$OUT/$c".*
  log "case $c (domain $dom, $order): pub [$pargs] sub [$sargs]"
  docker exec -d q_sub bash -c "tcpdump -i eth0 -U -w /out/$c.raw.pcap udp 2>/dev/null"
  wait_pcap "$OUT/$c.raw.pcap"
  sleep 0.3
  if [ "$order" = late ]; then
    docker exec -d q_pub bash -c "$env; python3 qos_pub.py $pargs > /out/$c.pub.log 2>&1"
    wait_log "$OUT/$c.pub.log" 'PUB [0-9]+$' 20
    local n; n=$(sed -n 's/.*--count \([0-9]*\).*/\1/p' <<<"$pargs"); n=${n:-5}
    wait_log "$OUT/$c.pub.log" "PUB $n\$" 20
    sleep 0.5
    docker exec q_sub bash -c "$env; python3 qos_sub.py --duration $sdur $sargs > /out/$c.sub.log 2>&1"
    wait_log "$OUT/$c.pub.log" 'DONE' 30
  else
    docker exec -d q_sub bash -c "$env; python3 qos_sub.py --duration $sdur $sargs > /out/$c.sub.log 2>&1"
    wait_log "$OUT/$c.sub.log" 'QOS' 20
    docker exec q_pub bash -c "$env; python3 qos_pub.py $pargs > /out/$c.pub.log 2>&1"
    wait_log "$OUT/$c.sub.log" 'DONE' 30
  fi
  sleep 0.5
  docker exec q_sub pkill -INT tcpdump || true
  sleep 0.5
  filter_pcap "$OUT/$c.raw.pcap" "$OUT/$c.pcap"
  log "  -> $(stat -c %s "$OUT/$c.pcap") B filtered pcap"
}

start_containers
for c in "${CASES[@]}"; do
  case "$c" in
    tl_d1)   run_case tl_d1   61 late 3 "--durability transient_local --depth 1 --count 20 --rate 50 --linger 6" \
                                        "--durability transient_local --depth 20";;
    tl_d10)  run_case tl_d10  62 late 3 "--durability transient_local --depth 10 --count 20 --rate 50 --linger 6" \
                                        "--durability transient_local --depth 20";;
    tl_all)  run_case tl_all  63 late 3 "--durability transient_local --history keep_all --count 20 --rate 50 --linger 6" \
                                        "--durability transient_local --depth 20";;
    vol_d10) run_case vol_d10 64 late 3 "--depth 10 --count 20 --rate 50 --linger 6" "--depth 20";;
    live_auto) run_case live_auto 65 subfirst 10 \
                 "--liveliness automatic --lease 1.5 --count 3 --rate 10 --wait-match --linger 6" \
                 "--liveliness automatic --lease 1.5";;
    live_man)  run_case live_man 66 subfirst 11 \
                 "--liveliness manual_by_topic --lease 1.5 --count 3 --rate 10 --wait-match --linger 7 --assert-every 0.5 --assert-for 3" \
                 "--liveliness manual_by_topic --lease 1.5";;
    dl_ls)   run_case dl_ls 67 subfirst 7 "--deadline 0.5 --lifespan 2 --count 5 --rate 10 --wait-match --linger 3" \
                                          "--deadline 0.5";;
    mm_rel)  run_case mm_rel 68 subfirst 6 "--reliability best_effort --count 10 --rate 10 --linger 2" "";;
    mm_dur)  run_case mm_dur 69 subfirst 6 "--count 10 --rate 10 --linger 2" "--durability transient_local";;
    loss_d1|loss_d50)
             d=${c#loss_d}
             docker exec q_pub tc qdisc replace dev eth0 root netem loss 20%
             run_case "$c" $((70 + ${#d})) subfirst 6 "--depth $d --count 50 --rate 200 --wait-match --linger 2" "--depth 50"
             docker exec q_pub tc qdisc del dev eth0 root || true;;
    *) log "unknown case $c"; usage >&2; exit 1;;
  esac
done

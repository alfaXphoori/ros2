#!/usr/bin/env bash
# Reproduce the ROS 2 Lyrical wire experiments (ros2_lyrical/docs/03_wire_experiments.md).
# Needs: Docker (user in the docker group), python3 on the host for the summary (optional).
# Usage: ./run_experiments.sh [--rebuild]      (REBUILD=1 works too; OUT=<dir> to change ./out)
# Output in ./out/ (git-ignored):
#   env.txt, dpkg_*.txt, ros2_doctor.txt     environment of the run (lib.sh write_env)
#   expN_*.raw.pcap                          what tcpdump wrote (unfiltered)
#   expN_*.pcap                              filtered like the committed captures (docs/03 §9.1)
#   expN_*.listener.log / .talker.log        node output;  expN_*.snmp.txt  /proc/net/snmp of Host B
#   expN_*.tcpdump.log                       tcpdump's "captured / dropped by kernel" counts
#   summary.txt                              the numbers docs/03 compares against
set -euo pipefail
cd "$(dirname "$0")"
# shellcheck source=lib.sh
source ./lib.sh
OUT="${OUT:-$PWD/out}"; mkdir -p "$OUT"; chmod 777 "$OUT"
T0=$(date +%s)

ensure_image "${1:-}"
ensure_net
trap 'clean; fix_owner "$OUT" || true' EXIT
log "environment -> $OUT/env.txt"
write_env "$OUT"

# run_pair <name> <listener cmd> <talker cmd> <listener-ready ERE or ""> [extra docker args...]
#  Host B ($IP_B): tcpdump on eth0 -> /out/<name>.raw.pcap, then the listener command.
#  Host A ($IP_A): the talker command, started once Host B is ready:
#    - the pcap header exists (tcpdump is capturing) and the listener process was started, and
#    - if an ERE is given, it appeared in the listener log (img_sub.py prints "subscription ready");
#      otherwise (demo listener prints nothing until data arrives) 1 s after the listener started,
#      which is the gap the 2026-11-24 runs had (sleep 1 in Host B, sleep 2 on the host).
run_pair() {
  local name="$1" lcmd="$2" tcmd="$3" ready="$4"; shift 4
  clean; rm -f "$OUT/$name".*
  wait_ips_free 60 "$IP_B" "$IP_A"
  docker run -d --name hostB --net "$NET" --ip "$IP_B" -v "$PWD:/exp:ro" -v "$OUT:/out" "$@" "$IMG" bash -c "$ROS_SRC
    tcpdump -i eth0 -U -w /out/$name.raw.pcap 2>/out/$name.tcpdump.log &
    $(ctr_wait_pcap "/out/$name.raw.pcap")
    touch /out/$name.started
    $lcmd > /out/$name.listener.log 2>&1
    grep -A1 '^Udp:' /proc/net/snmp > /out/$name.snmp.txt; grep -A1 '^Ip:' /proc/net/snmp >> /out/$name.snmp.txt
    kill %1; sleep 1" >/dev/null
  wait_pcap "$OUT/$name.raw.pcap" 10
  wait_file "$OUT/$name.started" 0 10
  if [ -n "$ready" ]; then wait_log "$OUT/$name.listener.log" "$ready" 20; else sleep 1; fi
  docker run -d --name hostA --net "$NET" --ip "$IP_A" -v "$PWD:/exp:ro" "$@" "$IMG" bash -c "$ROS_SRC; $tcmd" >/dev/null
  echo "hostA exit $(wait_exit hostA 60)" > "$OUT/$name.exit.txt"
  docker logs hostA > "$OUT/$name.talker.log" 2>&1 || true
  echo "hostB exit $(wait_exit hostB 60)" >> "$OUT/$name.exit.txt"
  rm -f "$OUT/$name.started"
  filter_pcap "$OUT/$name.raw.pcap" "$OUT/$name.pcap"
}

log "[1] Fast DDS default: demo talker -> listener (two containers)"
run_pair exp1_fastdds_default "timeout 14 ros2 run demo_nodes_cpp listener" "timeout 10 ros2 run demo_nodes_cpp talker" ""

log "[2] 640x480 rgb8 Image, RELIABLE"
run_pair exp2_image_reliable "timeout 12 python3 /exp/img_sub.py rel" "python3 /exp/img_pub.py rel 5" "subscription ready"

log "[3] rmw_zenoh_cpp via one router (router $IP_ZROUTER, listener $IP_ZLISTENER, talker $IP_ZTALKER)"
clean; rm -f "$OUT"/exp3_zenoh.*
wait_ips_free 60 "$IP_ZROUTER" "$IP_ZLISTENER" "$IP_ZTALKER"
ZENV=(-e RMW_IMPLEMENTATION=rmw_zenoh_cpp -e 'ZENOH_CONFIG_OVERRIDE=connect/endpoints=["tcp/zrouter:7447"];listen/endpoints=["tcp/0.0.0.0:0"]')
docker run -d --name zrouter --net "$NET" --ip "$IP_ZROUTER" "$IMG" bash -c "$ROS_SRC; timeout 30 ros2 run rmw_zenoh_cpp rmw_zenohd" >/dev/null
wait_tcp_listen zrouter 7447 15
docker run -d --name hostB --net "$NET" --ip "$IP_ZLISTENER" -v "$OUT:/out" "${ZENV[@]}" "$IMG" bash -c "$ROS_SRC
  tcpdump -i eth0 -U -w /out/exp3_zenoh.raw.pcap 2>/out/exp3_zenoh.tcpdump.log &
  $(ctr_wait_pcap /out/exp3_zenoh.raw.pcap)
  touch /out/exp3_zenoh.started
  timeout 14 ros2 run demo_nodes_cpp listener > /out/exp3_zenoh.listener.log 2>&1; kill %1; sleep 1" >/dev/null
wait_pcap "$OUT/exp3_zenoh.raw.pcap" 10
wait_file "$OUT/exp3_zenoh.started" 0 10
sleep 1   # demo listener has no ready line; same 1 s gap as run_pair
docker run -d --name hostA --net "$NET" --ip "$IP_ZTALKER" "${ZENV[@]}" "$IMG" bash -c "$ROS_SRC; timeout 9 ros2 run demo_nodes_cpp talker" >/dev/null
echo "hostA exit $(wait_exit hostA 60)" > "$OUT/exp3_zenoh.exit.txt"
docker logs hostA > "$OUT/exp3_zenoh.talker.log" 2>&1 || true
echo "hostB exit $(wait_exit hostB 60)" >> "$OUT/exp3_zenoh.exit.txt"
rm -f "$OUT/exp3_zenoh.started"
filter_pcap "$OUT/exp3_zenoh.raw.pcap" "$OUT/exp3_zenoh.pcap"

log "[4] same container (Fast DDS SHM): data should not appear on the network"
clean; rm -f "$OUT"/exp4_*
# default bridge (not $NET), as in the 2026-11-24 run; the sleeps inside are part of the experiment
docker run --rm --shm-size=256m -v "$OUT:/out" "$IMG" bash -c "$ROS_SRC
  tcpdump -i any -U -w /out/exp4_samehost_shm.raw.pcap 2>/out/exp4_samehost_shm.tcpdump.log &
  $(ctr_wait_pcap /out/exp4_samehost_shm.raw.pcap)
  ros2 run demo_nodes_cpp listener > /out/exp4.listener.log 2>&1 &
  sleep 1; timeout 6 ros2 run demo_nodes_cpp talker > /dev/null 2>&1 &
  sleep 4; ls -la /dev/shm > /out/exp4_devshm.txt
  ps -eLo comm | grep '^dds\.' | sort | uniq -c > /out/exp4_threads.txt
  sleep 4; kill %2 %1 2>/dev/null || true; sleep 1"
filter_pcap "$OUT/exp4_samehost_shm.raw.pcap" "$OUT/exp4_samehost_shm.pcap"

# Experiments 5-6 are the two end points of the receive-buffer question; run_rcvbuf_sweep.sh
# (docs/03 §4.2) sweeps it properly with repetitions. They stay here unchanged for comparison.
log "[5] Image BEST_EFFORT, default receive buffer"
run_pair exp5_image_besteffort "timeout 16 python3 /exp/img_sub.py be" "python3 /exp/img_pub.py be 20" "subscription ready"

log "[6] Image BEST_EFFORT, 4 MiB receive buffer (Fast DDS XML profile)"
run_pair exp6_image_besteffort_bigbuf "timeout 16 python3 /exp/img_sub.py be" "python3 /exp/img_pub.py be 20" "subscription ready" \
  -e FASTDDS_DEFAULT_PROFILES_FILE=/exp/bigbuf.xml

# ---- summary: the numbers docs/03 §2.1, §4.1 and §4.2 compare against ----
snmp() {  # <snmp.txt> <Udp|Ip> <field>  (column looked up by name)
  awk -v p="$2:" -v f="$3" '$1==p && !h {for(i=2;i<=NF;i++) if($i==f) c=i; h=1; next} $1==p && h {print $c}' "$1"
}
PEEK="$PWD/../../tools/rtps_peek.py"
{
  echo "run finished $(date -Is), wall time $(( $(date +%s) - T0 )) s"
  e=exp1_fastdds_default
  echo "[1] first 'Hello World: 1' frame in $e.pcap (filtered): $(docker run --rm --network none -v "$OUT:/o:ro" "$IMG" \
      tshark -r /o/$e.pcap -Y 'frame contains "Hello World: 1"' -T fields -e frame.number -e frame.len 2>/dev/null | head -1 | tr '\t' ' ') (frame-no length)"
  echo "    frames: raw $(docker run --rm --network none -v "$OUT:/o:ro" "$IMG" capinfos -c -M /o/$e.raw.pcap 2>/dev/null | awk '/Number/{print $NF}') filtered $(docker run --rm --network none -v "$OUT:/o:ro" "$IMG" capinfos -c -M /o/$e.pcap 2>/dev/null | awk '/Number/{print $NF}')"
  e=exp2_image_reliable
  echo "[2] received $(grep -c ' got ' "$OUT/$e.listener.log" || true)/5 · RcvbufErrors=$(snmp "$OUT/$e.snmp.txt" Udp RcvbufErrors) ReasmOKs=$(snmp "$OUT/$e.snmp.txt" Ip ReasmOKs)"
  if command -v python3 >/dev/null; then
    echo "    NACK_FRAG: $(python3 "$PEEK" sms "$OUT/$e.pcap" NACK_FRAG | grep -c 'NACK_FRAG' || true)"
    python3 "$PEEK" sms "$OUT/$e.pcap" NACK_FRAG | grep -o 'SN .*' | sed 's/^/      /' || true
    echo "    DATA_FRAG per writer/SN:"
    python3 "$PEEK" sms "$OUT/$e.pcap" DATA_FRAG | grep -o 'writer [0-9a-f.]* SN [0-9]*' | sort | uniq -c | sed 's/^/     /' || true
  fi
  for e in exp5_image_besteffort exp6_image_besteffort_bigbuf; do
    echo "[${e:3:1}] $e: received $(grep -c ' got ' "$OUT/$e.listener.log" || true)/20 · RcvbufErrors=$(snmp "$OUT/$e.snmp.txt" Udp RcvbufErrors) ReasmOKs=$(snmp "$OUT/$e.snmp.txt" Ip ReasmOKs)"
    if command -v python3 >/dev/null; then
      echo "    DATA_FRAG per SN in capture: $(python3 "$PEEK" sms "$OUT/$e.pcap" DATA_FRAG | grep -o 'SN [0-9]*' | sort | uniq -c | awk '{print $1}' | sort -n | uniq -c | awk '{printf "%s SN x %s frags; ", $1, $2}')"
    fi
  done
} > "$OUT/summary.txt"
cat "$OUT/summary.txt"
log "done -> $OUT"

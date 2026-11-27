#!/usr/bin/env bash
# Measured application-level end-to-end latency (rclpy) for ros2_lyrical/docs/03 section 10.
# Self-contained: needs Docker and the local image lyrical-wire:exp (built from ./Dockerfile).
# Raw data: ./out/latency/<config>/run_XX.{csv,meta.json,snmp,pub.log,sub.log}
# Summary : ../results/latency_summary.{json,csv}, ../results/latency_env.txt
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: run_latency.sh [options]

  --runs N            independent runs per config (fresh processes + fresh ROS_DOMAIN_ID)  [30]
  --small-count N     messages per run, small payload                                     [200]
  --small-rate HZ     publish rate, small payload                                         [100]
  --image-count N     messages per run, 640x480 rgb8 image                                [50]
  --image-rate HZ     publish rate, image                                                 [10]
  --warmup N          samples (by sequence number) discarded at the start of each run     [10]
  --configs LIST      comma list of configs (default: all)
                        small_cross, small_same, small_same_udp, image_cross_rel,
                        image_same_rel, image_cross_be, image_cross_rel_bigbuf
  --transport-check   also run one same-container check with tcpdump -i any + /dev/shm listing
  --inner-check P     (internal) body of --transport-check, run inside the container
  --analyze-only      skip measurement, only run analyze_latency.py on ./out/latency
  -h, --help          this help

Configs
  *_cross   publisher container 172.20.0.3 -> subscriber container 172.20.0.2 on Docker
            network rosnet (veth + bridge). Default Fast DDS transports; SHM cannot span
            containers (separate /dev/shm and IPC namespaces) so data goes over UDPv4.
  *_same    publisher and subscriber in ONE container, default transports (SHM expected;
            --transport-check verifies it).
  _same_udp as *_same but FASTDDS_BUILTIN_TRANSPORTS=UDPv4 on both ends (UDP over
            loopback, no SHM) to separate the effect of SHM from "same container".
  _rel/_be  RELIABLE / BEST_EFFORT, KEEP_LAST depth 10 for every config.
  _bigbuf   subscriber only gets FASTDDS_DEFAULT_PROFILES_FILE=bigbuf.xml
            (UDPv4 receiveBufferSize 4 MiB; kernel caps it at net.core.rmem_max).

Serialise with other experiments so CPU contention does not corrupt the latency:
  flock /path/to/exp.lock ./run_latency.sh

Two real machines (protocol only; not run here)
  The same lat_pub.py / lat_sub.py run unchanged on two hosts with ROS 2 Lyrical:
    host B: python3 lat_sub.py --payload small --count 200 --clock realtime --out run_00
    host A: python3 lat_pub.py --payload small --count 200 --rate 100 --clock realtime
  Clocks then differ: synchronise with PTP (ptp4l + phc2sys, hardware timestamping) or at
  least chrony on an idle LAN, record the offset bound during the run (e.g. `pmc -u -b 0
  'GET CURRENT_DATA_SET'` or `chronyc tracking` before and after) and report it next to
  every latency figure: a latency below the offset bound is not meaningful.
  Copy run_XX.csv / run_XX.meta.json into out/latency/<config>/ and run analyze_latency.py.
EOF
}

inner_check() {  # runs INSIDE the container: $1 = small|image
  local p=$1 n=100 rate=100 i
  [ "$p" = image ] && { n=20; rate=10; }
  set +eu; source /opt/ros/lyrical/setup.bash
  tcpdump -i any -U -w "/tmp/$p.pcap" 2>/dev/null & local td=$!
  sleep 1
  python3 /exp/lat_sub.py --payload "$p" --count "$n" --idle 3 --out "/tmp/$p" > "/tmp/$p.sub.log" 2>&1 &
  local sp=$!
  ( for i in $(seq 1 16); do sleep 0.5; ls -la /dev/shm; done > "/tmp/$p.shm" ) &
  python3 /exp/lat_pub.py --payload "$p" --count "$n" --rate "$rate" > /dev/null 2>&1
  wait "$sp"; sleep 1; kill "$td"; wait 2>/dev/null || true
  echo "== $p: $(tail -n1 "/tmp/$p.sub.log")"
  echo "-- /dev/shm fastdds entries seen during the run (sampled every 0.5 s): size name"
  grep fastdds "/tmp/$p.shm" | awk '{print $5, $NF}' | sort -u -k2
  echo "-- writerEntityId of every RTPS submessage that carries one, all interfaces"
  echo "   (user writers end in 02/03, builtin writers in c2/c3)"
  tshark -r "/tmp/$p.pcap" -Y rtps -T fields -E occurrence=a -e rtps.sm.wrEntityId 2>/dev/null \
    | tr ',\t' '\n\n' | grep . | sort | uniq -c
  echo "-- user-writer submessages on the wire: $(tshark -r "/tmp/$p.pcap" -Y rtps -T fields -E occurrence=a \
    -e rtps.sm.wrEntityId 2>/dev/null | tr ',\t' '\n\n' | grep -Ec '0[23]$')"
}
if [ "${1:-}" = --inner-check ]; then inner_check "$2"; exit 0; fi

RUNS=30; SMALL_COUNT=200; SMALL_RATE=100; IMAGE_COUNT=50; IMAGE_RATE=10; WARMUP=10
CONFIGS="small_cross,small_same,small_same_udp,image_cross_rel,image_same_rel,image_cross_be,image_cross_rel_bigbuf"
TCHECK=0; ANALYZE_ONLY=0
while [ $# -gt 0 ]; do
  case "$1" in
    --runs) RUNS=$2; shift 2;;
    --small-count) SMALL_COUNT=$2; shift 2;;
    --small-rate) SMALL_RATE=$2; shift 2;;
    --image-count) IMAGE_COUNT=$2; shift 2;;
    --image-rate) IMAGE_RATE=$2; shift 2;;
    --warmup) WARMUP=$2; shift 2;;
    --configs) CONFIGS=$2; shift 2;;
    --transport-check) TCHECK=1; shift;;
    --analyze-only) ANALYZE_ONLY=1; shift;;
    -h|--help) usage; exit 0;;
    *) echo "unknown option: $1" >&2; usage >&2; exit 1;;
  esac
done

cd "$(dirname "$0")"
HERE=$PWD
OUT="${LAT_OUT:-$HERE/out/latency}"; RES="${LAT_RES:-$(cd .. && pwd)/results}"   # override both for a trial run that must not overwrite the committed summary
mkdir -p "$OUT" "$RES"; chmod 777 "$OUT"
IMG=lyrical-wire:exp
SRC='source /opt/ros/lyrical/setup.bash'
NAMES="lat_sub lat_pub lat_same lat_check"
clean() { docker rm -f $NAMES >/dev/null 2>&1 || true; }

analyze() {
  python3 "$HERE/analyze_latency.py" --in "$OUT" --warmup "$WARMUP" \
    --json "$RES/latency_summary.json" --csv "$RES/latency_summary.csv"
}
if [ "$ANALYZE_ONLY" = 1 ]; then analyze; exit 0; fi

trap clean EXIT
docker image inspect "$IMG" >/dev/null   # never pulls or builds
docker network inspect rosnet >/dev/null 2>&1 || docker network create --subnet 172.20.0.0/16 rosnet >/dev/null

# ---- environment record (read-only) ----
{
  echo "date: $(date -Is)"
  echo "uname: $(uname -a)"
  echo "cpu: $(grep -m1 'model name' /proc/cpuinfo | cut -d: -f2- | sed 's/^ //')"
  echo "nproc: $(nproc)"
  echo "governor: $(cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor 2>/dev/null || echo unreadable)"
  echo "docker: $(docker version --format '{{.Server.Version}}' 2>/dev/null)"
  echo "image: $IMG $(docker image inspect --format '{{.Id}}' "$IMG")"
  echo "host net.core.rmem_default: $(cat /proc/sys/net/core/rmem_default)"
  echo "host net.core.rmem_max: $(cat /proc/sys/net/core/rmem_max)"
  echo "loadavg_before: $(cat /proc/loadavg)"
  echo "params: runs=$RUNS small_count=$SMALL_COUNT small_rate=$SMALL_RATE image_count=$IMAGE_COUNT image_rate=$IMAGE_RATE warmup=$WARMUP"
  echo "configs: $CONFIGS"
} > "$RES/latency_env.txt"

udp_line() { docker exec "$1" awk '/^Udp:/{n++} /^Udp:/ && n==2 {print; exit}' /proc/net/snmp; }

start_containers() {  # $1 = cross|same
  clean
  if [ "$1" = cross ]; then
    docker run -d --name lat_sub --net rosnet --ip 172.20.0.2 -v "$HERE:/exp:ro" -v "$OUT:/out" "$IMG" sleep infinity >/dev/null
    docker run -d --name lat_pub --net rosnet --ip 172.20.0.3 -v "$HERE:/exp:ro" -v "$OUT:/out" "$IMG" sleep infinity >/dev/null
    SUBC=lat_sub; PUBC=lat_pub
  else
    docker run -d --name lat_same --net rosnet --ip 172.20.0.2 -v "$HERE:/exp:ro" -v "$OUT:/out" "$IMG" sleep infinity >/dev/null
    SUBC=lat_same; PUBC=lat_same
  fi
}

run_config() {  # $1 = config name
  local cfg=$1 topo payload rel count rate subenv="" pubenv=""
  case "$cfg" in
    small_cross) topo=cross; payload=small; rel=reliable;;
    small_same) topo=same; payload=small; rel=reliable;;
    small_same_udp) topo=same; payload=small; rel=reliable
      subenv="FASTDDS_BUILTIN_TRANSPORTS=UDPv4"; pubenv=$subenv;;
    image_cross_rel) topo=cross; payload=image; rel=reliable;;
    image_same_rel) topo=same; payload=image; rel=reliable;;
    image_cross_be) topo=cross; payload=image; rel=best_effort;;
    image_cross_rel_bigbuf) topo=cross; payload=image; rel=reliable
      subenv="FASTDDS_DEFAULT_PROFILES_FILE=/exp/bigbuf.xml";;
    *) echo "unknown config $cfg" >&2; return 1;;
  esac
  if [ "$payload" = small ]; then count=$SMALL_COUNT; rate=$SMALL_RATE; else count=$IMAGE_COUNT; rate=$IMAGE_RATE; fi
  local d="$OUT/$cfg"; rm -rf "$d"; mkdir -p "$d"; chmod 777 "$d"
  echo "{\"config\":\"$cfg\",\"topology\":\"$topo\",\"payload\":\"$payload\",\"reliability\":\"$rel\",\"depth\":10,\"count\":$count,\"rate_hz\":$rate,\"runs\":$RUNS,\"sub_env\":\"$subenv\",\"pub_env\":\"$pubenv\"}" > "$d/config.json"
  start_containers "$topo"
  local r rr dom
  for ((r = 0; r < RUNS; r++)); do
    rr=$(printf '%02d' "$r"); dom=$((100 + r))   # fresh domain per run: no stale participants
    echo "before $(udp_line "$SUBC")" > "$d/run_$rr.snmp"
    docker exec -e ROS_DOMAIN_ID=$dom ${subenv:+-e $subenv} "$SUBC" bash -c "$SRC
      exec python3 /exp/lat_sub.py --payload $payload --count $count --reliability $rel --idle 3 --timeout $((count / rate + 30)) --out /out/$cfg/run_$rr" \
      > "$d/run_$rr.sub.log" 2>&1 &
    local sp=$!
    if [ "$r" = 0 ] && [ "$topo" = cross ]; then
      ( for _ in 1 2 3 4 5 6 7 8 9 10; do   # SO_RCVBUF actually granted to the subscriber
          sleep 0.5; docker exec "$SUBC" ss -uamnp > "$d/run_00.ss.txt" 2>&1 || true
          grep -q python3 "$d/run_00.ss.txt" && break
        done ) &
    fi
    docker exec -e ROS_DOMAIN_ID=$dom ${pubenv:+-e $pubenv} "$PUBC" bash -c "$SRC
      exec python3 /exp/lat_pub.py --payload $payload --count $count --rate $rate --reliability $rel --pub-out /out/$cfg/run_$rr.pub.csv" \
      > "$d/run_$rr.pub.log" 2>&1 || echo "  run $rr: publisher failed (see run_$rr.pub.log)"
    wait "$sp" || echo "  run $rr: subscriber failed (see run_$rr.sub.log)"
    wait || true
    echo "after $(udp_line "$SUBC")" >> "$d/run_$rr.snmp"
    printf '  %s run %s: %s\n' "$cfg" "$rr" "$(tail -n1 "$d/run_$rr.sub.log")"
  done
  clean
}

transport_check() {  # one same-container run per payload with tcpdump -i any + /dev/shm listing
  local f="$RES/latency_transport_check.txt" p
  clean
  docker run -d --name lat_check --net rosnet --ip 172.20.0.2 -v "$HERE:/exp:ro" "$IMG" sleep infinity >/dev/null
  echo "same-container transport check ($(date -Is)), ROS_DOMAIN_ID=99, default Fast DDS transports" > "$f"
  for p in small image; do
    docker exec -e ROS_DOMAIN_ID=99 lat_check bash /exp/run_latency.sh --inner-check "$p" >> "$f" 2>&1
  done
  clean
}
T0=$(date +%s)
IFS=, read -ra CFG_LIST <<< "$CONFIGS"
for c in "${CFG_LIST[@]}"; do
  echo "[$(date +%T)] config $c"
  run_config "$c"
done
[ "$TCHECK" = 1 ] && { echo "[$(date +%T)] transport check"; transport_check; }
echo "wall_clock_s: $(( $(date +%s) - T0 ))" >> "$RES/latency_env.txt"
echo "loadavg_after: $(cat /proc/loadavg)" >> "$RES/latency_env.txt"
analyze
echo "done -> $OUT , $RES"

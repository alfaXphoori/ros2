#!/usr/bin/env bash
# Experiment 17 (docs/03 section 19, docs/02 section 6.5): ONE message traced across layers,
# user space (ros2_tracing / LTTng-UST) + wire (tcpdump on both veth ends), no host privileges.
#
# Layout: two containers on Docker network trcnet (172.23.0.0/16), Fast DDS default transports
# (UDPv4 between containers, SHM cannot span them):
#   e_trc_a  172.23.0.3  demo_nodes_cpp talker   + lttng-sessiond (userspace only) + tcpdump eth0
#   e_trc_b  172.23.0.2  demo_nodes_cpp listener + lttng-sessiond (userspace only) + tcpdump eth0
# Both containers share the host kernel clocks (CLOCK_MONOTONIC, CLOCK_REALTIME): no clock sync
# is needed between them; LTTng (monotonic) and tcpdump (realtime) are aligned with an offset
# measured inside each container before and after the run (clock_offset.py).
#
# Raw data: ./out/trace/run/{A,B}/ (CTF traces, raw + filtered pcaps, logs, clock offsets)
# Results : ../results/trace_one_sample.csv, trace_stage_stats.csv, trace_env.txt,
#           trace_babeltrace_excerpt.txt   (written by trace_analyze.py)
#
# Usage: run_trace.sh [--seconds S] [--sample N] [--analyze-only]
#   --seconds S     how long the talker runs (it publishes at 1 Hz)        [30]
#   --sample N      which "Hello World: N" goes into the one-sample table   [10]
#   --analyze-only  only re-run trace_analyze.py on ./out/trace/run
# Timing run, serialise it:  flock -x out/exp.lock ./run_trace.sh
# Nothing here changes host settings: LTTng kernel domain is NOT used (needs kernel modules).
set -euo pipefail

SECONDS_RUN=30; SAMPLE=10; ANALYZE_ONLY=0
while [ $# -gt 0 ]; do
  case "$1" in
    --seconds) SECONDS_RUN=$2; shift 2;;
    --sample) SAMPLE=$2; shift 2;;
    --analyze-only) ANALYZE_ONLY=1; shift;;
    -h|--help) sed -n '2,22p' "$0"; exit 0;;
    *) echo "unknown option: $1" >&2; exit 1;;
  esac
done

export NET=trcnet SUBNET=172.23.0.0/16 GATEWAY=172.23.0.1 IP_B=172.23.0.2 IP_A=172.23.0.3
export IMG=lyrical-wire:exp-extra
cd "$(dirname "$0")"
HERE=$PWD
# shellcheck source=lib.sh
source "$HERE/lib.sh"
OUT="$HERE/out/trace/run"; RES="$(cd .. && pwd)/results"
NAMES=(e_trc_a e_trc_b)

analyze() {
  docker run --rm --network none -v "$HERE:/exp:ro" -v "$OUT:/out" -v "$RES:/res" "$IMG" \
    python3 /exp/trace_analyze.py --in /out --res /res --sample "$SAMPLE" --host-name "$(hostname)"
  fix_owner "$RES" 2>/dev/null || true
}
if [ "$ANALYZE_ONLY" = 1 ]; then analyze; exit 0; fi

trap 'clean "${NAMES[@]}"' EXIT
docker image inspect "$IMG" >/dev/null   # never pulls or builds
ensure_net
clean "${NAMES[@]}"
wait_ips_free 10 "$IP_A" "$IP_B"
rm -rf "$OUT"; mkdir -p "$OUT/A" "$OUT/B"; chmod -R 777 "$OUT"

# inner script: $1 = A|B, $2 = talker|listener ; started detached, stops on SIGTERM to the node
cat > "$OUT/inner.sh" <<'EOS'
#!/bin/bash
set +u
side=$1; node=$2; secs=$3; d=/out/$side
source /opt/ros/lyrical/setup.bash
lttng-sessiond --daemonize --no-kernel >"$d/sessiond.log" 2>&1
lttng create trc --output="$d/ctf" >"$d/lttng.log" 2>&1
lttng enable-event -u 'ros2:*' >>"$d/lttng.log" 2>&1
lttng add-context -u -t vpid -t vtid -t procname >>"$d/lttng.log" 2>&1
lttng start >>"$d/lttng.log" 2>&1
python3 /exp/clock_offset.py > "$d/clock_before.txt"
tcpdump -J -i eth0 > "$d/tstamp_types.txt" 2>&1
tcpdump -i eth0 -U --time-stamp-precision=nano -w "$d/$side.raw.pcap" udp 2>"$d/tcpdump.log" &
td=$!
for _i in $(seq 50); do [ "$(stat -c %s "$d/$side.raw.pcap" 2>/dev/null || echo 0)" -ge 24 ] && break; sleep 0.1; done
timeout -s INT "$secs" ros2 run demo_nodes_cpp "$node" >"$d/$node.log" 2>&1
sleep 1
kill -INT $td; wait $td 2>/dev/null
lttng stop >>"$d/lttng.log" 2>&1
lttng list trc >>"$d/lttng.log" 2>&1
lttng destroy >>"$d/lttng.log" 2>&1
python3 /exp/clock_offset.py > "$d/clock_after.txt"
echo done > "$d/done"
EOS
chmod 755 "$OUT/inner.sh"

log "env -> $OUT/env"
{ # read-only, unprivileged host checks (what kernel-side tracing would need); nothing is changed
  echo "# host checks (read only, unprivileged) $(date -Is)"
  echo "uname -r: $(uname -r)"
  echo "kernel.perf_event_paranoid = $(cat /proc/sys/kernel/perf_event_paranoid 2>&1)"
  echo "kernel.unprivileged_bpf_disabled = $(cat /proc/sys/kernel/unprivileged_bpf_disabled 2>&1)"
  echo "kernel.kptr_restrict = $(cat /proc/sys/kernel/kptr_restrict 2>&1)"
  echo "tracefs readable by this user: $( [ -r /sys/kernel/tracing/events ] && echo yes || echo no)"
  echo "lttng kernel modules installed for $(uname -r): $(find /lib/modules/"$(uname -r)" -name 'lttng*.ko*' 2>/dev/null | wc -l)"
  echo "bpftrace on host: $(command -v bpftrace || echo absent)  perf on host: $(command -v perf || echo absent)"
  echo "clocksource: $(cat /sys/devices/system/clocksource/clocksource0/current_clocksource 2>&1)"
  echo "governor cpu0: $(cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor 2>&1)"
  echo "loadavg_before: $(cat /proc/loadavg)"
} > "$OUT/host_checks.txt"
{
  echo "# run parameters"
  echo "date: $(date -Is)  seconds=$SECONDS_RUN sample=$SAMPLE"
  echo "image: $IMG $(docker image inspect --format '{{.Id}}' "$IMG")"
  echo "docker: $(docker version --format '{{.Server.Version}}' 2>/dev/null)"
  echo "network: $NET $SUBNET  talker A=$IP_A  listener B=$IP_B  ROS_DOMAIN_ID=17  RMW default (rmw_fastrtps_cpp)"
  docker run --rm --network none "$IMG" bash -c 'source /opt/ros/lyrical/setup.bash
    echo "tracetools status: $(ros2 run tracetools status 2>&1)"; lttng --version | head -1; babeltrace2 --version | head -1
    tcpdump --version 2>&1 | head -1
    dpkg -l | awk "/ros-lyrical-(fastdds|rmw-fastrtps-cpp|rclcpp|rcl|tracetools|demo-nodes-cpp) /{print \$2, \$3}"
    dpkg -l | awk "/liblttng-ust1t64 /{print \$2, \$3}"'
} > "$OUT/meta.txt" 2>&1
write_env "$OUT/env" >/dev/null 2>&1 || log "write_env failed (non-fatal)"
for side in B A; do
  if [ $side = B ]; then n=e_trc_b; ip=$IP_B; else n=e_trc_a; ip=$IP_A; fi
  docker run -d --name "$n" --hostname "$n" --net "$NET" --ip "$ip" -e ROS_DOMAIN_ID=17 \
    -v "$HERE:/exp:ro" -v "$OUT:/out" "$IMG" sleep infinity >/dev/null
done
log "listener (B) for $((SECONDS_RUN + 8)) s, talker (A) for $SECONDS_RUN s"
docker exec -d e_trc_b bash /out/inner.sh B listener $((SECONDS_RUN + 8))
sleep 4   # listener + its trace session are up before the first publish
docker exec e_trc_a bash /out/inner.sh A talker "$SECONDS_RUN"
wait_file "$OUT/B/done" 1 30
echo "loadavg_after: $(cat /proc/loadavg)" >> "$OUT/host_checks.txt"
for side in A B; do echo "tcpdump -J (container $side eth0): $(tr '\n' ' ' < "$OUT/$side/tstamp_types.txt")" >> "$OUT/host_checks.txt"; done
for side in A B; do filter_pcap "$OUT/$side/$side.raw.pcap" "$OUT/$side/$side.pcap"; done
fix_owner "$OUT"
clean "${NAMES[@]}"
docker network rm "$NET" >/dev/null 2>&1 || true
analyze
log "done: results in $RES/trace_*"

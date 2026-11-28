#!/usr/bin/env bash
# Receive-buffer sweep and tc-shaped variant of the image experiments (docs/03 §9, §11, §12).
#
# Each "arm" is one configuration; every run = one fresh receiver container (swB, $IP_B: tcpdump on
# eth0 + img_sub.py) and one fresh sender container (swA, $IP_A: img_pub.py <qos> <n>), so the
# /proc/net/snmp counters of the receiver netns contain only that run.
#
# Usage: ./run_rcvbuf_sweep.sh [options]
#   --arms LIST    comma-separated arm tokens  [qos:]name[*reps]   (qos defaults to --qos)
#                  name = noxml        no XML on either side (Fast DDS defaults)
#                         <bytes>      receiver only: <rtps><listenSocketBufferSize>bytes (template
#                                      socket_buffer_only.xml.in), builtin transports untouched
#                         oldbigbuf    bigbuf.xml (the confounded 2026-11-24 exp6 profile) on BOTH sides
#                         sndonly      sender only: <rtps><sendSocketBufferSize>4194304; receiver no XML
#                         largedata    BOTH sides FASTDDS_BUILTIN_TRANSPORTS=LARGE_DATA (docs/03 §15)
#                         mtu1400      fastdds_mtu1400.xml on BOTH sides: one UDPv4 transport with
#                                      maxMessageSize 1400, no builtin transports (docs/03 §15)
#                         flowctl      fastdds_flowctl.xml on BOTH sides: FIFO flow controller,
#                                      max_bytes_per_period 125000 / period_ms 1 on the publisher, plus
#                                      RMW_FASTRTPS_PUBLICATION_MODE=ASYNCHRONOUS (§15)
#                         cyclone      BOTH sides RMW_IMPLEMENTATION=rmw_cyclonedds_cpp, Cyclone defaults
#                                      (needs IMG=lyrical-wire:exp-extra; docs/03 §13)
#                  default: noxml,106496,212992,524288,1048576,2097152,4194304,8388608
#   --sizes LIST   shorthand: adds the byte sizes in LIST as arms (e.g. 524288,1048576)
#   --reps N       repetitions for arms without *reps (default 8). Order: round-robin by repetition,
#                  arms shuffled within each repetition (seeded, --seed, default 1)
#   --qos be|rel   default QoS for arms without a qos: prefix (default be)
#   --images N     images per run (default 20; 640x480 rgb8, 0.5 s period, img_pub.py)
#   --shape S      none (default) | tbf1g | wifi   egress qdisc on eth0 of BOTH containers (--cap-add NET_ADMIN)
#                    tbf1g: tc qdisc replace dev eth0 root tbf rate 1gbit burst 3028 latency 50ms
#                    wifi : tc qdisc replace dev eth0 root netem delay 3ms 1ms distribution normal
#                           rate 80mbit loss random 0.02% limit 10000   (EMULATION, arbitrary parameters)
#   --out DIR      output directory (default ./out/rcvbuf_sweep, or ./out/shaping when --shape != none);
#                  per-run rows are appended to DIR/runs.csv, files of each run in DIR/runs/
#   --keep-pcap N  keep the raw pcap of the first N repetitions of each arm (default 0: only the
#                  counts are kept, the ~19 MB pcap is deleted after sweep_pcap_stats.py has read it)
#   --dry-run      print the precondition check and the run order, run nothing
#   Two-machine mode (UNTESTED on real hardware; only the rosnet split was smoke-tested):
#   --role both|sub|pub  both (default) = two containers on this host; sub = receiver half only
#                  (waits for --images 'got' lines or --sub-timeout s); pub = sender half only
#   --net NAME     docker network (default rosnet with fixed IPs); "host" = --net host, no --ip
#   --iface IF     capture/shaping interface inside the container (default eth0)
#   --ip-sender IP / --ip-receiver IP   addresses used to classify the capture (default $IP_A / $IP_B)
#   --peer IP      sets ROS_STATIC_PEERS=IP (unicast discovery when multicast is blocked)
#   --sub-timeout S  receiver-only mode: give up after S seconds (default 120)
#
# Precondition (printed every time): requests above net.core.rmem_max are capped by the kernel
# (effective SO_RCVBUF = 2 x min(request, rmem_max)). This script never changes sysctls; to test
# above the cap the user must run e.g. `sudo sysctl -w net.core.rmem_max=16777216` on the host
# (net.core.rmem_max is not per-netns on this kernel: read-only inside containers, and
# `docker run --sysctl net.core.rmem_max=...` is refused).
#
# Serialize with the other experiment scripts:  flock <lockfile> ./run_rcvbuf_sweep.sh ...
set -euo pipefail
cd "$(dirname "$0")"
# shellcheck source=lib.sh
source ./lib.sh

ARMS="noxml,106496,212992,524288,1048576,2097152,4194304,8388608"; ARMS_SET=0; EXTRA=""
REPS=8; QOS=be; NIMG=20; SHAPE=none; OUTD=""; KEEP=0; DRY=0; SEED=1
ROLE=both; NETW="$NET"; IFACE=eth0; IPS="$IP_A"; IPR="$IP_B"; PEER=""; SUBTO=120
while [ $# -gt 0 ]; do
  case "$1" in
    --arms) ARMS="$2"; ARMS_SET=1; shift 2;;
    --sizes) EXTRA="$2"; shift 2;;
    --reps) REPS="$2"; shift 2;;
    --qos) QOS="$2"; shift 2;;
    --images) NIMG="$2"; shift 2;;
    --shape) SHAPE="$2"; shift 2;;
    --out) OUTD="$2"; shift 2;;
    --keep-pcap) KEEP="$2"; shift 2;;
    --seed) SEED="$2"; shift 2;;
    --dry-run) DRY=1; shift;;
    --role) ROLE="$2"; shift 2;;
    --net) NETW="$2"; shift 2;;
    --iface) IFACE="$2"; shift 2;;
    --ip-sender) IPS="$2"; shift 2;;
    --ip-receiver) IPR="$2"; shift 2;;
    --peer) PEER="$2"; shift 2;;
    --sub-timeout) SUBTO="$2"; shift 2;;
    -h|--help) sed -n '2,/^set -euo/p' "./$(basename "$0")" | sed '$d; s/^# \{0,1\}//'; exit 0;;
    *) echo "unknown option $1 (see --help)" >&2; exit 2;;
  esac
done
if [ -n "$EXTRA" ]; then
  if [ "$ARMS_SET" = 1 ]; then ARMS="$ARMS,$EXTRA"; else ARMS="$EXTRA"; fi
fi
case "$QOS" in be|rel) ;; *) echo "--qos must be be or rel" >&2; exit 2;; esac
case "$SHAPE" in
  none)  SHAPE_CMD="";;
  tbf1g) SHAPE_CMD="tc qdisc replace dev $IFACE root tbf rate 1gbit burst 3028 latency 50ms";;
  wifi)  SHAPE_CMD="tc qdisc replace dev $IFACE root netem delay 3ms 1ms distribution normal rate 80mbit loss random 0.02% limit 10000";;
  *) echo "--shape must be none, tbf1g or wifi" >&2; exit 2;;
esac
[ -z "$OUTD" ] && { if [ "$SHAPE" = none ]; then OUTD="$PWD/out/rcvbuf_sweep"; else OUTD="$PWD/out/shaping"; fi; }
mkdir -p "$OUTD/runs" "$OUTD/profiles" "$OUTD/exp"; chmod 777 "$OUTD" "$OUTD/runs"
OUTD="$(realpath "$OUTD")"

# ---- arms -> (qos, name, reps) ----
declare -a A_Q A_N A_R
IFS=',' read -r -a toks <<<"$ARMS"
for t in "${toks[@]}"; do
  [ -z "$t" ] && continue
  q="$QOS"; r="$REPS"
  case "$t" in *:*) q="${t%%:*}"; t="${t#*:}";; esac
  case "$t" in *'*'*) r="${t#*\*}"; t="${t%%\**}";; esac
  case "$t" in noxml|oldbigbuf|sndonly|largedata|mtu1400|flowctl|cyclone) ;; *[!0-9]*|'') echo "bad arm '$t'" >&2; exit 2;; esac
  A_Q+=("$q"); A_N+=("$t"); A_R+=("$r")
done

# ---- precondition check (read only) ----
RMEM_MAX=$(cat /proc/sys/net/core/rmem_max); WMEM_MAX=$(cat /proc/sys/net/core/wmem_max)
RMEM_DEF=$(cat /proc/sys/net/core/rmem_default)
{
  echo "# precondition check $(date -Is)"
  echo "host net.core.rmem_max=$RMEM_MAX rmem_default=$RMEM_DEF wmem_max=$WMEM_MAX (not changed by this script)"
  for i in "${!A_N[@]}"; do
    n="${A_N[$i]}"
    case "$n" in
      noxml) echo "arm ${A_Q[$i]}:$n  no setsockopt -> expected SO_RCVBUF = rmem_default = $RMEM_DEF";;
      oldbigbuf) echo "arm ${A_Q[$i]}:$n  bigbuf.xml 4194304 -> expected $(( 2 * (4194304 < RMEM_MAX ? 4194304 : RMEM_MAX) ))$( [ 4194304 -gt "$RMEM_MAX" ] && echo ' CAPPED by rmem_max')";;
      largedata|mtu1400|flowctl|cyclone) echo "arm ${A_Q[$i]}:$n  transport/RMW variant (docs/03 §13/§15); SO_RCVBUF read from ss -uamn per run";;
      sndonly) echo "arm ${A_Q[$i]}:$n  sender SO_SNDBUF request 4194304 -> expected $(( 2 * (4194304 < WMEM_MAX ? 4194304 : WMEM_MAX) ))$( [ 4194304 -gt "$WMEM_MAX" ] && echo ' CAPPED by wmem_max'); receiver default";;
      *) e=$(( 2 * (n < RMEM_MAX ? n : RMEM_MAX) ))
         if [ "$n" -gt "$RMEM_MAX" ]; then
           echo "arm ${A_Q[$i]}:$n  request $n > rmem_max $RMEM_MAX -> CAPPED, expected SO_RCVBUF $e (same as request $RMEM_MAX); testing it needs 'sudo sysctl -w net.core.rmem_max=$n' on the host"
         else echo "arm ${A_Q[$i]}:$n  request $n -> expected SO_RCVBUF $e (kernel doubles the request)"; fi;;
    esac
  done
} | tee -a "$OUTD/precheck.txt"

# ---- run order: round-robin by repetition, arms shuffled within each repetition ----
maxr=0; for r in "${A_R[@]}"; do [ "$r" -gt "$maxr" ] && maxr=$r; done
ORDER=()
for ((rep = 1; rep <= maxr; rep++)); do
  idx=(); for i in "${!A_N[@]}"; do [ "$rep" -le "${A_R[$i]}" ] && idx+=("$i"); done
  mapfile -t sh < <(python3 -c 'import random,sys; s=int(sys.argv[1]); x=sys.argv[2:]; random.Random(s).shuffle(x); print("\n".join(x))' "$((SEED * 1000 + rep))" "${idx[@]}")
  for i in "${sh[@]}"; do ORDER+=("$rep:$i"); done
done
echo "run order ($SHAPE, seed $SEED, ${#ORDER[@]} runs):" | tee -a "$OUTD/precheck.txt"
for o in "${ORDER[@]}"; do i="${o#*:}"; printf '  rep %s %s:%s\n' "${o%%:*}" "${A_Q[$i]}" "${A_N[$i]}"; done | tee -a "$OUTD/precheck.txt"
[ "$DRY" = 1 ] && exit 0

ensure_image
if [ "$NETW" = host ]; then NETARGS_B=(--net host); NETARGS_A=(--net host)
else
  NET="$NETW"; ensure_net
  NETARGS_B=(--net "$NETW" --ip "$IPR"); NETARGS_A=(--net "$NETW" --ip "$IPS")
fi
CAP=(); [ -n "$SHAPE_CMD" ] && CAP=(--cap-add NET_ADMIN)
PEERENV=(); [ -n "$PEER" ] && PEERENV=(-e "ROS_STATIC_PEERS=$PEER")

# snapshot of the node scripts used (other scripts in this directory may change while we run)
cp img_pub.py img_sub.py bigbuf.xml fastdds_mtu1400.xml fastdds_flowctl.xml "$OUTD/exp/"
gen_profile() {  # <element> <bytes> <file>
  sed -e "s/@ELEMENT@/$1/g" -e "s/@BYTES@/$2/g" socket_buffer_only.xml.in > "$3"
}
for i in "${!A_N[@]}"; do
  case "${A_N[$i]}" in
    noxml|oldbigbuf|largedata|mtu1400|flowctl|cyclone) ;;
    sndonly) gen_profile sendSocketBufferSize 4194304 "$OUTD/profiles/sndonly.xml";;
    *) gen_profile listenSocketBufferSize "${A_N[$i]}" "$OUTD/profiles/rb${A_N[$i]}.xml";;
  esac
done
[ -f "$OUTD/env.txt" ] || write_env "$OUTD"
{ echo; echo "# run_rcvbuf_sweep.sh $(date -Is) shape=$SHAPE seed=$SEED role=$ROLE net=$NETW image=$IMG arms=$ARMS"
  sha256sum "$OUTD"/exp/* socket_buffer_only.xml.in; } >> "$OUTD/env.txt"
[ -f "$OUTD/runs.csv" ] || python3 rcvbuf_sweep.py header > "$OUTD/runs.csv"

case "$ROLE" in sub) MINE=(swB); MYIPS=("$IPR");; pub) MINE=(swA); MYIPS=("$IPS");; *) MINE=(swA swB); MYIPS=("$IPR" "$IPS");; esac
trap 'clean "${MINE[@]}"; fix_owner "$OUTD" || true' EXIT

# --- container scripts (env: R=run prefix in /out, Q, N, IFACE, SHAPE_CMD, SUBTO) ---
B_SCRIPT='
'"$ROS_SRC"'
if [ -n "$SHAPE_CMD" ]; then $SHAPE_CMD > $R.tcsetup_B.txt 2>&1 || echo "SHAPE FAILED" >> $R.tcsetup_B.txt; fi
cat /proc/net/snmp > $R.snmp0_B.txt
tcpdump -i $IFACE -U -w $R.raw.pcap 2> $R.tcpdump.log & TD=$!
for i in $(seq 100); do [ "$(stat -c %s $R.raw.pcap 2>/dev/null || echo 0)" -ge 24 ] && break; sleep 0.1; done
python3 /exp/img_sub.py $Q > $R.listener.log 2>&1 & SP=$!
touch $R.started
for i in $(seq $((SUBTO * 10))); do
  [ -e $R.stop ] && break
  [ "$ROLE" = sub ] && [ "$(grep -c " got " $R.listener.log)" -ge "$N" ] && { sleep 1; break; }
  kill -0 $SP 2>/dev/null || break; sleep 0.1
done
ss -uamn > $R.ss_B_end.txt; ls /dev/shm > $R.shm_B.txt
kill -INT $SP; wait $SP
cat /proc/net/snmp > $R.snmp1_B.txt
tc -s qdisc show dev $IFACE > $R.tc_B.txt
kill -INT $TD; wait $TD; exit 0'
A_SCRIPT='
'"$ROS_SRC"'
if [ -n "$SHAPE_CMD" ]; then $SHAPE_CMD > $R.tcsetup_A.txt 2>&1 || echo "SHAPE FAILED" >> $R.tcsetup_A.txt; fi
cat /proc/net/snmp > $R.snmp0_A.txt
python3 /exp/img_pub.py $Q $N > $R.talker.log 2>&1 & P=$!
( for i in $(seq 300); do grep -Eq "published 0" $R.talker.log 2>/dev/null && break; sleep 0.1; done; sleep 1; ss -uamn > $R.ss_A.txt ) &
wait $P; RC=$?
cat /proc/net/snmp > $R.snmp1_A.txt
tc -s qdisc show dev $IFACE > $R.tc_A.txt
wait; exit $RC'

start_B() {  # <run-id> <profile-in-container or "">   (+ global ARM_ENV: extra -e args for this arm)
  local id="$1" prof="$2" env=("${ARM_ENV[@]}")
  [ -n "$prof" ] && env+=(-e "FASTDDS_DEFAULT_PROFILES_FILE=$prof")
  docker run -d --name swB "${NETARGS_B[@]}" "${CAP[@]}" "${PEERENV[@]}" "${env[@]}" \
    -v "$OUTD/exp:/exp:ro" -v "$OUTD:/out" \
    -e R="/out/runs/$id" -e Q="$CQ" -e N="$NIMG" -e IFACE="$IFACE" -e SHAPE_CMD="$SHAPE_CMD" \
    -e SUBTO="$SUBTO" -e ROLE="$ROLE" "$IMG" bash -c "$B_SCRIPT" >/dev/null
}
start_A() {
  local id="$1" prof="$2" env=("${ARM_ENV[@]}")
  [ -n "$prof" ] && env+=(-e "FASTDDS_DEFAULT_PROFILES_FILE=$prof")
  docker run -d --name swA "${NETARGS_A[@]}" "${CAP[@]}" "${PEERENV[@]}" "${env[@]}" \
    -v "$OUTD/exp:/exp:ro" -v "$OUTD:/out" \
    -e R="/out/runs/$id" -e Q="$CQ" -e N="$NIMG" -e IFACE="$IFACE" -e SHAPE_CMD="$SHAPE_CMD" \
    "$IMG" bash -c "$A_SCRIPT" >/dev/null
}

T0=$(date +%s); k=0
for o in "${ORDER[@]}"; do
  rep="${o%%:*}"; i="${o#*:}"; CQ="${A_Q[$i]}"; arm="${A_N[$i]}"; k=$((k + 1))
  id=$(printf '%s_%s_%s_%s_r%02d' "$(date +%m%d%H%M%S)" "$SHAPE" "$CQ" "$arm" "$rep")
  P="$OUTD/runs/$id"
  profB=""; profA=""; req=""; pB=none; pA=none; ARM_ENV=(); RMW=rmw_fastrtps_cpp; ENVX=""
  case "$arm" in
    noxml) ;;
    largedata) ENVX="FASTDDS_BUILTIN_TRANSPORTS=LARGE_DATA";;
    mtu1400) profB=/exp/fastdds_mtu1400.xml; profA=/exp/fastdds_mtu1400.xml; pB=fastdds_mtu1400.xml; pA=fastdds_mtu1400.xml;;
    flowctl) profB=/exp/fastdds_flowctl.xml; profA=/exp/fastdds_flowctl.xml; pB=fastdds_flowctl.xml; pA=fastdds_flowctl.xml
             ENVX="RMW_FASTRTPS_PUBLICATION_MODE=ASYNCHRONOUS";;   # rmw_fastrtps forces SYNCHRONOUS otherwise
    cyclone) RMW=rmw_cyclonedds_cpp; ENVX="RMW_IMPLEMENTATION=rmw_cyclonedds_cpp";;
    oldbigbuf) profB=/exp/bigbuf.xml; profA=/exp/bigbuf.xml; req=4194304; pB=bigbuf.xml; pA=bigbuf.xml;;
    sndonly) profA=/out/profiles/sndonly.xml; pA=sendSocketBufferSize=4194304;;
    *) profB=/out/profiles/rb$arm.xml; req=$arm; pB=listenSocketBufferSize=$arm;;
  esac
  for e in $ENVX; do ARM_ENV+=(-e "$e"); done   # ENVX: space-separated VAR=value list
  log "[$k/${#ORDER[@]}] rep $rep $SHAPE $CQ:$arm -> $id"
  t1=$(date +%s); note=""
  clean "${MINE[@]}"
  [ "$NETW" != host ] && wait_ips_free 60 "${MYIPS[@]}"
  if [ "$ROLE" != pub ]; then
    start_B "$id" "$profB"
    wait_file "$P.started" 0 15 || note="$note no-start"
    wait_log "$P.listener.log" 'subscription ready' 30 || note="$note no-ready"
    docker exec swB ss -uamn > "$P.ss_B_ready.txt" 2>&1 || true
    [ "$ROLE" = sub ] && log "receiver ready on $IPR; start the sender half now (--role pub) on the other machine"
  fi
  if [ "$ROLE" != sub ]; then
    start_A "$id" "$profA"
    echo "A $(wait_exit swA 180 || echo timeout)" > "$P.exit.txt"
    docker logs swA >> "$P.talker.docker.log" 2>&1 || true
  fi
  if [ "$ROLE" = both ]; then sleep 1.5; touch "$P.stop"; fi
  if [ "$ROLE" != pub ]; then
    echo "B $(wait_exit swB $((SUBTO + 30)) || echo timeout)" >> "$P.exit.txt"
    docker logs swB > "$P.receiver.docker.log" 2>&1 || true
  fi
  clean "${MINE[@]}"
  rm -f "$P.started" "$P.stop"
  python3 rcvbuf_sweep.py row "$P" run_id="$id" start="$(date -d @"$t1" -Is)" rep="$rep" order="$k" \
    shape="$SHAPE" qos="$CQ" arm="$arm" profile_B="$pB" profile_A="$pA" req_bytes="$req" n_pub="$NIMG" \
    ip_sender="$IPS" ip_receiver="$IPR" wall_s="$(( $(date +%s) - t1 ))" note="${note# }" rmw="$RMW" env_extra="$ENVX" >> "$OUTD/runs.csv"
  tail -1 "$OUTD/runs.csv" | python3 -c 'import csv,sys
h=next(csv.reader(open(sys.argv[1]))); r=next(csv.reader(sys.stdin)); d=dict(zip(h,r))
print("   delivered %s/%s rb_B %s RcvbufErrors %s sockdrops %s DATA_FRAG %s NACK_FRAG %s burst %s ms tcA %s/%s/%s" % (d["delivered"], d["published"], d["rb_B_port"], d["B_RcvbufErrors"], d["drops_B_port"], d["datafrag_total"], d["nackfrag"], d["burst_ms_med"], d["tcA_pkts"], d["tcA_dropped"], d["tcA_overlimits"]))' "$OUTD/runs.csv" >&2
  if [ "$rep" -gt "$KEEP" ]; then rm -f "$P.raw.pcap" 2>/dev/null || docker run --rm --network none -v "$OUTD/runs:/r" "$IMG" rm -f "/r/$id.raw.pcap"; fi
done
log "done: ${#ORDER[@]} runs in $(( $(date +%s) - T0 )) s -> $OUTD/runs.csv"

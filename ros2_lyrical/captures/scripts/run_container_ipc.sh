#!/usr/bin/env bash
# Experiment 14 (docs/03 §16): does Fast DDS SHM work between two containers?
# Demo talker in container c_A, demo listener in container c_B, Fast DDS default transports
# (rmw_fastrtps_cpp, UDPv4 + SHM). The arms vary only the namespaces/mounts docker gives c_B:
#
#   a      bridge ctrnet, own netns, own IPC ns, own /dev/shm           (docker default)
#   b_ipc  bridge, c_B --ipc=container:c_A  (c_A --ipc=shareable)       (shared /dev/shm + SysV IPC)
#   b_vol  bridge, own IPC ns, but one tmpfs docker volume mounted on /dev/shm in both
#   b_ipc_samehost  as b_ipc + both containers --hostname ipcpeer
#   c_net  c_B --network container:c_A (same netns/IP/MAC), own IPC ns     (~ --net=host without --ipc=host)
#   c_both c_B --network container:c_A --ipc=container:c_A                 (~ --net=host --ipc=host)
#   kill   b_vol layout (shared tmpfs volume on /dev/shm, separate IPC/PID ns); the talker container
#          is SIGKILLed mid-run, then a second talker container with the same volume is started:
#          are stale fastdds_* files left, does data still flow? (b_ipc cannot be used here: docker
#          refuses --ipc=container:X when X itself joined another container's IPC namespace)
#
# Usage: run_container_ipc.sh <arm> <rep>        one run (wrap in: flock -s <lock>)
#        run_container_ipc.sh --all [reps=3] [first_rep=1]  every arm x reps, groups of arms under flock -s
#        run_container_ipc.sh --summary          only rebuild ../results/ipc_* from out/ipc
# Evidence per run (out/ipc/<arm>_r<rep>.*): tcpdump -i any in every netns (pcap), ls -la /dev/shm
# in both containers 4 s after the talker started, listener/talker logs, SPDP SHM locators.
# Nothing here touches host settings: no --net=host, no --ipc=host, no --privileged.
set -euo pipefail
cd "$(dirname "$0")"
export NET=ctrnet SUBNET=172.22.0.0/16 GATEWAY=172.22.0.1 IP_A=172.22.0.3 IP_B=172.22.0.2
# shellcheck source=lib.sh
source ./lib.sh
OUT="${OUT:-$PWD/out/ipc}"; mkdir -p "$OUT"; chmod 777 "$OUT"
LOCK="${LOCK:-$PWD/out/exp.lock}"
RES="$PWD/../results"
# own DDS domain 14 (ports 10900+): run_sros2.sh shares ctrnet with domain 15
DOM="${DOM:-14}"
ARMS=(a b_ipc b_vol b_ipc_samehost c_net c_both kill)

summary() {
  python3 ./ipc_summary.py "$OUT" "$RES"
}

if [ "${1:-}" = "--summary" ]; then summary; exit 0; fi
if [ "${1:-}" = "--all" ]; then
  reps="${2:-3}"
  ensure_net
  write_env "$OUT" >/dev/null 2>&1 || true
  first="${3:-1}"
  # arms in two groups so each shared-lock hold stays < ~90 s (about 19 s per arm, 30 s for kill)
  for r in $(seq "$first" "$reps"); do
    for grp in "a b_ipc b_vol b_ipc_samehost" "c_net c_both kill"; do
      log "exp14 rep=$r arms: $grp"
      # shellcheck disable=SC2016
      flock -s "$LOCK" bash -c 'for arm in $2; do "$1" "$arm" "$3" || echo "run $arm r$3 FAILED" >&2; done' _ "$0" "$grp" "$r"
    done
  done
  cp "$OUT/env.txt" "$RES/ipc_env.txt" 2>/dev/null || true
  sed -i "s/$(hostname)/<host>/g" "$RES/ipc_env.txt" 2>/dev/null || true
  summary
  # the network is shared with run_sros2.sh: remove it yourself when both are done (docker network rm ctrnet)
  exit 0
fi

arm="${1:?arm}"; rep="${2:?rep}"; name="${arm}_r${rep}"
ROS="$ROS_SRC"
ensure_net
clean c_A c_B c_A2
docker volume rm -f c_shm >/dev/null 2>&1 || true
rm -f "$OUT/$name".*
trap 'clean c_A c_B c_A2; docker volume rm -f c_shm >/dev/null 2>&1 || true; fix_owner "$OUT" || true' EXIT
wait_ips_free 60 "$IP_A" "$IP_B"

A_ARGS=(--net "$NET" --ip "$IP_A" -e ROS_DOMAIN_ID="$DOM"); B_ARGS=()
B_OWN_NETNS=1
case "$arm" in
  a)      B_ARGS=(--net "$NET" --ip "$IP_B") ;;
  b_ipc)  A_ARGS+=(--ipc=shareable); B_ARGS=(--net "$NET" --ip "$IP_B" --ipc=container:c_A) ;;
  b_ipc_samehost) A_ARGS+=(--ipc=shareable --hostname ipcpeer); B_ARGS=(--net "$NET" --ip "$IP_B" --ipc=container:c_A --hostname ipcpeer) ;;
  b_vol|kill) docker volume create --driver local --opt type=tmpfs --opt device=tmpfs --opt o=size=256m c_shm >/dev/null
          A_ARGS+=(-v c_shm:/dev/shm); B_ARGS=(--net "$NET" --ip "$IP_B" -v c_shm:/dev/shm) ;;
  c_net)  B_ARGS=(--network container:c_A); B_OWN_NETNS=0 ;;
  c_both) A_ARGS+=(--ipc=shareable); B_ARGS=(--network container:c_A --ipc=container:c_A); B_OWN_NETNS=0 ;;
  *) echo "unknown arm $arm (one of: ${ARMS[*]})" >&2; exit 2 ;;
esac

# c_A: tcpdump on all its interfaces, waits for /out/<name>.go, then the talker (8 s).
# In arm "kill" the talker runs without timeout and the container is SIGKILLed from outside.
TALK="timeout 8 ros2 run demo_nodes_cpp talker"
[ "$arm" = kill ] && TALK="ros2 run demo_nodes_cpp talker"
docker run -d --name c_A "${A_ARGS[@]}" -v "$OUT:/out" "$IMG" bash -c "$ROS
  tcpdump -i any -U -w /out/$name.A.raw.pcap 2>/out/$name.A.tcpdump.log &
  $(ctr_wait_pcap "/out/$name.A.raw.pcap")
  touch /out/$name.A.ready
  while [ ! -e /out/$name.go ]; do sleep 0.1; done
  $TALK > /out/$name.talker.log 2>&1
  while [ ! -e /out/$name.done ]; do sleep 0.2; done
  kill %1; sleep 0.5" >/dev/null
wait_file "$OUT/$name.A.ready" 0 15
CAPB=""
if [ "$B_OWN_NETNS" = 1 ]; then
  CAPB="tcpdump -i any -U -w /out/$name.B.raw.pcap 2>/out/$name.B.tcpdump.log &
  $(ctr_wait_pcap "/out/$name.B.raw.pcap")"
fi
LIS_T=14; [ "$arm" = kill ] && LIS_T=20
docker run -d --name c_B -e ROS_DOMAIN_ID="$DOM" "${B_ARGS[@]}" -v "$OUT:/out" "$IMG" bash -c "$ROS
  $CAPB
  touch /out/$name.B.ready
  timeout $LIS_T ros2 run demo_nodes_cpp listener > /out/$name.listener.log 2>&1
  ls -la /dev/shm > /out/$name.B.shm_end.txt 2>&1
  [ -n \"\$(jobs -p)\" ] && kill %1; sleep 0.5" >/dev/null
wait_file "$OUT/$name.B.ready" 0 15
sleep 1
touch "$OUT/$name.go"
sleep 4
for c in c_A c_B; do
  docker exec "$c" bash -c 'echo "# hostname=$(hostname) ipcns=$(readlink /proc/self/ns/ipc) netns=$(readlink /proc/self/ns/net) pidns=$(readlink /proc/self/ns/pid) shm_fs=$(df -h /dev/shm | tail -1 | tr -s " ")"; ls -la --time-style=+ /dev/shm' \
    > "$OUT/$name.${c#c_}.shm_mid.txt" 2>&1 || true
done
if [ "$arm" = kill ]; then
  docker kill c_A >/dev/null   # SIGKILL: no cleanup by Fast DDS in the talker
  sleep 1
  docker exec c_B ls -la --time-style=+ /dev/shm > "$OUT/$name.B.shm_afterkill.txt" 2>&1 || true
  # second talker: same shm volume as c_B (c_A is gone), own netns on the bridge
  docker run -d --name c_A2 --net "$NET" --ip "$IP_A" -e ROS_DOMAIN_ID="$DOM" -v c_shm:/dev/shm "$IMG" \
    bash -c "$ROS; timeout 6 ros2 run demo_nodes_cpp talker" >/dev/null
  echo "c_A2 exit $(wait_exit c_A2 30)" > "$OUT/$name.exit2.txt"
  docker logs c_A2 > "$OUT/$name.talker2.log" 2>&1 || true
  docker exec c_B ls -la --time-style=+ /dev/shm > "$OUT/$name.B.shm_after2.txt" 2>&1 || true
else
  while [ "$(docker inspect -f '{{.State.Running}}' c_A)" = true ] && ! grep -q . "$OUT/$name.talker.log" 2>/dev/null; do sleep 0.2; done
fi
echo "c_B exit $(wait_exit c_B 40)" > "$OUT/$name.exit.txt"
touch "$OUT/$name.done"
[ "$arm" != kill ] && echo "c_A exit $(wait_exit c_A 20)" >> "$OUT/$name.exit.txt"
rm -f "$OUT/$name".{go,done,A.ready,B.ready}
for s in A B; do
  [ -f "$OUT/$name.$s.raw.pcap" ] && filter_pcap "$OUT/$name.$s.raw.pcap" "$OUT/$name.$s.pcap"
done
# per-pcap evidence: "Hello World" frames by (src,dst) and the SHM default-unicast locators in SPDP
for s in A B; do
  [ -f "$OUT/$name.$s.pcap" ] || continue
  docker run --rm --network none -v "$OUT:/o" "$IMG" bash -c "
    tshark -r /o/$name.$s.pcap -Y 'frame contains \"Hello World\"' -T fields -e ip.src -e ip.dst 2>/dev/null | sort | uniq -c > /o/$name.$s.hello.txt
    tshark -r /o/$name.$s.pcap -Y 'rtps.sm.wrEntityId==0x000100c2' -T fields -e ip.src -e rtps.guidPrefix.src -e rtps.locator.kind -e rtps.locator.ipv4 -e rtps.locator.port 2>/dev/null | sort -u > /o/$name.$s.spdp.txt"
done
python3 ./ipc_shm_locators.py "$OUT"/"$name".[AB].pcap > "$OUT/$name.shmloc.txt" 2>&1 || true
log "done $name: received $(grep -c 'I heard' "$OUT/$name.listener.log" || true)"

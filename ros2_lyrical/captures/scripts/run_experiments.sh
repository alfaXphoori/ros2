#!/usr/bin/env bash
# Reproduce the ROS 2 Lyrical wire experiments (ros2_lyrical/docs/03_wire_experiments.md).
# Needs: Docker (user in the docker group). Output pcaps go to ./out/
set -euo pipefail
cd "$(dirname "$0")"
OUT="$PWD/out"; mkdir -p "$OUT"; chmod 777 "$OUT"
IMG=lyrical-wire:exp
docker build -q -t "$IMG" . >/dev/null
docker network create rosnet >/dev/null 2>&1 || true
SRC='source /opt/ros/lyrical/setup.bash'
clean() { docker rm -f hostA hostB zrouter >/dev/null 2>&1 || true; }
trap clean EXIT

run_pair() {  # $1=name  $2=listener cmd  $3=talker cmd  $4=extra docker env  $5=wait
  clean
  docker run -d --name hostB --net rosnet -v "$PWD:/exp" -v "$OUT:/out" $4 "$IMG" bash -c "$SRC
    tcpdump -i eth0 -U -w /out/$1.pcap 2>/dev/null & sleep 1
    $2 > /out/$1.listener.log 2>&1
    grep -A1 '^Udp:' /proc/net/snmp > /out/$1.snmp.txt; grep -A1 '^Ip:' /proc/net/snmp >> /out/$1.snmp.txt
    kill %1; sleep 1" >/dev/null
  sleep 2
  docker run -d --name hostA --net rosnet -v "$PWD:/exp" $4 "$IMG" bash -c "$SRC; $3" >/dev/null
  sleep "$5"
}

echo "[1] Fast DDS default: demo talker -> listener (two containers)"
run_pair exp1_fastdds_default "timeout 14 ros2 run demo_nodes_cpp listener" "timeout 10 ros2 run demo_nodes_cpp talker" "" 17

echo "[2] 640x480 rgb8 Image, RELIABLE"
run_pair exp2_image_reliable "timeout 12 python3 /exp/img_sub.py rel" "python3 /exp/img_pub.py rel 5" "" 15

echo "[3] rmw_zenoh_cpp via one router"
clean
ZENV='-e RMW_IMPLEMENTATION=rmw_zenoh_cpp -e ZENOH_CONFIG_OVERRIDE=connect/endpoints=["tcp/zrouter:7447"];listen/endpoints=["tcp/0.0.0.0:0"]'
docker run -d --name zrouter --net rosnet "$IMG" bash -c "$SRC; timeout 30 ros2 run rmw_zenoh_cpp rmw_zenohd" >/dev/null
sleep 2
docker run -d --name hostB --net rosnet -v "$OUT:/out" $ZENV "$IMG" bash -c "$SRC
  tcpdump -i eth0 -U -w /out/exp3_zenoh.pcap 2>/dev/null & sleep 1
  timeout 14 ros2 run demo_nodes_cpp listener > /out/exp3_zenoh.listener.log 2>&1; kill %1; sleep 1" >/dev/null
sleep 2
docker run -d --name hostA --net rosnet $ZENV "$IMG" bash -c "$SRC; timeout 9 ros2 run demo_nodes_cpp talker" >/dev/null
sleep 15

echo "[4] same container (Fast DDS SHM): data should not appear on the network"
clean
docker run --rm --shm-size=256m -v "$OUT:/out" "$IMG" bash -c "$SRC
  tcpdump -i any -U -w /out/exp4_samehost_shm.pcap 2>/dev/null & sleep 1
  ros2 run demo_nodes_cpp listener > /out/exp4.listener.log 2>&1 &
  sleep 1; timeout 6 ros2 run demo_nodes_cpp talker > /dev/null 2>&1 &
  sleep 4; ls -la /dev/shm > /out/exp4_devshm.txt
  ps -eLo comm | grep '^dds\.' | sort | uniq -c > /out/exp4_threads.txt
  sleep 4; kill %2 %1 2>/dev/null || true; sleep 1"

echo "[5] Image BEST_EFFORT, default receive buffer"
run_pair exp5_image_besteffort "timeout 16 python3 /exp/img_sub.py be" "python3 /exp/img_pub.py be 20" "" 18

echo "[6] Image BEST_EFFORT, 4 MiB receive buffer (Fast DDS XML profile)"
run_pair exp6_image_besteffort_bigbuf "timeout 16 python3 /exp/img_sub.py be" "python3 /exp/img_pub.py be 20" "-e FASTDDS_DEFAULT_PROFILES_FILE=/exp/bigbuf.xml" 18

for e in exp5_image_besteffort exp6_image_besteffort_bigbuf; do
  echo "$e: received $(grep -c got "$OUT/$e.listener.log")/20 · $(sed -n 2p "$OUT/$e.snmp.txt" | awk '{print "RcvbufErrors=" $6}')"
done
echo "done -> $OUT"

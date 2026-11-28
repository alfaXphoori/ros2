#!/usr/bin/env bash
# Experiment 15 (docs/03 §2.4): SROS2 Enforce on the wire, Fast DDS (rmw_fastrtps_cpp) default.
# Two containers on bridge network ctrnet (talker 172.22.1.3 -> listener 172.22.1.2, exp1 layout),
# tcpdump on the listener's eth0. A fresh keystore is generated every time the script runs a
# "keystore" step (never committed: out/ is git-ignored and **/sros2_keystore/ is ignored too).
#
# Usage:
#   run_sros2.sh keystore              fresh keystore + enclaves /talker /listener in out/sros2/sros2_keystore
#   run_sros2.sh func <rep>            demo talker/listener, secure and plain, 10 s, capture   (flock -s)
#   run_sros2.sh timing <rep>          sec_pub.py 1 kHz x 10 s -> sec_sub.py, secure and plain,
#                                      capture; match time, first sample, CPU                   (flock -x)
#   run_sros2.sh --all [reps=3]        keystore, then func and timing reps, each under the right lock
#   run_sros2.sh --summary             only rebuild ../results/sros2_* (sros2_summary.py)
#   run_sros2.sh pcap [rep=3]          write ../exp15_sros2_enforce.pcap.gz from func_sec_r<rep>
# Output: out/sros2/<mode>_<sec|plain>_r<rep>.{raw.pcap,pcap,talker.log,listener.log}
set -euo pipefail
cd "$(dirname "$0")"
export NET=ctrnet SUBNET=172.22.0.0/16 GATEWAY=172.22.0.1 IP_A=172.22.1.3 IP_B=172.22.1.2
# shellcheck source=lib.sh
source ./lib.sh
OUT="${OUT:-$PWD/out/sros2}"; mkdir -p "$OUT"; chmod 777 "$OUT"
KS="$OUT/sros2_keystore"
LOCK="${LOCK:-$PWD/out/exp.lock}"
RES="$PWD/../results"
# own DDS domain: other experiments share ctrnet (exp14 uses domain 0); the governance/permissions
# files are generated for this domain id (sros2 reads ROS_DOMAIN_ID at create time)
DOM="${DOM:-15}"

keystore() {
  rm -rf "$KS" 2>/dev/null || docker run --rm --network none -v "$OUT:/o" "$IMG" rm -rf /o/sros2_keystore
  docker run --rm --network none -e ROS_DOMAIN_ID="$DOM" -v "$OUT:/o" "$IMG" bash -c "$ROS_SRC
    ros2 security create_keystore /o/sros2_keystore
    ros2 security create_enclave /o/sros2_keystore /talker
    ros2 security create_enclave /o/sros2_keystore /listener
    ros2 security list_enclaves /o/sros2_keystore
    openssl x509 -in /o/sros2_keystore/enclaves/talker/cert.pem -noout -text | grep -E 'Signature Algorithm|Public Key Algorithm|ASN1 OID|NIST CURVE' | sort -u
    find /o/sros2_keystore -type f | sed 's|/o/sros2_keystore/||' | sort" > "$OUT/keystore.log" 2>&1
  fix_owner "$OUT"
  cat "$OUT/keystore.log"
}

# pair <name> <secure 0|1> <listener cmd> <talker cmd> <ready ERE or "">
pair() {
  local name="$1" sec="$2" lcmd="$3" tcmd="$4" ready="$5" senv=(-e ROS_DOMAIN_ID="$DOM") lenc="" tenc=""
  if [ "$sec" = 1 ]; then
    senv+=(-v "$KS:/ks:ro" -e ROS_SECURITY_KEYSTORE=/ks -e ROS_SECURITY_ENABLE=true -e ROS_SECURITY_STRATEGY=Enforce)
    lenc="--ros-args --enclave /listener"; tenc="--ros-args --enclave /talker"
  fi
  clean c_sB c_sA; rm -f "$OUT/$name".*
  wait_ips_free 60 "$IP_B" "$IP_A"
  docker run -d --name c_sB --net "$NET" --ip "$IP_B" -v "$PWD:/exp:ro" -v "$OUT:/out" "${senv[@]}" "$IMG" bash -c "$ROS_SRC
    tcpdump -i eth0 -U -w /out/$name.raw.pcap 2>/out/$name.tcpdump.log &
    $(ctr_wait_pcap "/out/$name.raw.pcap")
    touch /out/$name.started
    $lcmd $lenc > /out/$name.listener.log 2>&1
    sleep 0.5; kill %1; sleep 0.5" >/dev/null
  wait_pcap "$OUT/$name.raw.pcap" 10
  wait_file "$OUT/$name.started" 0 10
  if [ -n "$ready" ]; then wait_log "$OUT/$name.listener.log" "$ready" 30; else sleep 1; fi
  docker run -d --name c_sA --net "$NET" --ip "$IP_A" -v "$PWD:/exp:ro" "${senv[@]}" "$IMG" bash -c "$ROS_SRC; $tcmd $tenc" >/dev/null
  echo "c_sA exit $(wait_exit c_sA 90)" > "$OUT/$name.exit.txt"
  docker logs c_sA > "$OUT/$name.talker.log" 2>&1 || true
  echo "c_sB exit $(wait_exit c_sB 90)" >> "$OUT/$name.exit.txt"
  rm -f "$OUT/$name.started"
  filter_pcap "$OUT/$name.raw.pcap" "$OUT/$name.pcap"
  clean c_sB c_sA
}

case "${1:-}" in
  keystore) ensure_net; keystore ;;
  func)
    ensure_net; r="${2:?rep}"; trap 'clean c_sA c_sB; fix_owner "$OUT" || true' EXIT
    [ -f "$KS/enclaves/governance.p7s" ] || { log "no keystore: run '$0 keystore' first"; exit 1; }
    for sec in 1 0; do
      tag=$([ $sec = 1 ] && echo sec || echo plain)
      pair "func_${tag}_r$r" "$sec" "timeout 14 ros2 run demo_nodes_cpp listener" "timeout 10 ros2 run demo_nodes_cpp talker" ""
      log "func $tag r$r: listener heard $(grep -c 'I heard' "$OUT/func_${tag}_r$r.listener.log" || true)"
    done ;;
  timing)
    ensure_net; r="${2:?rep}"; trap 'clean c_sA c_sB; fix_owner "$OUT" || true' EXIT
    [ -f "$KS/enclaves/governance.p7s" ] || { log "no keystore: run '$0 keystore' first"; exit 1; }
    for sec in 1 0; do
      tag=$([ $sec = 1 ] && echo sec || echo plain)
      pair "timing_${tag}_r$r" "$sec" "python3 /exp/sec_sub.py --idle 2 --timeout 45" \
        "python3 /exp/sec_pub.py --rate 1000 --duration 10" "subscription ready"
      log "timing $tag r$r: $(tail -1 "$OUT/timing_${tag}_r$r.listener.log")"
    done ;;
  --summary) python3 ./sros2_summary.py "$OUT" "$RES" ;;
  pcap)  # small committed capture: func_sec_r<rep> reduced to the two containers' frames, gzipped
    r="${2:-3}"
    docker run --rm --network none -v "$OUT:/o" "$IMG" tshark -r "/o/func_sec_r$r.pcap" \
      -Y "(ip.src==$IP_A || ip.src==$IP_B) && !(udp.port==5353) || arp.src.proto_ipv4==$IP_A || arp.src.proto_ipv4==$IP_B" \
      -F pcap -w /o/exp15_sros2_enforce.pcap 2>/dev/null
    gzip -9 -c "$OUT/exp15_sros2_enforce.pcap" > "$PWD/../exp15_sros2_enforce.pcap.gz" ;;
  --all)
    reps="${2:-3}"
    flock -s "$LOCK" "$0" keystore
    for r in $(seq 1 "$reps"); do flock -s "$LOCK" "$0" func "$r"; done
    for r in $(seq 1 "$reps"); do flock -x "$LOCK" "$0" timing "$r"; done
    python3 ./sros2_summary.py "$OUT" "$RES" ;;
  *) sed -n '2,17p' "$0"; exit 2 ;;
esac

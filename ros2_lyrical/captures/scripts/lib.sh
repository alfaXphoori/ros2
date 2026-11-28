# shellcheck shell=bash
# Shared helpers for the wire-experiment scripts in this directory.
# Usage:   source "$(dirname "$0")/lib.sh"      (from a bash script with `set -euo pipefail`)
#
# Constants (override any of them by exporting it before sourcing):
#   IMG=lyrical-wire:exp        image built from ./Dockerfile
#   NET=rosnet  SUBNET=172.20.0.0/16  GATEWAY=172.20.0.1
#   IP_B=172.20.0.2   receiver / listener / tcpdump ("Host B")
#   IP_A=172.20.0.3   sender / talker ("Host A")
#   IP_ZROUTER=172.20.0.2  IP_ZLISTENER=172.20.0.3  IP_ZTALKER=172.20.0.4   (exp3, rmw_zenoh)
#   ROS_SRC='source /opt/ros/lyrical/setup.bash'
#   PCAP_FILTER  tshark display filter used by filter_pcap (IPv4+ARP, no mDNS, nothing to/from the gateway)
#   LIB_DIR      directory of this file (the docker build context)
#
# Functions (all return non-zero on failure; nothing here changes host settings):
#   log <msg...>                        timestamped message on stderr
#   ensure_image [--rebuild]            build $IMG only if missing (or REBUILD=1 / --rebuild)
#   ensure_net                          create $NET with $SUBNET if missing; fail if it has another subnet
#   clean [name...]                     docker rm -f the containers (default: hostA hostB zrouter)
#   wait_ips_free <timeout_s> <ip...>  wait until no container on $NET holds these IPs. Docker hands
#                                        out dynamic IPs from .2 upward, so any container started on
#                                        $NET WITHOUT --ip can take .2/.3/.4; use --ip and the lock.
#   wait_file <path> <min_bytes> [timeout_s=10]   wait until a host file has >= min_bytes
#   wait_pcap <path> [timeout_s=10]     wait until a pcap has its 24-byte global header
#   wait_log <file> <ERE> [timeout_s=20] wait until a line matching ERE appears in a host file
#   wait_tcp_listen <container> <port> [timeout_s=10]  wait until something listens on TCP port
#   wait_exit <container> [timeout_s=60] `docker wait` with a timeout; prints the exit code
#   ctr_wait_pcap <path-in-container> [timeout_s=5]   prints a bash snippet (for use INSIDE a
#                                        container script) that waits for the pcap header
#   write_env <outdir>                  env.txt + dpkg_ros_lyrical.txt + dpkg_all.txt in <outdir>
#   filter_pcap <in> <out>              tshark (inside $IMG) with $PCAP_FILTER, pcap format
#   fix_owner <dir>                     chown files written by root containers back to the caller
#
# File convention: tcpdump writes <name>.raw.pcap (unfiltered, may contain host names via mDNS),
# filter_pcap writes <name>.pcap (same filter as the committed captures, so frame numbers are
# comparable with docs/03).

LIB_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
IMG="${IMG:-lyrical-wire:exp}"
NET="${NET:-rosnet}"
SUBNET="${SUBNET:-172.20.0.0/16}"
GATEWAY="${GATEWAY:-172.20.0.1}"
IP_B="${IP_B:-172.20.0.2}"
IP_A="${IP_A:-172.20.0.3}"
IP_ZROUTER="${IP_ZROUTER:-172.20.0.2}"
IP_ZLISTENER="${IP_ZLISTENER:-172.20.0.3}"
IP_ZTALKER="${IP_ZTALKER:-172.20.0.4}"
ROS_SRC="${ROS_SRC:-source /opt/ros/lyrical/setup.bash}"
# Keeps IPv4 + ARP between the containers. The committed captures contain ARP frames, so the
# filter that produced them kept ARP; the older note in docs/03 §9.1 (`ip && ...`) would drop it and
# shift frame numbers. This filter leaves the committed pcaps unchanged (checked 2026-11-27).
PCAP_FILTER="${PCAP_FILTER:-(ip || arp) && !(udp.port==5353) && !(ip.addr==${GATEWAY}) && !(arp.src.proto_ipv4==${GATEWAY}) && !(arp.dst.proto_ipv4==${GATEWAY})}"

log() { printf '[%s] %s\n' "$(date +%H:%M:%S)" "$*" >&2; }

ensure_image() {
  local rebuild="${REBUILD:-0}"
  [ "${1:-}" = "--rebuild" ] && rebuild=1
  if [ "$rebuild" != 1 ] && docker image inspect "$IMG" >/dev/null 2>&1; then
    return 0
  fi
  log "building $IMG from $LIB_DIR/Dockerfile"
  docker build -q -t "$IMG" "$LIB_DIR" >/dev/null
  if docker run --rm --network none "$IMG" grep -q MISMATCH /opt/exp/apt-pin-check.txt; then
    log "WARNING: $IMG package versions differ from apt-pins.txt (see /opt/exp/apt-pin-check.txt)"
  fi
}

ensure_net() {
  local have
  if have=$(docker network inspect "$NET" --format '{{range .IPAM.Config}}{{.Subnet}} {{end}}' 2>/dev/null); then
    have="${have%% }"
    if [ "$have" != "$SUBNET" ]; then
      log "ERROR: docker network '$NET' exists with subnet '$have', expected '$SUBNET'."
      log "       Not touching it. Remove it yourself (docker network rm $NET) or set NET=<other name>."
      return 1
    fi
  else
    docker network create --subnet "$SUBNET" --gateway "$GATEWAY" "$NET" >/dev/null
  fi
}

clean() {
  local names=("$@")
  [ ${#names[@]} -eq 0 ] && names=(hostA hostB zrouter)
  docker rm -f "${names[@]}" >/dev/null 2>&1 || true
}

wait_ips_free() {  # <timeout_s> <ip...>  wait until no container on $NET holds any of the IPs
  local t="$1" end used ip busy; shift
  end=$(( $(date +%s) + t ))
  while :; do
    used=$(docker network inspect "$NET" --format '{{range .Containers}}{{.Name}}={{.IPv4Address}} {{end}}' 2>/dev/null)
    busy=""
    for ip in "$@"; do
      case " $used" in *"=$ip/"*) busy="$busy $(tr ' ' '\n' <<<"$used" | grep "=$ip/")";; esac
    done
    [ -z "$busy" ] && return 0
    if [ "$(date +%s)" -ge "$end" ]; then
      log "ERROR: fixed IPs in use on $NET by:$busy (another script without the lock?)"; return 1
    fi
    sleep 1
  done
}

wait_file() {  # <path> <min_bytes> [timeout_s]
  local f="$1" min="$2" t="${3:-10}" end
  end=$(( $(date +%s) + t ))
  while :; do
    if [ -f "$f" ] && [ "$(stat -c %s "$f")" -ge "$min" ]; then return 0; fi
    if [ "$(date +%s)" -ge "$end" ]; then log "timeout: $f did not reach $min B in ${t}s"; return 1; fi
    sleep 0.1
  done
}

wait_pcap() { wait_file "$1" 24 "${2:-10}"; }

wait_log() {  # <file> <ERE> [timeout_s]
  local f="$1" re="$2" t="${3:-20}" end
  end=$(( $(date +%s) + t ))
  until [ -f "$f" ] && grep -Eq "$re" "$f"; do
    if [ "$(date +%s)" -ge "$end" ]; then log "timeout: /$re/ not seen in $f within ${t}s"; return 1; fi
    sleep 0.1
  done
}

wait_tcp_listen() {  # <container> <port> [timeout_s]
  local c="$1" p="$2" t="${3:-10}" end
  end=$(( $(date +%s) + t ))
  until docker exec "$c" ss -Hltn "sport = :$p" 2>/dev/null | grep -q .; do
    if [ "$(date +%s)" -ge "$end" ]; then log "timeout: nothing listening on $c:$p within ${t}s"; return 1; fi
    sleep 0.2
  done
}

wait_exit() {  # <container> [timeout_s] ; prints exit code
  local c="$1" t="${2:-60}" rc
  if rc=$(timeout "$t" docker wait "$c"); then echo "$rc"; return 0; fi
  log "timeout: container $c still running after ${t}s"
  return 1
}

ctr_wait_pcap() {  # <path-in-container> [timeout_s] -> bash snippet on stdout
  local n=$(( ${2:-5} * 10 ))
  printf 'for _i in $(seq %d); do [ "$(stat -c %%s %s 2>/dev/null || echo 0)" -ge 24 ] && break; sleep 0.1; done' "$n" "$1"
}

write_env() {  # <outdir>
  local out="$1" f k
  mkdir -p "$out"; f="$out/env.txt"
  {
    echo "# environment of this run (written by lib.sh write_env)"
    echo "date: $(date -Is)"
    echo "uname -a: $(uname -a)"
    echo "nproc: $(nproc)"
    echo "cpu: $(grep -m1 'model name' /proc/cpuinfo | cut -d: -f2- | sed 's/^ //')"
    echo "docker client: $(docker version --format '{{.Client.Version}}' 2>&1)"
    echo "docker server: $(docker version --format '{{.Server.Version}}' 2>&1)"
    echo "image $IMG id: $(docker image inspect "$IMG" --format '{{.Id}}' 2>&1)"
    echo "image $IMG created: $(docker image inspect "$IMG" --format '{{.Created}}' 2>&1)"
    echo "base image (Dockerfile FROM): $(grep -m1 '^FROM' "$LIB_DIR/Dockerfile" | cut -d' ' -f2)"
    echo "base image local RepoDigests: $(docker image inspect ros:lyrical-ros-base --format '{{json .RepoDigests}}' 2>&1)"
    echo "network $NET: $(docker network inspect "$NET" --format '{{range .IPAM.Config}}{{.Subnet}} gw {{.Gateway}}{{end}}' 2>&1)"
    echo
    echo "# sysctl (read only). host = init network namespace of the host;"
    echo "# container = a fresh container on $NET (its own network namespace; values shown are what /proc/sys exposes there)"
    for k in rmem_max rmem_default wmem_max wmem_default; do
      echo "host      net.core.$k = $(cat /proc/sys/net/core/$k 2>&1)"
    done
    docker run --rm --net "$NET" "$IMG" bash -c \
      'for k in rmem_max rmem_default wmem_max wmem_default; do echo "container net.core.$k = $(cat /proc/sys/net/core/$k 2>&1)"; done' 2>&1
    echo
    echo "# tools inside $IMG"
    docker run --rm --network none "$IMG" bash -c \
      'tshark --version 2>/dev/null | head -1; tcpdump --version 2>&1 | head -2; grep PRETTY /etc/os-release' 2>&1
    echo
    echo "# apt pin check inside $IMG (/opt/exp/apt-pin-check.txt; absent if the image predates it)"
    docker run --rm --network none "$IMG" cat /opt/exp/apt-pin-check.txt 2>&1 || true
    echo
    echo "# ros-lyrical packages: see dpkg_ros_lyrical.txt ($(docker run --rm --network none "$IMG" bash -c 'dpkg -l | grep -c ros-lyrical' 2>&1) lines), full list: dpkg_all.txt"
  } > "$f"
  docker run --rm --network none "$IMG" dpkg -l > "$out/dpkg_all.txt" 2>&1
  grep ros-lyrical "$out/dpkg_all.txt" > "$out/dpkg_ros_lyrical.txt" || true
  # ros2 doctor --report takes ~5 s here; skip it if it does not finish within 20 s
  local t0 t1
  t0=$(date +%s)
  if docker run --rm --net "$NET" "$IMG" bash -c "$ROS_SRC; timeout 20 ros2 doctor --report" > "$out/ros2_doctor.txt" 2>&1; then
    t1=$(date +%s); echo "ros2 doctor --report: ok in $((t1 - t0)) s -> ros2_doctor.txt" >> "$f"
  else
    echo "ros2 doctor --report: skipped (failed or exceeded 20 s), partial output in ros2_doctor.txt" >> "$f"
  fi
}

filter_pcap() {  # <in> <out>
  local in out ind outd
  in="$(realpath "$1")"; out="$(realpath -m "$2")"
  ind="$(dirname "$in")"; outd="$(dirname "$out")"
  mkdir -p "$outd"
  docker run --rm --network none -v "$ind:/fin:ro" -v "$outd:/fout" "$IMG" \
    tshark -r "/fin/$(basename "$in")" -Y "$PCAP_FILTER" -F pcap -w "/fout/$(basename "$out")" 2>/dev/null
}

fix_owner() {  # <dir>
  docker run --rm --network none -v "$(realpath "$1"):/d" "$IMG" chown -R "$(id -u):$(id -g)" /d
}

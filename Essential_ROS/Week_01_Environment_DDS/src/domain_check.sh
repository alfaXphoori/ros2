#!/usr/bin/env bash
# Week 01: ROS 2 environment + DDS (RTPS) port diagnostic
#
# Usage:  domain_check.sh [DOMAIN_ID] [PARTICIPANT_ID]
#         (defaults: DOMAIN_ID=$ROS_DOMAIN_ID or 0, PARTICIPANT_ID=0)
#
# Port mapping from the OMG DDSI-RTPS spec (v2.x, section 9.6.1.1):
#   port = PB + DG*domain + d + PG*participant   (participant term only for unicast)
#   PB=7400  DG=250  PG=2  d0=0 (SPDP multicast)  d2=1 (user multicast)
#                          d1=10 (SPDP unicast)   d3=11 (user unicast)

PB=7400
DG=250
PG=2

DOMAIN="${1:-${ROS_DOMAIN_ID:-0}}"
PARTICIPANT="${2:-0}"

if ! [[ "$DOMAIN" =~ ^[0-9]+$ && "$PARTICIPANT" =~ ^[0-9]+$ ]]; then
    echo "ERROR: DOMAIN_ID and PARTICIPANT_ID must be non-negative integers" >&2
    exit 2
fi

echo "========================================================"
echo "ROS 2 DDS & Network Diagnostic (Week 01)"
echo "========================================================"

echo "[1/3] ROS 2 environment"
echo "  ROS_DISTRO                    : ${ROS_DISTRO:-<not set: source /opt/ros/jazzy/setup.bash>}"
echo "  ROS_DOMAIN_ID                 : ${ROS_DOMAIN_ID:-<not set -> 0>}"
echo "  RMW_IMPLEMENTATION            : ${RMW_IMPLEMENTATION:-<not set -> rmw_fastrtps_cpp (Jazzy default)>}"
echo "  ROS_AUTOMATIC_DISCOVERY_RANGE : ${ROS_AUTOMATIC_DISCOVERY_RANGE:-<not set -> SUBNET>}"

echo ""
echo "[2/3] RTPS ports for domain ${DOMAIN}, participant ${PARTICIPANT}"
echo "  Discovery multicast (SPDP, d0=0)  : $((PB + DG * DOMAIN + 0))"
echo "  User data multicast (d2=1)        : $((PB + DG * DOMAIN + 1))"
echo "  Discovery unicast   (SEDP, d1=10) : $((PB + DG * DOMAIN + 10 + PG * PARTICIPANT))"
echo "  User data unicast   (d3=11)       : $((PB + DG * DOMAIN + 11 + PG * PARTICIPANT))"

# Highest port a domain can use with the ~120 participants ROS 2 assumes per host
LAST_PORT=$((PB + DG * DOMAIN + 11 + PG * 119))
echo "  Port range of this domain         : $((PB + DG * DOMAIN))-${LAST_PORT}"
if [ "$LAST_PORT" -gt 65535 ]; then
    echo "  WARNING: ports above 65535 -> domain ${DOMAIN} cannot work (valid UDP ports end at 65535)"
elif [ -r /proc/sys/net/ipv4/ip_local_port_range ]; then
    read -r EPH_LO EPH_HI < /proc/sys/net/ipv4/ip_local_port_range
    if [ "$LAST_PORT" -ge "$EPH_LO" ] && [ "$((PB + DG * DOMAIN))" -le "$EPH_HI" ]; then
        echo "  WARNING: overlaps the Linux ephemeral range ${EPH_LO}-${EPH_HI}; another program may"
        echo "           already hold one of these ports (use ROS_DOMAIN_ID 0-101 on Linux)"
    else
        echo "  OK: no overlap with the Linux ephemeral range ${EPH_LO}-${EPH_HI}"
    fi
fi

echo ""
echo "[3/3] ROS 2 daemon"
if command -v ros2 >/dev/null 2>&1; then
    echo "  $(ros2 daemon status 2>&1)"
else
    echo "  ros2 CLI not found (environment not sourced)"
fi
echo "========================================================"

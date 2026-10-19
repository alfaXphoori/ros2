#!/usr/bin/env bash
# Week 01: DDS Domain ID and Multicast Diagnostic Script
echo "========================================================"
echo "🤖 ROS 2 DDS & Network Diagnostic Test"
echo "========================================================"

echo "[1/3] Checking ROS 2 Environment Variables:"
echo "ROS_DISTRO: ${ROS_DISTRO:-Not Set}"
echo "ROS_DOMAIN_ID: ${ROS_DOMAIN_ID:-0 (Default)}"
echo "RMW_IMPLEMENTATION: ${RMW_IMPLEMENTATION:-rmw_fastrtps_cpp}"

echo ""
echo "[2/3] Checking ROS 2 Daemon Status:"
ros2 daemon status

echo ""
echo "[3/3] Checking DDS Discovery Multicast Port:"
DOMAIN=${ROS_DOMAIN_ID:-0}
MULTICAST_PORT=$((7400 + 250 * DOMAIN))
echo "Expected Discovery Multicast Port for Domain ${DOMAIN} is: ${MULTICAST_PORT}"

echo ""
echo "✅ DDS Environment Diagnostic Complete!"

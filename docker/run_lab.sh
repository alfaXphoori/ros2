#!/usr/bin/env bash
# Usage:
#   ./docker/run_lab.sh                      -> interactive shell (ROS 2 Jazzy sourced)
#   ./docker/run_lab.sh <command> [args...]  -> run a single command inside the lab container
#
# The repository root is mounted at /workspace (working directory),
# so use repo-relative paths, e.g.:
#   ./docker/run_lab.sh python3 Essential_ROS/Week_02_Nodes_Topics_QoS/src/sensor_qos_publisher.py
#
# If the course packages were built (`make build`), install/setup.bash is sourced too,
# so `ros2 run amr_week02 sensor_qos_publisher` and `ros2 launch amr_week11 ...` work.
#
# Environment variables forwarded from the host (all optional):
#   ROS_DOMAIN_ID (default 0), RMW_IMPLEMENTATION, ROS_AUTOMATIC_DISCOVERY_RANGE,
#   ROS_SECURITY_* (SROS2 lab), GZ_PARTITION (isolate Gazebo transport), DISPLAY
#   LAB_AS_ROOT=1  -> run as root inside the container (default: your host uid/gid,
#                     so build/, log/ and keystores created in the repo stay yours)
#
# Core dumps are disabled (--ulimit core=0): a Nav2 node that crashes on shutdown
# would otherwise drop a ~160 MB core file into the lab folder on every test run.
set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
IMAGE_NAME="ros:lab-runner"

# Build image if missing
if [[ "$(docker images -q ${IMAGE_NAME} 2> /dev/null)" == "" ]]; then
    echo "Building ${IMAGE_NAME} container..."
    docker build -t ${IMAGE_NAME} -f "${DIR}/docker/Dockerfile" "${DIR}/docker"
fi

# Allocate a TTY only when attached to a terminal (allows use from scripts/CI)
TTY_FLAGS="-i"
if [ -t 0 ] && [ -t 1 ]; then
    TTY_FLAGS="-it"
fi

USER_FLAGS=(--user "$(id -u):$(id -g)" -e HOME=/tmp/home)
if [ "${LAB_AS_ROOT:-0}" = "1" ]; then
    USER_FLAGS=()
fi

ENV_FLAGS=(-e ROS_DOMAIN_ID="${ROS_DOMAIN_ID:-0}")
for v in RMW_IMPLEMENTATION ROS_AUTOMATIC_DISCOVERY_RANGE ROS_STATIC_PEERS GZ_PARTITION \
         ROS_SECURITY_KEYSTORE ROS_SECURITY_ENABLE ROS_SECURITY_STRATEGY ROS_SECURITY_ENCLAVE_OVERRIDE; do
    if [ -n "${!v}" ]; then
        ENV_FLAGS+=(-e "${v}=${!v}")
    fi
done

if [ "$#" -eq 0 ]; then
    CMD=(bash)
else
    CMD=("$@")
fi

docker run --rm ${TTY_FLAGS} \
    --net host \
    --ipc host \
    --ulimit core=0 \
    "${USER_FLAGS[@]}" \
    "${ENV_FLAGS[@]}" \
    -e DISPLAY="${DISPLAY}" \
    -v /tmp/.X11-unix:/tmp/.X11-unix:rw \
    -v "${DIR}:/workspace" \
    -w /workspace \
    ${IMAGE_NAME} \
    bash -c 'mkdir -p "$HOME" 2>/dev/null; source /opt/ros/jazzy/setup.bash
             if [ -f /workspace/install/setup.bash ]; then source /workspace/install/setup.bash; fi
             exec "$@"' _ "${CMD[@]}"

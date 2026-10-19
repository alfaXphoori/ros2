#!/usr/bin/env bash
# Usage:
#   ./docker/run_lab.sh                      -> interactive shell (ROS 2 Jazzy sourced)
#   ./docker/run_lab.sh <command> [args...]  -> run a single command inside the lab container
#
# The repository root is mounted at /workspace (working directory),
# so use repo-relative paths, e.g.:
#   ./docker/run_lab.sh python3 Essential_ROS/Week_02_Nodes_Topics_QoS/src/sensor_qos_publisher.py
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

if [ "$#" -eq 0 ]; then
    CMD=(bash)
else
    CMD=("$@")
fi

docker run --rm ${TTY_FLAGS} \
    --net host \
    --ipc host \
    -e DISPLAY="${DISPLAY}" \
    -e ROS_DOMAIN_ID="${ROS_DOMAIN_ID:-0}" \
    -v /tmp/.X11-unix:/tmp/.X11-unix:rw \
    -v "${DIR}:/workspace" \
    -w /workspace \
    ${IMAGE_NAME} \
    bash -c 'source /opt/ros/jazzy/setup.bash && exec "$@"' _ "${CMD[@]}"

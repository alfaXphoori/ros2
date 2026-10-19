#!/usr/bin/env bash
set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

IMAGE_NAME="ros:lab-runner"

# Check if image exists, build if not
if [[ "$(docker images -q ${IMAGE_NAME} 2> /dev/null)" == "" ]]; then
    echo "Building ${IMAGE_NAME} container..."
    docker build -t ${IMAGE_NAME} -f "${DIR}/docker/Dockerfile" "${DIR}/docker"
fi

echo "Starting interactive ROS 2 Jazzy & Gazebo Sim Lab environment..."
docker run --rm -it \
    --net host \
    --ipc host \
    -e DISPLAY="${DISPLAY}" \
    -v /tmp/.X11-unix:/tmp/.X11-unix:rw \
    -v "${DIR}:/workspace" \
    -w /workspace \
    ${IMAGE_NAME} bash

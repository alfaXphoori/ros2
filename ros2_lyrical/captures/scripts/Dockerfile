FROM ros:lyrical-ros-base
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
      ros-lyrical-demo-nodes-cpp ros-lyrical-rmw-zenoh-cpp ros-lyrical-sensor-msgs \
      tcpdump tshark iproute2 && rm -rf /var/lib/apt/lists/*

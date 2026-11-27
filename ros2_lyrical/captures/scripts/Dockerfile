# Image for the wire experiments (docs/03_wire_experiments.md).
#
# Reproducibility layers, from strongest to weakest:
#  1. Base image pinned by digest (verified 2026-11-27 with
#     `docker image inspect ros:lyrical-ros-base --format '{{json .RepoDigests}}'`).
#  2. The apt install line below is unchanged from the image used on 2026-11-24, so a
#     build on a machine that already has that layer reuses it from cache.
#  3. apt-pins.txt = exact versions of the key packages found in that image. The check
#     step at the end compares them with what got installed and writes the result to
#     /opt/exp/apt-pin-check.txt (and prints a WARNING); `--build-arg STRICT_PINS=1`
#     turns a mismatch into a build failure.
#  4. `--build-arg APT_EXACT=1` re-installs the pinned versions with `pkg=version`.
#     Trade-off: packages.ros.org keeps only the latest build of each package, so exact
#     versions usually disappear from the repo after the next sync; then APT_EXACT=1
#     fails ("Version ... was not found"). That is why exact pinning is opt-in and the
#     default is "install latest + record + compare" (the full `dpkg -l` is saved in
#     /opt/exp/dpkg-l.txt so any later image can be diffed against it).
FROM ros:lyrical-ros-base@sha256:c69a7a39142b0a19c8cc5e80a35e9087e2ae46080dfa0a59961ff72287fdc5f6
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
      ros-lyrical-demo-nodes-cpp ros-lyrical-rmw-zenoh-cpp ros-lyrical-sensor-msgs \
      tcpdump tshark iproute2 && rm -rf /var/lib/apt/lists/*
COPY apt-pins.txt /opt/exp/apt-pins.txt
ARG APT_EXACT=0
RUN if [ "$APT_EXACT" = 1 ]; then \
      apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        --allow-downgrades $(cat /opt/exp/apt-pins.txt) && rm -rf /var/lib/apt/lists/*; fi
ARG STRICT_PINS=0
RUN dpkg -l > /opt/exp/dpkg-l.txt \
 && while IFS='=' read -r p v; do \
      have=$(dpkg-query -W -f '${Version}' "$p" 2>/dev/null || echo MISSING); \
      if [ "$have" = "$v" ]; then echo "OK $p $v"; else echo "MISMATCH $p pinned=$v installed=$have"; fi; \
    done < /opt/exp/apt-pins.txt > /opt/exp/apt-pin-check.txt \
 && if grep -q MISMATCH /opt/exp/apt-pin-check.txt; then \
      echo "WARNING: package versions differ from apt-pins.txt:"; grep MISMATCH /opt/exp/apt-pin-check.txt; \
      [ "$STRICT_PINS" != 1 ]; fi

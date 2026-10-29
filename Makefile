# ==============================================================================
# ROS 2 AMR course — build & test every lab package inside the Docker lab image
# ==============================================================================
# All targets run through ./docker/run_lab.sh, so nothing has to be installed on
# the host except Docker (Ubuntu 26.04 has no ROS 2 Jazzy binaries).
#
#   make image                 build the ros:lab-runner image
#   make build                 colcon build every package (Essential_ROS + Advanced_ROS)
#   make test                  build, then colcon test + summary (packages run one at a time:
#                              launch tests share ROS_DOMAIN_ID / GZ_PARTITION)
#   make test PKG=amr_week04   build/test one package (and what it depends on)
#   make lint                  YAML / XML / URDF / markdown-link checks (no ROS graph)
#   make list                  list all course packages
#   make clean                 remove build/ install/ log/

RUN      := ./docker/run_lab.sh
BASES    := --base-paths Essential_ROS Advanced_ROS
ifdef PKG
SELECT   := --packages-up-to $(PKG)
TSELECT  := --packages-select $(PKG)
endif
# Keep labs off the classroom network while testing
export ROS_AUTOMATIC_DISCOVERY_RANGE ?= LOCALHOST
export ROS_DOMAIN_ID ?= 42
export GZ_PARTITION ?= amr_make_test

.PHONY: image build test lint list clean

image:
	docker build -t ros:lab-runner -f docker/Dockerfile docker

build:
	$(RUN) colcon build $(BASES) $(SELECT) --event-handlers console_cohesion+

test: build
	$(RUN) bash -c 'colcon test $(BASES) $(TSELECT) --executor sequential --event-handlers console_cohesion+ --return-code-on-test-failure; rc=$$?; colcon test-result --all | tail -n 25; exit $$rc'

lint:
	$(RUN) bash -c 'yamllint -d "{extends: relaxed, rules: {line-length: disable}}" $$(git ls-files "*.yaml" "*.yml") \
	  && xmllint --noout $$(git ls-files "*.xml" "*.sdf" "*.urdf") \
	  && for f in $$(git ls-files "*.urdf"); do check_urdf $$f >/dev/null || exit 1; done \
	  && python3 scripts/check_links.py'

list:
	$(RUN) colcon list $(BASES) --names-only

clean:
	rm -rf build install log

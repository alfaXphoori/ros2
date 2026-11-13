#!/usr/bin/env python3
"""
Week 12: make sure slam_toolbox reaches ACTIVE, even if the launch autostart misses an event.

  ros2 run amr_week12 slam_lifecycle_guard        (online_async_slam.launch.py starts it)

Why: slam_toolbox's online_async_launch.py (autostart:=true) sends `configure` and then waits
for the node's /slam_toolbox/transition_event "configuring -> inactive" before it sends
`activate`. In a real test run of this course (1 of 5 `make check` rounds) that message never
reached launch: slam_toolbox logged "Configuring", stayed `inactive` and never published /map.

The guard polls lifecycle_msgs/GetState. If the node stays in a stable non-active state
(unconfigured / inactive) for `heal_after` seconds, the guard sends the missing transitions
itself through lifecycle_msgs/ChangeState and logs a WARN. It exits 0 as soon as the node is
ACTIVE - normally after a second or two, without changing anything. Week 14's
nav2_lifecycle_guard does the same for the Nav2 lifecycle nodes.
"""

import signal
import sys
import threading
import time

from lifecycle_msgs.msg import Transition
from lifecycle_msgs.srv import ChangeState, GetState
import rclpy
from rclpy.signals import SignalHandlerOptions

STABLE_INACTIVE = ('unconfigured', 'inactive')


def transitions_for(state):
    """lifecycle transitions that take a node from `state` to ACTIVE."""
    if state == 'unconfigured':
        return [Transition.TRANSITION_CONFIGURE, Transition.TRANSITION_ACTIVATE]
    if state == 'inactive':
        return [Transition.TRANSITION_ACTIVATE]
    return []


def _call(node, client, request, timeout):
    fut = client.call_async(request)
    rclpy.spin_until_future_complete(node, fut, timeout_sec=timeout)
    return fut.result()


def wait_until_active(node, target, heal_after, timeout, stop):
    """True once `target` is ACTIVE; drives it there itself after heal_after s in one state."""
    log = node.get_logger()
    get = node.create_client(GetState, f'/{target}/get_state')
    change = node.create_client(ChangeState, f'/{target}/change_state')
    state, since, healed = None, time.monotonic(), False
    end = time.monotonic() + timeout  # wall time: /clock may not run yet
    while not stop.is_set() and rclpy.ok() and time.monotonic() < end:
        res = _call(node, get, GetState.Request(), 2.0) \
            if get.wait_for_service(timeout_sec=0.5) else None
        if res is not None:
            label = res.current_state.label
            if label == 'active':
                return True
            if label != state:
                state, since = label, time.monotonic()
            stuck = time.monotonic() - since
            if state in STABLE_INACTIVE and stuck > heal_after and not healed:
                healed = True
                log.warn(f'{target} still {state} after {stuck:.0f} s (autostart event lost?) '
                         '-> sending its transitions directly')
                for t in transitions_for(state):
                    req = ChangeState.Request()
                    req.transition.id = t
                    res = _call(node, change, req, 10.0)
                    label = 'configure' if t == Transition.TRANSITION_CONFIGURE else 'activate'
                    log.warn(f'{target} {label} -> '
                             f"{res.success if res is not None else 'no reply'}")
                continue  # read the new state right away
        stop.wait(0.5)
    return False


def main(args=None):
    # Clean shutdown as in Week 2: SIGINT/SIGTERM only set a flag that the polling loop checks.
    rclpy.init(args=args, signal_handler_options=SignalHandlerOptions.NO)
    stop = threading.Event()
    for sig in (signal.SIGINT, signal.SIGTERM):
        signal.signal(sig, lambda *_: stop.set())
    node = rclpy.create_node('slam_lifecycle_guard')
    target = node.declare_parameter('node', 'slam_toolbox').value
    heal_after = node.declare_parameter('heal_after', 15.0).value
    timeout = node.declare_parameter('timeout', 120.0).value
    ok = False
    try:
        ok = wait_until_active(node, target, heal_after, timeout, stop)
        if ok:
            node.get_logger().info(f'{target} is ACTIVE')
        elif not stop.is_set():
            node.get_logger().error(f'{target} not ACTIVE after {timeout:.0f} s')
    finally:
        # stopping: ignore further signals (Python resets our handler at exit -> 2nd Ctrl+C = -2)
        for sig in (signal.SIGINT, signal.SIGTERM):
            signal.signal(sig, signal.SIG_IGN)
        node.destroy_node()
        rclpy.try_shutdown()
    sys.exit(0 if ok or stop.is_set() else 1)  # Ctrl+C before ACTIVE is not an error


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""
Week 14: wait until every Nav2 lifecycle node is ACTIVE, with a watchdog for a lost reply.

  ros2 run amr_week14 nav2_lifecycle_guard --ros-args -p use_sim_time:=true

Why: nav2_lifecycle_manager sends each transition request (configure, activate) once and then
waits for the reply with no timeout (Jazzy: LifecycleServiceClient::change_state(transition)).
In real runs of this course (about 2 in 21 fresh starts) a node executed the transition -
"Configuring" in its own log - but the reply never reached the manager, so the manager and the
whole bringup waited forever. `ros2 lifecycle get /amcl` then shows a *stable* state
(unconfigured / inactive) that never changes.

This guard polls lifecycle_msgs/GetState of every node. A node still in a stable non-active
state after `heal_after` seconds is driven by the guard itself through
lifecycle_msgs/ChangeState (configure, then activate) and logged as WARN. Navigation servers
get twice the time: their manager brings them up one after another, and planner_server waits
for the map -> odom TF that AMCL publishes. Exit code 0 when all nodes are ACTIVE.

The same functions are used by Week 15 (waypoint_patrol) and Week 16 (final_mission_executor).
"""

import sys
import time

from lifecycle_msgs.msg import Transition
from lifecycle_msgs.srv import ChangeState, GetState
import rclpy
from rclpy.executors import ExternalShutdownException

# node_names of the two lifecycle managers in launch/nav2_bringup.launch.py
LOCALIZATION_NODES = ['map_server', 'amcl']
NAVIGATION_NODES = ['controller_server', 'smoother_server', 'planner_server',
                    'behavior_server', 'velocity_smoother', 'collision_monitor',
                    'bt_navigator', 'waypoint_follower']
NAV2_NODES = LOCALIZATION_NODES + NAVIGATION_NODES
STABLE_INACTIVE = ('unconfigured', 'inactive')


def node_to_heal(states, waited, heal_after, healed=(), early=LOCALIZATION_NODES):
    """Next node the guard should transition itself, or None.

    states: {node: state label} in manager order; waited: seconds since the guard started.
    Only stable states are touched (never 'configuring'/'activating', never 'unavailable'),
    each node at most once, in manager order. Nodes in `early` may be healed after
    heal_after s, the rest after 2 * heal_after s.
    """
    for name, state in states.items():
        limit = heal_after * (1.0 if name in early else 2.0)
        if state in STABLE_INACTIVE and waited > limit and name not in healed:
            return name
    return None


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


def ensure_nav2_active(node, nodes=NAV2_NODES, timeout=120.0, heal_after=25.0):
    """Block until all `nodes` are ACTIVE (True) or `timeout` wall seconds pass (False).

    Returns (all_active, states, healed). Uses wall time: the lost reply is a middleware
    problem and must also be detected while /clock is not running yet.
    """
    log = node.get_logger()
    get = {n: node.create_client(GetState, f'/{n}/get_state') for n in nodes}
    change = {n: node.create_client(ChangeState, f'/{n}/change_state') for n in nodes}
    states = {n: 'unavailable' for n in nodes}
    healed = []
    start = time.monotonic()
    try:
        while rclpy.ok() and time.monotonic() - start < timeout:
            for n, cli in get.items():
                if states[n] == 'active' or not cli.wait_for_service(timeout_sec=0.5):
                    continue
                res = _call(node, cli, GetState.Request(), 2.0)
                if res is not None:
                    states[n] = res.current_state.label
            if all(s == 'active' for s in states.values()):
                return True, states, healed
            waited = time.monotonic() - start
            name = node_to_heal(states, waited, heal_after, healed)
            if name is not None:
                healed.append(name)
                log.warn(f'lifecycle guard: {name} still {states[name]} after {waited:.0f} s '
                         '(lifecycle_manager reply lost?) -> sending its transitions directly')
                for t in transitions_for(states[name]):
                    req = ChangeState.Request()
                    req.transition.id = t
                    res = _call(node, change[name], req, 20.0)
                    label = 'configure' if t == Transition.TRANSITION_CONFIGURE else 'activate'
                    log.warn(f"lifecycle guard: {name} {label} -> "
                             f"{res.success if res is not None else 'no reply'}")
                continue  # re-read the states before touching the next node
            time.sleep(0.5)
        return all(s == 'active' for s in states.values()), states, healed
    finally:
        for cli in list(get.values()) + list(change.values()):
            node.destroy_client(cli)


def describe(states, healed):
    """One-line summary for logs, e.g. '10/10 Nav2 lifecycle nodes ACTIVE (guard drove: amcl)'."""
    active = sum(1 for s in states.values() if s == 'active')
    text = f'{active}/{len(states)} Nav2 lifecycle nodes ACTIVE'
    missing = [f'{n}={s}' for n, s in states.items() if s != 'active']
    if missing:
        text += f' (not active: {", ".join(missing)})'
    if healed:
        text += f' (guard drove: {", ".join(healed)})'
    return text


def main(args=None):
    rclpy.init(args=args)
    node = rclpy.create_node('nav2_lifecycle_guard')
    timeout = node.declare_parameter('timeout', 120.0).value
    heal_after = node.declare_parameter('heal_after', 25.0).value
    ok = False
    try:
        ok, states, healed = ensure_nav2_active(node, timeout=timeout, heal_after=heal_after)
        (node.get_logger().info if ok else node.get_logger().error)(describe(states, healed))
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main()

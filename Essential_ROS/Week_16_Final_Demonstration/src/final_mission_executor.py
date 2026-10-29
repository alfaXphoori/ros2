#!/usr/bin/env python3
"""
Week 16: Final Practical Examination mission executor.

  ros2 run amr_week16 final_mission_executor --ros-args -p use_sim_time:=true

Warehouse delivery scenario (map frame, all stations in free space of the real map):
  0. wait until every Nav2 lifecycle node is active (Week 14 nav2_lifecycle_guard),
     then set the AMCL initial pose at Home (0, 0, 0 deg)
  1. Cargo Pickup Bay   ( 1.5,  1.0,  90 deg), dwell 3 s
  2. Dropoff Station    (-1.5, -1.0, 180 deg), dwell 2 s
  3. Home Charging Base ( 0.0,  0.0,   0 deg), dwell 1 s

Every stage is logged with its TaskResult, duration (sim time) and the final
position error reported by Nav2 feedback. The process exits 0 only if all
stages SUCCEEDED (PASS); otherwise it logs FAIL and exits 1.
"""

import math
import sys

from amr_week14.nav2_lifecycle_guard import describe, ensure_nav2_active
from geometry_msgs.msg import PoseStamped
from nav2_simple_commander.robot_navigator import BasicNavigator, TaskResult
import rclpy
from rclpy.executors import ExternalShutdownException

MISSION = [
    {'name': 'Cargo Pickup Bay', 'x': 1.5, 'y': 1.0, 'yaw_deg': 90.0, 'dwell': 3.0},
    {'name': 'Dropoff Station', 'x': -1.5, 'y': -1.0, 'yaw_deg': 180.0, 'dwell': 2.0},
    {'name': 'Home Charging Base', 'x': 0.0, 'y': 0.0, 'yaw_deg': 0.0, 'dwell': 1.0},
]


def create_pose(navigator, x, y, yaw_deg=0.0):
    pose = PoseStamped()
    pose.header.frame_id = 'map'
    pose.header.stamp = navigator.get_clock().now().to_msg()
    pose.pose.position.x = float(x)
    pose.pose.position.y = float(y)
    rad = math.radians(yaw_deg)
    pose.pose.orientation.z = math.sin(rad / 2.0)
    pose.pose.orientation.w = math.cos(rad / 2.0)
    return pose


def evaluate(results):
    """results: list of TaskResult -> (n_succeeded, percent, 'PASS'|'FAIL')."""
    n_ok = sum(1 for r in results if r == TaskResult.SUCCEEDED)
    pct = 100.0 * n_ok / len(MISSION)
    return n_ok, pct, 'PASS' if n_ok == len(MISSION) else 'FAIL'


def now_s(nav):
    return nav.get_clock().now().nanoseconds * 1e-9


def run_mission(nav):
    log = nav.get_logger()
    dwell_scale = nav.declare_parameter('dwell_scale', 1.0).value
    timeout = nav.declare_parameter('stage_timeout', 120.0).value
    bringup_timeout = nav.declare_parameter('bringup_timeout', 150.0).value

    log.info('AMR-101 final mission: initial pose (0.0, 0.0, 0 deg), waiting for Nav2')
    # waitUntilNav2Active() has no timeout and would wait forever if a lifecycle_manager
    # reply is lost; the Week 14 guard heals that case and gives up after bringup_timeout
    ok, states, healed = ensure_nav2_active(nav, timeout=bringup_timeout)
    (log.info if ok else log.error)(describe(states, healed))
    if not ok:
        log.error(f'MISSION SUMMARY: 0/{len(MISSION)} stages SUCCEEDED (0%), '
                  'Nav2 not active -> FAIL')
        return False
    nav.setInitialPose(create_pose(nav, 0.0, 0.0, 0.0))
    nav.waitUntilNav2Active(localizer='amcl')
    log.info('Stage 0 Localization + Nav2 bringup: ACTIVE')

    results = []
    mission_start = now_s(nav)
    for idx, wp in enumerate(MISSION, start=1):
        log.info(f"Stage {idx}/{len(MISSION)} -> {wp['name']} "
                 f"(x={wp['x']:.2f}, y={wp['y']:.2f}, yaw={wp['yaw_deg']:.0f} deg)")
        t0 = now_s(nav)
        if not nav.goToPose(create_pose(nav, wp['x'], wp['y'], wp['yaw_deg'])):
            log.error(f'Stage {idx}: goal rejected')
            results.append(TaskResult.FAILED)
            break
        last, canceled = None, False
        while not nav.isTaskComplete():
            fb = nav.getFeedback()
            if fb is not None:
                last = fb
            if not canceled and now_s(nav) - t0 > timeout:
                log.error(f'Stage {idx}: no result after {timeout:.0f} s, canceling')
                nav.cancelTask()
                canceled = True
        result = nav.getResult()
        results.append(result)
        dt = now_s(nav) - t0
        err = ''
        if last is not None:
            p = last.current_pose.pose.position
            err = f', final position error {math.hypot(p.x - wp["x"], p.y - wp["y"]):.2f} m'
        if result == TaskResult.SUCCEEDED:
            log.info(f"Stage {idx} {wp['name']}: SUCCEEDED in {dt:.1f} s{err}")
            dwell_end = now_s(nav) + wp['dwell'] * dwell_scale
            while now_s(nav) < dwell_end:      # spin so /clock keeps updating
                rclpy.spin_once(nav, timeout_sec=0.1)
        else:
            log.error(f"Stage {idx} {wp['name']}: {result.name} after {dt:.1f} s{err}")
            break

    n_ok, pct, verdict = evaluate(results)
    total = now_s(nav) - mission_start
    summary = (f'MISSION SUMMARY: {n_ok}/{len(MISSION)} stages SUCCEEDED ({pct:.0f}%), '
               f'total {total:.1f} s (sim time) -> {verdict}')
    (log.info if verdict == 'PASS' else log.error)(summary)
    return verdict == 'PASS'


def main():
    rclpy.init()
    navigator = BasicNavigator('final_mission_executor')
    ok = False
    try:
        ok = run_mission(navigator)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        navigator.destroy_node()
        rclpy.try_shutdown()
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main()

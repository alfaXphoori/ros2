#!/usr/bin/env python3
"""
Advanced Module 06: Kidnapped-robot demonstration (oral defense scenario), measured honestly.

  ros2 launch amr_adv06 full_warehouse_system.launch.py headless:=true      # terminal 1
  ros2 run amr_adv06 kidnap_demo --ros-args -p use_sim_time:=true           # terminal 2

1. AMCL localised at Home; the robot is teleported in Gazebo (/world/warehouse/set_pose).
2. Week 14 AMCL uses recovery_alpha_slow = recovery_alpha_fast = 0.0, i.e. it NEVER injects
   random particles by itself -> the error stays large (it is not "recovering by default").
3. Method A - global localization: /reinitialize_global_localization (std_srvs/Empty) spreads
   the particles over the whole free map, then the robot spins 360 deg (Nav2 Spin) and AMCL is
   forced to update (/request_nomotion_update). The warehouse is mirror-symmetric about x = 0
   (shelves at x = +-2 m), so the filter may lock onto the mirror pose: perceptual aliasing.
4. Method B - operator re-localisation: a new /initialpose (RViz "2D Pose Estimate").

Every error is AMCL (TF map -> base_footprint) vs the Gazebo ground truth.
"""

import math
import sys
import threading
import time

from geometry_msgs.msg import PoseWithCovarianceStamped
from nav2_simple_commander.robot_navigator import BasicNavigator
import rclpy
from rclpy.executors import ExternalShutdownException, SingleThreadedExecutor
from std_srvs.srv import Empty

try:
    from amr_adv06.capstone_mission import make_pose, Monitor
except ImportError:  # python3 src/kidnap_demo.py
    from capstone_mission import make_pose, Monitor


def teleport(x, y, yaw, model='diff_drive_robot', world='warehouse'):
    from gz.msgs10.boolean_pb2 import Boolean
    from gz.msgs10.pose_pb2 import Pose
    from gz.transport13 import Node as GzNode
    req = Pose()
    req.name = model
    req.position.x, req.position.y, req.position.z = x, y, 0.0
    req.orientation.z, req.orientation.w = math.sin(yaw / 2), math.cos(yaw / 2)
    ok, rep = GzNode().request(f'/world/{world}/set_pose', req, Pose, Boolean, 3000)
    return ok and rep.data


def mirror(pose):
    """Pose with the same LiDAR view in the x-mirrored warehouse."""
    x, y, yaw = pose
    return -x, y, math.atan2(math.sin(math.pi - yaw), math.cos(math.pi - yaw))


class KidnapDemo:
    def __init__(self, nav, mon):
        self.nav, self.mon = nav, mon
        self.target = nav.declare_parameter('kidnap_pose', [1.5, -2.0, 0.0]).value

    def say(self, text):
        print(text, flush=True)

    def call(self, name):
        cli = self.nav.create_client(Empty, name)
        if not cli.wait_for_service(timeout_sec=10.0):
            raise RuntimeError(f'service {name} not available')
        fut = cli.call_async(Empty.Request())
        rclpy.spin_until_future_complete(self.nav, fut, timeout_sec=10.0)
        self.nav.destroy_client(cli)

    def wait(self, seconds):
        end = self.mon.now_s() + seconds
        while self.mon.now_s() < end:
            time.sleep(0.05)

    def report(self, label):
        gt, am = self.mon.gt_pose(), self.mon.amcl_pose()
        err = math.hypot(am[0] - gt[0], am[1] - gt[1])
        mx, my, _ = mirror(gt)
        err_m = math.hypot(am[0] - mx, am[1] - my)
        self.say(f'{label}: true x={gt[0]:+.2f} y={gt[1]:+.2f} yaw={math.degrees(gt[2]):+6.1f} | '
                 f'AMCL x={am[0]:+.2f} y={am[1]:+.2f} yaw={math.degrees(am[2]):+6.1f} | '
                 f'AMCL error {err:.2f} m (distance to the mirror pose {err_m:.2f} m)')
        return err

    def nomotion_updates(self, n=10):
        for _ in range(n):
            self.call('/request_nomotion_update')
            self.wait(0.3)

    def run(self):
        self.nav.setInitialPose(make_pose(self.nav, 0.0, 0.0, 0.0))
        self.nav.waitUntilNav2Active(localizer='amcl')
        self.wait(2.0)
        self.report('1. localised at Home         ')
        x, y, yaw = self.target
        self.say(f'2. KIDNAP: Gazebo set_pose -> x={x:.2f} y={y:.2f} yaw={math.degrees(yaw):.0f}'
                 f' deg: {teleport(x, y, yaw)}')
        self.wait(3.0)
        self.nomotion_updates(5)
        before = self.report('   after kidnap (5 updates)  ')

        self.say('3. Method A: /reinitialize_global_localization + Spin 360 deg + 10 updates')
        self.call('/reinitialize_global_localization')
        self.nav.spin(spin_dist=2 * math.pi, time_allowance=40)
        while not self.nav.isTaskComplete():
            pass
        self.nomotion_updates(10)
        err_a = self.report('   after global localization ')

        self.say('4. Method B: operator re-localisation (/initialpose = true pose)')
        gt = self.mon.gt_pose()
        msg = PoseWithCovarianceStamped()
        msg.header = make_pose(self.nav, gt[0], gt[1], math.degrees(gt[2])).header
        msg.pose.pose = make_pose(self.nav, gt[0], gt[1], math.degrees(gt[2])).pose
        msg.pose.covariance[0] = msg.pose.covariance[7] = 0.25 ** 2
        msg.pose.covariance[35] = math.radians(10) ** 2
        self.nav.initial_pose_pub.publish(msg)
        self.wait(1.0)
        self.nomotion_updates(5)
        err_b = self.report('   after /initialpose        ')
        self.say(f'SUMMARY: kidnapped error {before:.2f} m (no self-recovery), global '
                 f'localization {err_a:.2f} m, operator /initialpose {err_b:.2f} m')
        return err_b <= 0.10


def main():
    rclpy.init()
    nav = BasicNavigator('kidnap_demo')
    mon = Monitor(nav.get_parameter('use_sim_time').value)
    executor = SingleThreadedExecutor()
    executor.add_node(mon)
    threading.Thread(target=executor.spin, daemon=True).start()
    ok = False
    try:
        ok = KidnapDemo(nav, mon).run()
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        executor.shutdown()
        mon.destroy_node()
        nav.destroy_node()
        rclpy.try_shutdown()
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main()

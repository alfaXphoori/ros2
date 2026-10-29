#!/usr/bin/env python3
"""Headless Gazebo probe: DiffDrive /odom vs ground-truth pose for the Week 07 robot.

Starts `gz sim -s -r` on worlds/flat_ground.sdf, spawns urdf/diff_drive_robot.urdf,
drives three manoeuvres on the gz /cmd_vel topic and compares the DiffDrive
odometry with /world/flat_ground/dynamic_pose/info (ground truth).

  python3 test/gz_odom_probe.py [path/to/robot.urdf]     # prints a table
Used by test_gz_odometry.py.
"""
import math
import os
import subprocess
import sys
import threading
import time

from gz.msgs10.odometry_pb2 import Odometry
from gz.msgs10.pose_v_pb2 import Pose_V
from gz.msgs10.twist_pb2 import Twist
from gz.transport13 import Node

PKG_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORLD = os.path.join(PKG_DIR, 'worlds', 'flat_ground.sdf')
URDF = os.path.join(PKG_DIR, 'urdf', 'diff_drive_robot.urdf')
WORLD_NAME = 'flat_ground'
MODEL = 'amr'

# name, v [m/s], w [rad/s], duration [s]
MANOEUVRES = [
    ('rotate_in_place', 0.0, 0.6, 5.0),
    ('arc', 0.2, 0.4, 5.0),
    ('straight', 0.3, 0.0, 5.0),
]


def yaw_of(q):
    return math.atan2(2.0 * (q.w * q.z + q.x * q.y), 1.0 - 2.0 * (q.y * q.y + q.z * q.z))


class Track:
    """Latest pose plus a continuously unwrapped yaw."""

    def __init__(self):
        self.lock = threading.Lock()
        self.x = self.y = None
        self.yaw = 0.0          # unwrapped
        self._last_raw = None
        self.count = 0

    def update(self, x, y, raw_yaw):
        with self.lock:
            if self._last_raw is not None:
                d = raw_yaw - self._last_raw
                d = (d + math.pi) % (2 * math.pi) - math.pi
                self.yaw += d
            else:
                self.yaw = raw_yaw
            self._last_raw = raw_yaw
            self.x, self.y = x, y
            self.count += 1

    def snapshot(self):
        with self.lock:
            return self.x, self.y, self.yaw


def relative(start, end):
    """Displacement of end in start's heading frame, and yaw change."""
    dx, dy = end[0] - start[0], end[1] - start[1]
    c, s = math.cos(start[2]), math.sin(start[2])
    return c * dx + s * dy, -s * dx + c * dy, end[2] - start[2]


def run(urdf=URDF, manoeuvres=MANOEUVRES, log=print):
    env = dict(os.environ)
    sim = subprocess.Popen(['gz', 'sim', '-s', '-r', '--headless-rendering', WORLD],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, env=env,
                           start_new_session=True)
    try:
        node = Node()
        odom, truth = Track(), Track()

        def on_odom(msg):
            p = msg.pose
            odom.update(p.position.x, p.position.y, yaw_of(p.orientation))

        def on_pose(msg):
            for p in msg.pose:
                if p.name == MODEL:
                    truth.update(p.position.x, p.position.y, yaw_of(p.orientation))

        node.subscribe(Odometry, '/odom', on_odom)
        node.subscribe(Pose_V, f'/world/{WORLD_NAME}/dynamic_pose/info', on_pose)
        pub = node.advertise('/cmd_vel', Twist)

        # Spawn the URDF once the world's create service exists
        req = f'sdf_filename: "{urdf}", name: "{MODEL}", pose: {{position: {{z: 0.005}}}}'
        deadline = time.monotonic() + 60
        while True:
            r = subprocess.run(['gz', 'service', '-s', f'/world/{WORLD_NAME}/create',
                                '--reqtype', 'gz.msgs.EntityFactory',
                                '--reptype', 'gz.msgs.Boolean', '--timeout', '3000',
                                '--req', req], capture_output=True, text=True, env=env)
            if 'data: true' in r.stdout:
                break
            if time.monotonic() > deadline:
                raise RuntimeError(f'could not spawn robot: {r.stdout} {r.stderr}')
            time.sleep(1.0)

        def drive(v, w, seconds):
            msg = Twist()
            msg.linear.x, msg.angular.z = v, w
            end = time.monotonic() + seconds
            while time.monotonic() < end:
                pub.publish(msg)
                time.sleep(0.05)

        drive(0.0, 0.0, 3.0)    # settle on the ground
        if odom.count == 0 or truth.count == 0:
            raise RuntimeError('no /odom or ground-truth pose received')
        results = {}
        for name, v, w, secs in manoeuvres:
            s_odom, s_truth = odom.snapshot(), truth.snapshot()
            drive(v, w, secs)
            drive(0.0, 0.0, 1.5)
            o = relative(s_odom, odom.snapshot())
            t = relative(s_truth, truth.snapshot())
            results[name] = {'odom': o, 'truth': t}
            log(f'{name:16s} odom: dx={o[0]:+.3f} dy={o[1]:+.3f} dyaw={math.degrees(o[2]):+7.1f} deg'
                f' | truth: dx={t[0]:+.3f} dy={t[1]:+.3f} dyaw={math.degrees(t[2]):+7.1f} deg')
        return results
    finally:
        os.killpg(sim.pid, 15)
        try:
            sim.wait(timeout=10)
        except subprocess.TimeoutExpired:
            os.killpg(sim.pid, 9)
            sim.wait()


if __name__ == '__main__':
    run(sys.argv[1] if len(sys.argv) > 1 else URDF)

"""Week 11: the safety gate must stop forward motion when an obstacle is close,
even while a command source keeps publishing (no last-writer race)."""

import math
import time

from amr_week11.emergency_stop_node import EmergencyStopNode, front_min_range, gate_command
from geometry_msgs.msg import Twist
import pytest
import rclpy
from rclpy.executors import SingleThreadedExecutor
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import LaserScan

N = 360
INC = 2 * math.pi / N


def make_scan(front=5.0, side=5.0):
    """360-beam scan from -pi; beams within +-30 deg read `front`, others `side`."""
    msg = LaserScan()
    msg.header.frame_id = 'lidar_link'
    msg.angle_min, msg.angle_max, msg.angle_increment = -math.pi, math.pi - INC, INC
    msg.range_min, msg.range_max = 0.12, 10.0
    msg.ranges = [front if abs(-math.pi + i * INC) <= math.radians(30) else side
                  for i in range(N)]
    return msg


# ---------- pure functions ----------

def test_front_min_ignores_sides_and_invalid():
    s = make_scan(front=2.0, side=0.2)          # wall close on the side only
    assert front_min_range(s.ranges, s.angle_min, s.angle_increment, s.range_min,
                           s.range_max, math.radians(30)) == pytest.approx(2.0)
    s.ranges[180] = 0.05                        # below range_min -> invalid
    s.ranges[181] = math.inf                    # no return
    assert front_min_range(s.ranges, s.angle_min, s.angle_increment, s.range_min,
                           s.range_max, math.radians(30)) == pytest.approx(2.0)


def test_front_min_scan_starting_at_zero():
    # scan convention 0..2pi: beams near 2pi are also "front"
    ranges = [5.0] * N
    ranges[N - 5] = 0.3
    assert front_min_range(ranges, 0.0, INC, 0.12, 10.0, math.radians(30)) == pytest.approx(0.3)


def test_gate_blocks_forward_only():
    assert gate_command(0.4, 0.0, 0.25, 0.35) == (0.0, 0.0, True)
    assert gate_command(0.4, 0.5, 0.25, 0.35) == (0.0, 0.5, True)    # may turn away
    assert gate_command(-0.2, 0.0, 0.25, 0.35) == (-0.2, 0.0, True)  # may reverse
    assert gate_command(0.4, 0.1, 1.00, 0.35) == (0.4, 0.1, False)   # clear: pass-through


# ---------- node behaviour with synthetic LaserScan ----------

@pytest.fixture
def ros():
    rclpy.init()
    gate = EmergencyStopNode()
    helper = rclpy.create_node('estop_test_helper')
    ex = SingleThreadedExecutor()
    ex.add_node(gate)
    ex.add_node(helper)
    out = []
    helper.create_subscription(Twist, 'cmd_vel', out.append, 10)
    pubs = {
        'scan': helper.create_publisher(LaserScan, 'scan', qos_profile_sensor_data),
        'cmd': helper.create_publisher(Twist, 'cmd_vel_in', 10),
    }
    yield ex, pubs, out
    ex.shutdown()
    gate.destroy_node()
    helper.destroy_node()
    rclpy.try_shutdown()


def drive(ex, pubs, out, front, seconds=1.0, vx=0.4):
    """Publish scan + cmd_vel_in(vx) at 20 Hz like teleop would; return outputs."""
    out.clear()
    cmd = Twist()
    cmd.linear.x = vx
    end = time.monotonic() + seconds
    while time.monotonic() < end:
        pubs['scan'].publish(make_scan(front=front))
        pubs['cmd'].publish(cmd)
        ex.spin_once(timeout_sec=0.05)
    return list(out)


def test_node_passes_through_when_clear(ros):
    ex, pubs, out = ros
    msgs = drive(ex, pubs, out, front=3.0)
    assert len(msgs) > 5
    assert msgs[-1].linear.x == pytest.approx(0.4)


def test_node_outputs_zero_with_obstacle_at_25cm(ros):
    ex, pubs, out = ros
    drive(ex, pubs, out, front=3.0, seconds=0.5)
    msgs = drive(ex, pubs, out, front=0.25)      # input keeps asking for 0.4 m/s
    assert len(msgs) > 5
    # after the first scan with the obstacle, every output must be a stop
    tail = msgs[3:]
    assert all(m.linear.x == 0.0 and m.angular.z == 0.0 for m in tail), \
        [m.linear.x for m in tail]


def test_node_fail_safe_without_scan(ros):
    ex, pubs, out = ros
    cmd = Twist()
    cmd.linear.x = 0.4
    for _ in range(20):
        pubs['cmd'].publish(cmd)
        ex.spin_once(timeout_sec=0.05)
    assert out and all(m.linear.x == 0.0 for m in out)


# ---------- ground-truth helper (pure parsing) ----------

def test_parse_pose_v():
    from amr_week11.ground_truth import parse_pose_v
    text = '''pose {
  name: "ground_plane"
  id: 4
  position {
  }
  orientation {
    w: 1
  }
}
pose {
  name: "diff_drive_robot"
  id: 9
  position {
    x: 1.5
    y: -0.25
    z: 0.08
  }
  orientation {
    z: 0.70710678
    w: 0.70710678
  }
}
'''
    x, y, yaw = parse_pose_v(text, 'diff_drive_robot')
    assert (x, y) == (1.5, -0.25)
    assert yaw == pytest.approx(math.pi / 2, abs=1e-6)

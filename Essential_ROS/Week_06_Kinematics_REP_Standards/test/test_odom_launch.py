"""launch_testing: feed /cmd_vel to diff_drive_kinematics and check /odom_calculated + /tf,
then check the cmd_vel watchdog stops dead reckoning when commands stop."""
import math
import time
import unittest

import launch
import launch_ros.actions
import launch_testing.actions
import launch_testing.asserts
import pytest
import rclpy
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from rclpy.duration import Duration
from rclpy.time import Time
from tf2_ros import Buffer, TransformListener


@pytest.mark.launch_test
def generate_test_description():
    node = launch_ros.actions.Node(package='amr_week06', executable='diff_drive_kinematics',
                                   parameters=[{'cmd_vel_timeout': 0.5}], output='screen')
    return launch.LaunchDescription([node, launch_testing.actions.ReadyToTest()]), {'kin': node}


def yaw_of(q):
    return math.atan2(2.0 * (q.w * q.z + q.x * q.y), 1.0 - 2.0 * (q.y * q.y + q.z * q.z))


class TestOdometry(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        rclpy.init()
        cls.node = rclpy.create_node('odom_probe')
        cls.odom = []
        cls.node.create_subscription(Odometry, '/odom_calculated', cls.odom.append, 10)
        cls.pub = cls.node.create_publisher(Twist, '/cmd_vel', 10)
        cls.tf_buffer = Buffer()
        cls.tf_listener = TransformListener(cls.tf_buffer, cls.node)

    @classmethod
    def tearDownClass(cls):
        cls.node.destroy_node()
        rclpy.shutdown()

    def spin_for(self, seconds, cmd=None, until=None):
        end = time.monotonic() + seconds
        next_pub = 0.0
        while time.monotonic() < end and not (until and until()):
            if cmd is not None and time.monotonic() >= next_pub:
                self.pub.publish(cmd)
                next_pub = time.monotonic() + 0.1  # 10 Hz like `ros2 topic pub -r 10`
            rclpy.spin_once(self.node, timeout_sec=0.02)

    def test_1_odom_and_tf(self):
        # wait for the node + the subscription match
        end = time.monotonic() + 15.0
        while (not self.odom or self.node.count_subscribers('/cmd_vel') == 0) \
                and time.monotonic() < end:
            rclpy.spin_once(self.node, timeout_sec=0.1)
        self.assertTrue(self.odom, 'no /odom_calculated')
        first = self.odom[-1]
        self.assertEqual(first.header.frame_id, 'odom')
        self.assertEqual(first.child_frame_id, 'base_footprint')

        # drive straight at 0.2 m/s; first wait until the node reports the commanded speed
        cmd = Twist()
        cmd.linear.x = 0.2
        self.spin_for(10.0, cmd,
                      until=lambda: abs(self.odom[-1].twist.twist.linear.x - 0.2) < 1e-9)
        start = self.odom[-1]
        self.spin_for(2.0, cmd)
        last = self.odom[-1]
        elapsed = Time.from_msg(last.header.stamp) - Time.from_msg(start.header.stamp)
        elapsed = elapsed.nanoseconds / 1e9
        self.assertGreater(elapsed, 1.5)
        self.assertAlmostEqual(last.twist.twist.linear.x, 0.2, places=6)
        # dead reckoning: distance = v * t (stamps of the odometry messages)
        self.assertAlmostEqual(last.pose.pose.position.x - start.pose.pose.position.x,
                               0.2 * elapsed, delta=0.01)
        self.assertAlmostEqual(last.pose.pose.position.y, 0.0, places=6)

        # TF odom -> base_footprint matches the odometry message (REP 105 chain)
        tf = self.tf_buffer.lookup_transform('odom', 'base_footprint', Time(),
                                             timeout=Duration(seconds=2.0))
        self.assertAlmostEqual(tf.transform.translation.x, self.odom[-1].pose.pose.position.x,
                               delta=0.02)

        # spin in place: x, y stay, yaw grows CCW
        x1 = self.odom[-1].pose.pose.position.x
        cmd = Twist()
        cmd.angular.z = 0.5
        self.spin_for(2.0, cmd)
        last = self.odom[-1]
        self.assertAlmostEqual(last.pose.pose.position.x, x1, delta=0.03)  # last straight step
        self.assertGreater(yaw_of(last.pose.pose.orientation), 0.6)

    def test_2_watchdog_stops_dead_reckoning(self):
        cmd = Twist()
        cmd.linear.x = 0.3
        self.spin_for(1.0, cmd)
        self.spin_for(1.0)  # no more commands: > cmd_vel_timeout (0.5 s)
        x_stopped = self.odom[-1].pose.pose.position.x
        self.assertEqual(self.odom[-1].twist.twist.linear.x, 0.0)
        self.spin_for(1.5)
        self.assertAlmostEqual(self.odom[-1].pose.pose.position.x, x_stopped, places=9)

    def test_3_watchdog_logged(self, proc_output, kin):
        proc_output.assertWaitFor('stopping wheels', process=kin, timeout=5)


@launch_testing.post_shutdown_test()
class TestAfterShutdown(unittest.TestCase):

    def test_exit_codes(self, proc_info):
        launch_testing.asserts.assertExitCodes(proc_info)

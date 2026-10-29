"""launch_testing: vision pipeline with the tag visible at a known pose.

* /detected_dock_pose (PoseStamped) carries the image header (same stamp, optical frame)
* pose error vs. the rendered ground truth < 1 cm and < 2 deg
* /perception/detections is a vision_msgs/Detection2DArray with the two scene objects
* camera topics are offered BEST_EFFORT (qos_profile_sensor_data)
"""
import math
import os
import time
import unittest

import launch
import launch_testing.actions
import numpy as np
import pytest
import rclpy
from ament_index_python.packages import get_package_share_directory
from geometry_msgs.msg import PoseStamped
from launch.launch_description_sources import PythonLaunchDescriptionSource
from rclpy.qos import ReliabilityPolicy, qos_profile_sensor_data
from sensor_msgs.msg import Image
from vision_msgs.msg import Detection2DArray

from amr_adv02 import vision_utils as vu

TAG = {'tag_x': 0.12, 'tag_y': 0.04, 'tag_z': 0.85, 'tag_yaw_deg': -20.0}


@pytest.mark.launch_test
def generate_test_description():
    launch_file = os.path.join(get_package_share_directory('amr_adv02'), 'launch',
                               'vision_pipeline.launch.py')
    return launch.LaunchDescription([
        launch.actions.IncludeLaunchDescription(
            PythonLaunchDescriptionSource(launch_file),
            launch_arguments={k: str(v) for k, v in TAG.items()}.items()),
        launch_testing.actions.ReadyToTest(),
    ])


def spin_until(node, predicate, timeout):
    end = time.monotonic() + timeout
    while time.monotonic() < end and not predicate():
        rclpy.spin_once(node, timeout_sec=0.05)
    return predicate()


class TestVisionPipeline(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        rclpy.init()
        cls.node = rclpy.create_node('adv02_probe')
        cls.image_stamps = set()
        cls.poses, cls.dets = [], []

        def add_stamp(msg):
            cls.image_stamps.add((msg.header.stamp.sec, msg.header.stamp.nanosec))
        # images are BEST_EFFORT (a probe may miss some); the camera publishes the ground truth
        # RELIABLY with the very same header, so its stamps are the complete list of frames
        cls.node.create_subscription(Image, '/camera/image_raw', add_stamp, qos_profile_sensor_data)
        cls.node.create_subscription(PoseStamped, '/camera/tag_pose_ground_truth', add_stamp, 50)
        cls.node.create_subscription(PoseStamped, '/detected_dock_pose', cls.poses.append, 10)
        cls.node.create_subscription(Detection2DArray, '/perception/detections',
                                     cls.dets.append, 10)

    @classmethod
    def tearDownClass(cls):
        cls.node.destroy_node()
        rclpy.shutdown()

    def test_dock_pose_accuracy_and_header(self):
        self.assertTrue(spin_until(self.node, lambda: len(self.poses) >= 5, 30.0),
                        'no PoseStamped on /detected_dock_pose')
        R_true = vu.tag_rotation_in_camera(math.radians(TAG['tag_yaw_deg']))
        t_true = np.array([TAG['tag_x'], TAG['tag_y'], TAG['tag_z']])
        for p in self.poses:
            self.assertEqual(p.header.frame_id, 'camera_optical_link')
            self.assertIn((p.header.stamp.sec, p.header.stamp.nanosec), self.image_stamps,
                          'pose stamp is not the stamp of an image')
            t = np.array([p.pose.position.x, p.pose.position.y, p.pose.position.z])
            q = p.pose.orientation
            R = vu.quaternion_to_rotation(q.x, q.y, q.z, q.w)
            self.assertLess(np.linalg.norm(t - t_true), 0.01)
            self.assertLess(vu.rotation_angle_deg(R_true, R), 2.0)
        # quaternion sign must be continuous (q and -q averaged by a filter -> NaN)
        qs = [(p.pose.orientation.x, p.pose.orientation.y, p.pose.orientation.z,
               p.pose.orientation.w) for p in self.poses]
        for a, b in zip(qs, qs[1:]):
            self.assertGreater(sum(x * y for x, y in zip(a, b)), 0.0, 'quaternion sign flipped')

    def test_detections_are_detection2darray(self):
        self.assertTrue(spin_until(self.node, lambda: len(self.dets) >= 3, 30.0))
        types = dict(self.node.get_topic_names_and_types())
        self.assertEqual(types['/perception/detections'], ['vision_msgs/msg/Detection2DArray'])
        last = self.dets[-1]
        self.assertIn((last.header.stamp.sec, last.header.stamp.nanosec), self.image_stamps)
        classes = sorted(d.results[0].hypothesis.class_id for d in last.detections)
        self.assertEqual(classes, ['pallet_cargo', 'safety_cone'])

    def test_camera_qos_is_sensor_data(self):
        self.assertTrue(spin_until(
            self.node, lambda: self.node.get_publishers_info_by_topic('/camera/image_raw'), 15.0))
        for info in self.node.get_publishers_info_by_topic('/camera/image_raw'):
            self.assertEqual(info.qos_profile.reliability, ReliabilityPolicy.BEST_EFFORT)

"""launch_testing: with the tag removed from the scene the tracker publishes NO pose
(the old tracker published a constant z = 0.8 m pose for every image)."""
import os
import time
import unittest

import launch
import launch_testing.actions
import pytest
import rclpy
from ament_index_python.packages import get_package_share_directory
from geometry_msgs.msg import PoseStamped
from launch.launch_description_sources import PythonLaunchDescriptionSource
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import Image
from vision_msgs.msg import Detection2DArray


@pytest.mark.launch_test
def generate_test_description():
    launch_file = os.path.join(get_package_share_directory('amr_adv02'), 'launch',
                               'vision_pipeline.launch.py')
    return launch.LaunchDescription([
        launch.actions.IncludeLaunchDescription(
            PythonLaunchDescriptionSource(launch_file),
            launch_arguments={'tag_visible': 'false'}.items()),
        launch_testing.actions.ReadyToTest(),
    ])


class TestNoTag(unittest.TestCase):

    def test_no_pose_without_tag(self):
        rclpy.init()
        node = rclpy.create_node('adv02_no_tag_probe')
        images, poses, dets = [], [], []
        node.create_subscription(Image, '/camera/image_raw', images.append,
                                 qos_profile_sensor_data)
        node.create_subscription(PoseStamped, '/detected_dock_pose', poses.append, 10)
        node.create_subscription(Detection2DArray, '/perception/detections', dets.append, 10)
        try:
            end = time.monotonic() + 30.0
            while time.monotonic() < end and (len(images) < 20 or len(dets) < 10):
                rclpy.spin_once(node, timeout_sec=0.05)
            self.assertGreaterEqual(len(images), 20, 'camera is not publishing')
            self.assertGreaterEqual(len(dets), 10, 'tracker/detector pipeline not running')
            self.assertEqual(poses, [], 'a dock pose was published although no tag is visible')
        finally:
            node.destroy_node()
            rclpy.shutdown()

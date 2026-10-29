"""Pure unit tests (no ROS graph): REP 103 quaternion, URDF consistency, lecture example."""
import math
import os
import sys
import xml.etree.ElementTree as ET

import pytest
from geometry_msgs.msg import PointStamped
from tf2_geometry_msgs import do_transform_point

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                'src'))
import static_sensor_broadcaster as bc  # noqa: E402


def test_rep103_optical_quaternion():
    q = bc.euler_to_quaternion(-math.pi / 2, 0.0, -math.pi / 2)
    assert q == pytest.approx((-0.5, 0.5, -0.5, 0.5), abs=1e-12)


@pytest.mark.parametrize('frame', bc.SENSOR_FRAMES, ids=lambda f: f[1])
def test_quaternions_are_unit(frame):
    q = bc.euler_to_quaternion(*frame[3])
    assert sum(v * v for v in q) == pytest.approx(1.0, abs=1e-12)


def test_lecture_example_camera_point_to_base_link():
    camera = next(f for f in bc.SENSOR_FRAMES if f[1] == 'camera_link')
    tf = bc.make_transform(PointStamped().header.stamp, *camera)
    pt = PointStamped()
    pt.header.frame_id = 'camera_link'
    pt.point.x, pt.point.y, pt.point.z = 1.2, 0.3, 0.0
    out = do_transform_point(pt, tf)
    assert (out.point.x, out.point.y, out.point.z) == pytest.approx((1.40, 0.30, 0.02))
    assert out.header.frame_id == 'base_link'


def test_broadcaster_matches_week07_urdf():
    """The broadcaster and the URDF must agree, so either can be the single TF source."""
    try:
        from ament_index_python.packages import get_package_share_directory
        urdf = os.path.join(get_package_share_directory('amr_week07'),
                            'urdf', 'diff_drive_robot.urdf')
    except Exception:  # package not built/sourced
        pytest.skip('amr_week07 not installed')
    joints = {j.find('child').get('link'): j for j in ET.parse(urdf).getroot().iter('joint')}
    for parent, child, xyz, rpy in bc.SENSOR_FRAMES:
        j = joints[child]
        assert j.find('parent').get('link') == parent
        origin = j.find('origin')
        assert [float(v) for v in origin.get('xyz').split()] == pytest.approx(list(xyz))
        assert [float(v) for v in origin.get('rpy').split()] == pytest.approx(list(rpy),
                                                                              abs=1e-9)

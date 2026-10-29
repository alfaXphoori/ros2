"""Unit tests (no ROS graph): synthetic AprilTag rendering, PnP pose accuracy, colour detector."""
import math

import numpy as np
import pytest

from amr_adv02 import vision_utils as vu
from amr_adv02.object_detector_node import to_detection_array

K = vu.camera_matrix(525.0, 525.0, 319.5, 239.5)
TAG = 0.10


@pytest.mark.parametrize('t,yaw_deg', [
    ((0.10, 0.05, 0.80), 15.0),
    ((0.00, 0.05, 0.80), 20.0),
    ((-0.10, 0.02, 0.50), -30.0),
    ((0.05, -0.03, 0.40), 35.0),
    ((0.15, 0.00, 1.00), -25.0),
])
def test_pose_error_below_1cm_and_2deg(t, yaw_deg):
    R = vu.tag_rotation_in_camera(math.radians(yaw_deg))
    img = vu.render_tag(640, 480, K, R, np.array(t), TAG, tag_id=0)
    dets = vu.detect_tags(img)
    assert [d[0] for d in dets] == [0]
    R_est, t_est = vu.estimate_tag_pose(dets[0][1], TAG, K)
    assert np.linalg.norm(t_est - np.array(t)) < 0.01
    assert vu.rotation_angle_deg(R, R_est) < 2.0


def test_no_tag_no_detection():
    img = np.full((480, 640, 3), 90, np.uint8)
    vu.draw_scene_objects(img)
    assert vu.detect_tags(img) == []


def test_tag_behind_camera_is_not_drawn():
    bg = np.full((480, 640, 3), 90, np.uint8)
    img = vu.render_tag(640, 480, K, vu.tag_rotation_in_camera(0.0), np.array([0, 0, -1.0]), TAG,
                        background=bg)
    assert np.array_equal(img, bg)


def test_other_tag_id_is_reported_as_such():
    R = vu.tag_rotation_in_camera(0.3)
    img = vu.render_tag(640, 480, K, R, np.array([0.0, 0.0, 0.7]), TAG, tag_id=7)
    assert [d[0] for d in vu.detect_tags(img)] == [7]


def test_quaternion_round_trip():
    for yaw in (0.0, 0.4, -2.5, math.pi):
        R = vu.rot_z(0.3) @ vu.tag_rotation_in_camera(yaw)
        q = vu.rotation_to_quaternion(R)
        assert np.allclose(vu.quaternion_to_rotation(*q), R, atol=1e-9)
        assert abs(np.linalg.norm(q) - 1.0) < 1e-12


def test_color_detector_finds_scene_objects():
    img = np.full((480, 640, 3), 90, np.uint8)
    truth = vu.draw_scene_objects(img)
    dets = {d['class_id']: d for d in vu.color_detections(img)}
    assert set(dets) == {'safety_cone', 'pallet_cargo'}
    for name, (cx, cy, w, h) in truth.items():
        d = dets[name]
        assert abs(d['cx'] - cx) <= 3 and abs(d['cy'] - cy) <= 3
        assert abs(d['w'] - w) <= 4 and abs(d['h'] - h) <= 4
        assert 0.0 < d['score'] <= 1.0
    # a blank frame gives no detections (the old node returned two fake boxes for ANY frame)
    assert vu.color_detections(np.full((480, 640, 3), 90, np.uint8)) == []


def test_detection_array_conversion():
    from std_msgs.msg import Header
    h = Header(frame_id='camera_optical_link')
    h.stamp.sec, h.stamp.nanosec = 12, 345
    msg = to_detection_array(h, [{'class_id': 'pallet_cargo', 'score': 0.9, 'cx': 10.0,
                                  'cy': 20.0, 'w': 30.0, 'h': 40.0}])
    assert msg.header.stamp.sec == 12 and msg.header.stamp.nanosec == 345
    d = msg.detections[0]
    assert d.header.frame_id == 'camera_optical_link'
    assert (d.bbox.center.position.x, d.bbox.center.position.y) == (10.0, 20.0)
    assert (d.bbox.size_x, d.bbox.size_y) == (30.0, 40.0)
    assert d.results[0].hypothesis.class_id == 'pallet_cargo'
    assert d.results[0].hypothesis.score == pytest.approx(0.9)


def test_fronto_parallel_corners_give_finite_pose():
    # detected corners of a tag squarely facing the camera at 0.87 m: OpenCV 4.6 IPPE_SQUARE
    # returns NaN here, the old tracker then published a NaN pose and the docking server lost
    # its dock estimate
    corners = np.array([[292.73757935, 209.44433594], [353.19393921, 209.44290161],
                        [353.19393921, 269.55709839], [292.73757935, 269.55566406]])
    R, t = vu.estimate_tag_pose(corners, TAG, K)
    assert np.all(np.isfinite(R)) and np.all(np.isfinite(t))
    assert t[2] == pytest.approx(0.871, abs=0.005)
    assert vu.rotation_angle_deg(vu.tag_rotation_in_camera(0.0), R) < 2.0


def test_random_near_frontal_poses_always_solved():
    rng = np.random.default_rng(3)
    for _ in range(200):
        z = rng.uniform(0.2, 1.2)
        R = vu.tag_rotation_in_camera(math.radians(rng.uniform(-3, 3)))
        t = np.array([rng.uniform(-0.06, 0.06), 0.0, z])
        dets = vu.detect_tags(vu.render_tag(640, 480, K, R, t, TAG))
        est = vu.estimate_tag_pose(dets[0][1], TAG, K)
        assert est is not None and np.all(np.isfinite(est[0]))
        assert np.linalg.norm(est[1] - t) < 0.02

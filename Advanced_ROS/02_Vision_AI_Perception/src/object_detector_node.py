#!/usr/bin/env python3
"""
Advanced Module 02: object detection node -> vision_msgs/Detection2DArray.

  camera/image_raw (qos_profile_sensor_data) -> cv_bridge -> detector backend
      -> perception/detections  vision_msgs/Detection2DArray (header = image header)
      -> perception/debug_image sensor_msgs/Image with the boxes drawn (for rqt_image_view)

Backends (parameter `backend`):
  color (default) : CLASSICAL computer vision - HSV colour threshold + contours
                    (vision_utils.color_detections). Runs anywhere, CPU only, no model file.
                    It is NOT a neural network; `score` is a contour fill ratio, not a probability.
  yolo  (optional): Ultralytics YOLO (YOLOv8/YOLO11) - needs `pip install ultralytics` (PyTorch)
                    in a venv; not installed in the lab image. Model file via parameter `model`.

Run:  ros2 run amr_adv02 object_detector
      ros2 run amr_adv02 object_detector --ros-args -p backend:=yolo -p model:=yolov8n.pt
"""

import signal
import threading

import cv2
import rclpy
from cv_bridge import CvBridge, CvBridgeError
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from rclpy.signals import SignalHandlerOptions
from sensor_msgs.msg import Image
from vision_msgs.msg import Detection2D, Detection2DArray, ObjectHypothesisWithPose

try:
    from amr_adv02 import vision_utils as vu
except ImportError:  # python3 src/object_detector_node.py
    import vision_utils as vu


def to_detection_array(header, detections):
    """List of {class_id, score, cx, cy, w, h} -> vision_msgs/Detection2DArray."""
    out = Detection2DArray()
    out.header = header
    for d in detections:
        det = Detection2D()
        det.header = header
        det.bbox.center.position.x = float(d['cx'])
        det.bbox.center.position.y = float(d['cy'])
        det.bbox.size_x = float(d['w'])
        det.bbox.size_y = float(d['h'])
        hyp = ObjectHypothesisWithPose()
        hyp.hypothesis.class_id = str(d['class_id'])
        hyp.hypothesis.score = float(d['score'])
        det.results.append(hyp)
        out.detections.append(det)
    return out


class YoloBackend:
    """Optional Ultralytics backend (exercise). Imported lazily so the node runs without it."""

    def __init__(self, model_path, conf):
        from ultralytics import YOLO  # pip install ultralytics (not in the lab image)
        self.model = YOLO(model_path)
        self.conf = conf

    def __call__(self, bgr):
        result = self.model(bgr, conf=self.conf, verbose=False)[0]
        dets = []
        for box in result.boxes:
            cx, cy, w, h = (float(v) for v in box.xywh[0].tolist())
            dets.append({'class_id': result.names[int(box.cls)], 'score': float(box.conf),
                         'cx': cx, 'cy': cy, 'w': w, 'h': h})
        return dets


class ObjectDetectorNode(Node):
    def __init__(self):
        super().__init__('object_detector')
        self.backend_name = self.declare_parameter('backend', 'color').value
        self.min_area = self.declare_parameter('min_area', 150).value
        model = self.declare_parameter('model', 'yolov8n.pt').value
        conf = self.declare_parameter('confidence', 0.5).value
        self.bridge = CvBridge()

        if self.backend_name == 'yolo':
            try:
                self.backend = YoloBackend(model, conf)
            except ImportError:
                raise SystemExit('backend:=yolo needs Ultralytics: python3 -m venv --system-site-'
                                 'packages ~/yolo && ~/yolo/bin/pip install ultralytics')
            label = f'Ultralytics YOLO ({model})'
        else:
            self.backend = lambda bgr: vu.color_detections(bgr, min_area=self.min_area)
            label = 'classical HSV colour + contour detector (no neural network)'

        self.create_subscription(Image, 'camera/image_raw', self.image_callback,
                                 qos_profile_sensor_data)
        self.pub_det = self.create_publisher(Detection2DArray, 'perception/detections', 10)
        self.pub_debug = self.create_publisher(Image, 'perception/debug_image',
                                               qos_profile_sensor_data)
        self.get_logger().info(f'Object detector ready: {label}')

    def image_callback(self, msg: Image):
        try:
            bgr = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
        except CvBridgeError as e:
            self.get_logger().error(f'cv_bridge conversion error: {e}')
            return
        dets = self.backend(bgr)
        self.pub_det.publish(to_detection_array(msg.header, dets))
        self.get_logger().info(
            f'{len(dets)} detections: ' + ', '.join(f"{d['class_id']}({d['score']:.2f})"
                                                    for d in dets),
            throttle_duration_sec=2.0)
        if self.pub_debug.get_subscription_count() > 0:
            for d in dets:
                p0 = (int(d['cx'] - d['w'] / 2), int(d['cy'] - d['h'] / 2))
                p1 = (int(d['cx'] + d['w'] / 2), int(d['cy'] + d['h'] / 2))
                cv2.rectangle(bgr, p0, p1, (0, 255, 0), 2)
                cv2.putText(bgr, d['class_id'], (p0[0], max(12, p0[1] - 4)),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
            dbg = self.bridge.cv2_to_imgmsg(bgr, encoding='bgr8')
            dbg.header = msg.header
            self.pub_debug.publish(dbg)


def main(args=None):
    # SIGINT/SIGTERM only set a flag that the loop checks between spin_once() calls. With
    # rclpy's own handler the context could be shut down while a message was being taken
    # (RuntimeError in take_message -> exit code 1 at the end of a launch test).
    rclpy.init(args=args, signal_handler_options=SignalHandlerOptions.NO)
    stop = threading.Event()
    for sig in (signal.SIGINT, signal.SIGTERM):
        signal.signal(sig, lambda *_: stop.set())
    node = None
    try:
        node = ObjectDetectorNode()
        while not stop.is_set() and rclpy.ok():
            rclpy.spin_once(node, timeout_sec=0.1)
    except ExternalShutdownException:
        pass
    finally:
        # stopping: ignore further signals (Python resets our handler at exit -> 2nd Ctrl+C = -2)
        for sig in (signal.SIGINT, signal.SIGTERM):
            signal.signal(sig, signal.SIG_IGN)
        if node is not None:
            node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()

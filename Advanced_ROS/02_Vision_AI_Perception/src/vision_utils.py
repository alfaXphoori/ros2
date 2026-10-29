#!/usr/bin/env python3
"""
Advanced Module 02: pure OpenCV/NumPy helpers (no ROS) used by the vision nodes and tests.

* render_tag()          draw an AprilTag 36h11 into a pinhole-camera image at a known pose
* detect_tags()         cv2.aruco detection of AprilTag 36h11 markers (OpenCV 4.6 .. 4.10+ API)
* estimate_tag_pose()   cv2.solvePnP(SOLVEPNP_IPPE_SQUARE) -> R, t of the tag in the camera frame
* color_detections()    classical colour/contour object detector (NOT a neural network)

Frames: the camera frame is the optical frame (x right, y down, z forward). The tag frame
follows OpenCV/ArUco: origin at the tag centre, x right, y up, z out of the tag face.
"""

import math

import cv2
import numpy as np

TAG_FAMILY = cv2.aruco.DICT_APRILTAG_36h11

# Tag frame -> camera optical frame for a tag that squarely faces the camera:
# x_tag = x_cam, y_tag = -y_cam (up), z_tag = -z_cam (towards the camera).
R_FACING = np.diag([1.0, -1.0, -1.0])


# ---------------------------------------------------------------- rotations
def rot_x(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[1, 0, 0], [0, c, -s], [0, s, c]], dtype=float)


def rot_y(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]], dtype=float)


def rot_z(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]], dtype=float)


def tag_rotation_in_camera(yaw):
    """Tag facing the camera, turned by `yaw` rad about the camera's vertical (optical y) axis."""
    return rot_y(yaw) @ R_FACING


def rotation_to_quaternion(R):
    """3x3 rotation matrix -> (x, y, z, w)."""
    R = np.asarray(R, dtype=float)
    tr = R[0, 0] + R[1, 1] + R[2, 2]
    if tr > 0.0:
        s = math.sqrt(tr + 1.0) * 2.0
        w = 0.25 * s
        x = (R[2, 1] - R[1, 2]) / s
        y = (R[0, 2] - R[2, 0]) / s
        z = (R[1, 0] - R[0, 1]) / s
    elif R[0, 0] > R[1, 1] and R[0, 0] > R[2, 2]:
        s = math.sqrt(1.0 + R[0, 0] - R[1, 1] - R[2, 2]) * 2.0
        w = (R[2, 1] - R[1, 2]) / s
        x = 0.25 * s
        y = (R[0, 1] + R[1, 0]) / s
        z = (R[0, 2] + R[2, 0]) / s
    elif R[1, 1] > R[2, 2]:
        s = math.sqrt(1.0 + R[1, 1] - R[0, 0] - R[2, 2]) * 2.0
        w = (R[0, 2] - R[2, 0]) / s
        x = (R[0, 1] + R[1, 0]) / s
        y = 0.25 * s
        z = (R[1, 2] + R[2, 1]) / s
    else:
        s = math.sqrt(1.0 + R[2, 2] - R[0, 0] - R[1, 1]) * 2.0
        w = (R[1, 0] - R[0, 1]) / s
        x = (R[0, 2] + R[2, 0]) / s
        y = (R[1, 2] + R[2, 1]) / s
        z = 0.25 * s
    q = np.array([x, y, z, w])
    q /= np.linalg.norm(q)
    if q[3] < 0.0:  # canonical form (w >= 0)
        q = -q
    return tuple(float(v) for v in q)


def quaternion_to_rotation(x, y, z, w):
    n = math.sqrt(x * x + y * y + z * z + w * w)
    x, y, z, w = x / n, y / n, z / n, w / n
    return np.array([
        [1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
        [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
        [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)],
    ])


def rotation_angle_deg(R_a, R_b):
    """Angle (deg) of the relative rotation R_a^T R_b."""
    R = np.asarray(R_a).T @ np.asarray(R_b)
    c = max(-1.0, min(1.0, (np.trace(R) - 1.0) / 2.0))
    return math.degrees(math.acos(c))


# ---------------------------------------------------------------- camera
def camera_matrix(fx, fy, cx, cy):
    return np.array([[fx, 0.0, cx], [0.0, fy, cy], [0.0, 0.0, 1.0]], dtype=float)


def tag_object_points(tag_size):
    """Tag corners in the tag frame, in ArUco order: top-left, top-right, bottom-right, bottom-left."""
    h = tag_size / 2.0
    return np.array([[-h, h, 0.0], [h, h, 0.0], [h, -h, 0.0], [-h, -h, 0.0]], dtype=np.float64)


def project_points(points, R, t, K):
    """Project Nx3 points given in the tag frame to pixels. Returns Nx2 and the depths."""
    pc = (np.asarray(R) @ np.asarray(points, dtype=float).T).T + np.asarray(t, dtype=float)
    uvw = (np.asarray(K) @ pc.T).T
    return uvw[:, :2] / uvw[:, 2:3], pc[:, 2]


# ---------------------------------------------------------------- tags
def aruco_dictionary():
    return cv2.aruco.getPredefinedDictionary(TAG_FAMILY)


def marker_image(tag_id, side_px):
    """Black/white AprilTag 36h11 image (side_px x side_px) incl. its black border."""
    d = aruco_dictionary()
    if hasattr(cv2.aruco, 'generateImageMarker'):  # OpenCV >= 4.7
        return cv2.aruco.generateImageMarker(d, int(tag_id), int(side_px), borderBits=1)
    return cv2.aruco.drawMarker(d, int(tag_id), int(side_px), borderBits=1)


def render_tag(width, height, K, R, t, tag_size, tag_id=0, background=None,
               margin=0.25, supersample=2):
    """Render a tag (with a white quiet zone of `margin` x tag_size) into a BGR image.

    R, t: pose of the tag frame in the camera optical frame. If the tag is not in front of the
    camera the background is returned unchanged.
    """
    if background is None:
        img = np.full((height, width, 3), 90, dtype=np.uint8)
    else:
        img = background.copy()
    s = int(supersample)
    board_m = tag_size * (1.0 + 2.0 * margin)          # board side in metres
    h = board_m / 2.0
    corners_3d = np.array([[-h, h, 0.0], [h, h, 0.0], [h, -h, 0.0], [-h, -h, 0.0]])
    uv, depth = project_points(corners_3d, R, t, K)
    if np.any(depth <= 0.05):
        return img
    dst = ((uv + 0.5) * s - 0.5).astype(np.float32)
    # Texture resolution close to the projected size: strong minification with INTER_LINEAR
    # aliases the cell edges and biases the detected corners.
    edge = max(np.linalg.norm(dst[i] - dst[(i + 1) % 4]) for i in range(4))
    cell = int(np.clip(np.ceil(edge / (1.0 + 2.0 * margin) / 8.0), 2, 40))
    tag_px = 8 * cell                                   # 8 cells (6 data + 2 border)
    off = int(round(tag_px * margin))
    board_px = tag_px + 2 * off
    board = np.full((board_px, board_px), 255, dtype=np.uint8)
    board[off:off + tag_px, off:off + tag_px] = marker_image(tag_id, tag_px)
    # the quiet zone is rounded to whole pixels: map the TAG corners (not the board) exactly
    tag_uv, _ = project_points(tag_object_points(tag_size), R, t, K)
    dst = ((tag_uv + 0.5) * s - 0.5).astype(np.float32)
    # board pixel i covers [i - 0.5, i + 0.5]: tag edges are at off - 0.5 and off + tag_px - 0.5
    src = np.array([[off, off], [off + tag_px, off], [off + tag_px, off + tag_px],
                    [off, off + tag_px]], dtype=np.float32) - 0.5
    H = cv2.getPerspectiveTransform(src, dst)
    big_w, big_h = width * s, height * s
    warped = cv2.warpPerspective(board, H, (big_w, big_h), flags=cv2.INTER_LINEAR,
                                 borderMode=cv2.BORDER_CONSTANT, borderValue=0)
    mask = cv2.warpPerspective(np.full_like(board, 255), H, (big_w, big_h),
                               flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT,
                               borderValue=0)
    warped = cv2.resize(warped, (width, height), interpolation=cv2.INTER_AREA).astype(float)
    alpha = cv2.resize(mask, (width, height), interpolation=cv2.INTER_AREA).astype(float) / 255.0
    out = img.astype(float) * (1.0 - alpha[..., None]) + warped[..., None] * alpha[..., None]
    return np.clip(out + 0.5, 0, 255).astype(np.uint8)


def detect_tags(image):
    """Detect AprilTag 36h11 markers. Returns a list of (tag_id, corners 4x2 float32)."""
    gray = image if image.ndim == 2 else cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    d = aruco_dictionary()
    if hasattr(cv2.aruco, 'ArucoDetector'):  # OpenCV >= 4.7
        params = cv2.aruco.DetectorParameters()
        params.cornerRefinementMethod = cv2.aruco.CORNER_REFINE_SUBPIX
        corners, ids, _ = cv2.aruco.ArucoDetector(d, params).detectMarkers(gray)
    else:
        params = cv2.aruco.DetectorParameters_create()
        params.cornerRefinementMethod = cv2.aruco.CORNER_REFINE_SUBPIX
        corners, ids, _ = cv2.aruco.detectMarkers(gray, d, parameters=params)
    if ids is None:
        return []
    return [(int(i), c.reshape(4, 2).astype(np.float32)) for i, c in zip(ids.flatten(), corners)]


def reprojection_error(corners, tag_size, K, D, rvec, tvec):
    proj, _ = cv2.projectPoints(tag_object_points(tag_size), rvec, tvec, K, D)
    return float(np.abs(proj.reshape(4, 2) - np.asarray(corners).reshape(4, 2)).max())


def estimate_tag_pose(corners, tag_size, K, D=None, max_reproj_px=2.0):
    """solvePnP with the IPPE_SQUARE solver (made for square markers) + LM refinement.

    Both IPPE solutions are checked by their reprojection error: with OpenCV 4.6, IPPE_SQUARE
    sometimes returns a 180-deg-flipped rotation or NaN for nearly fronto-parallel tags, so the
    generic planar IPPE and SQPNP solvers are fallbacks. Returns (R 3x3, t 3) of the tag frame
    in the camera frame, or None if no solution reprojects within `max_reproj_px` pixels.
    """
    D = np.zeros(5) if D is None or len(D) == 0 else np.asarray(D, dtype=float)
    K = np.asarray(K, dtype=float)
    img = np.asarray(corners, dtype=np.float64).reshape(4, 1, 2)
    obj = tag_object_points(tag_size)
    best = None
    for flag in (cv2.SOLVEPNP_IPPE_SQUARE, cv2.SOLVEPNP_IPPE, cv2.SOLVEPNP_SQPNP):
        n, rvecs, tvecs, _ = cv2.solvePnPGeneric(obj, img, K, D, flags=flag)
        for rvec, tvec in zip(rvecs[:n], tvecs[:n]):
            if tvec.flatten()[2] <= 0.0:
                continue
            rvec, tvec = cv2.solvePnPRefineLM(obj, img, K, D, rvec.copy(), tvec.copy())
            if not (np.all(np.isfinite(rvec)) and np.all(np.isfinite(tvec))):
                continue  # degenerate solution (seen with OpenCV 4.6 IPPE_SQUARE)
            err = reprojection_error(img, tag_size, K, D, rvec, tvec)
            if not np.isfinite(err):
                continue
            if best is None or err < best[0]:
                best = (err, rvec, tvec)
        if best is not None and best[0] <= max_reproj_px:
            break
    if best is None or best[0] > max_reproj_px:
        return None
    R, _ = cv2.Rodrigues(best[1])
    return R, best[2].flatten()


# ---------------------------------------------------------------- classical detector
# HSV ranges (OpenCV: H 0..179). Classes of the synthetic warehouse scene.
DEFAULT_COLOR_CLASSES = {
    'safety_cone': [((5, 120, 120), (20, 255, 255))],      # orange
    'pallet_cargo': [((100, 120, 60), (130, 255, 255))],   # blue
}


def color_detections(bgr, classes=None, min_area=150):
    """Classical colour-threshold + contour detector.

    Returns a list of dicts {class_id, score, cx, cy, w, h}. `score` is the contour fill ratio
    (contour area / box area): a shape-quality heuristic, NOT a calibrated probability.
    """
    classes = DEFAULT_COLOR_CLASSES if classes is None else classes
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    out = []
    for name, ranges in classes.items():
        mask = np.zeros(hsv.shape[:2], dtype=np.uint8)
        for lo, hi in ranges:
            mask |= cv2.inRange(hsv, np.array(lo, dtype=np.uint8), np.array(hi, dtype=np.uint8))
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for c in contours:
            area = cv2.contourArea(c)
            if area < min_area:
                continue
            x, y, w, h = cv2.boundingRect(c)
            out.append({'class_id': name, 'score': float(min(1.0, area / float(w * h))),
                        'cx': x + w / 2.0, 'cy': y + h / 2.0, 'w': float(w), 'h': float(h)})
    out.sort(key=lambda d: (d['class_id'], d['cx']))
    return out


def draw_scene_objects(img):
    """Paint the synthetic scene objects (an orange cone, a blue pallet) into a BGR image.

    Returns the ground-truth boxes as {class_id: (cx, cy, w, h)} in pixels.
    """
    h, w = img.shape[:2]
    # orange safety cone (triangle) at the lower left
    base_y = int(0.92 * h)
    cone = np.array([[int(0.10 * w), base_y], [int(0.20 * w), base_y], [int(0.15 * w), int(0.62 * h)]],
                    dtype=np.int32)
    cv2.fillConvexPoly(img, cone, (0, 120, 255))
    # blue pallet (rectangle) at the lower right
    x0, y0, x1, y1 = int(0.68 * w), int(0.70 * h), int(0.94 * w), int(0.90 * h)
    cv2.rectangle(img, (x0, y0), (x1 - 1, y1 - 1), (200, 60, 20), thickness=-1)
    cx_cone = (cone[0, 0] + cone[1, 0]) / 2.0
    return {
        'safety_cone': (cx_cone, (cone[2, 1] + base_y + 1) / 2.0,
                        float(cone[1, 0] - cone[0, 0] + 1), float(base_y - cone[2, 1] + 1)),
        'pallet_cargo': ((x0 + x1) / 2.0, (y0 + y1) / 2.0, float(x1 - x0), float(y1 - y0)),
    }

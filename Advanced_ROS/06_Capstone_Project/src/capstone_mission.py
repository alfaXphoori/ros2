#!/usr/bin/env python3
"""
Advanced Module 06: capstone mission executor that MEASURES the KPIs against Gazebo ground truth.

  ros2 launch amr_adv06 full_warehouse_system.launch.py headless:=true      # terminal 1
  ros2 run amr_adv06 capstone_mission --ros-args -p use_sim_time:=true      # terminal 2
      optional: -p path_csv:=/tmp/capstone_path.csv  -p estop_test:=false  -p dwell_scale:=0.5

Stages (definitions in config/capstone_mission.yaml, KPI targets in config/kpi_targets.yaml):
  0. System bringup : AMCL initial pose at Home, Nav2 active, every lifecycle node ACTIVE
                      (Nav2 servers + docking_server), ground truth available
  1. Pick Station A : NavigateToPose, dwell (load)
  2. Drop Station B : NavigateToPose, dwell (unload)
  3. Dock           : nav2_msgs/DockRobot (navigate to staging -> AprilTag detection ->
                      graceful controller) -> docking error from ground truth vs the TRUE dock
  4. Undock         : nav2_msgs/UndockRobot -> robot back at the staging area
  5. E-stop test    : drive home; at >= trigger speed a box is spawned in Gazebo inside the
                      collision_monitor StopZone -> measure LiDAR-detection -> cmd_vel = 0
                      latency and the remaining bumper gap (no contact = PASS); box removed
  6. Return Home    : NavigateToPose

Every stage logs result, duration (sim time) and errors; a final KPI table compares the measured
values with the passing targets. Exit code 0 only if every stage PASSED and every KPI met its
passing target, otherwise 1.
"""

import math
import sys
import threading
import time

from geometry_msgs.msg import PoseStamped, Twist
from lifecycle_msgs.msg import Transition
from lifecycle_msgs.srv import ChangeState, GetState
from nav2_simple_commander.robot_navigator import BasicNavigator, TaskResult
from nav_msgs.msg import Odometry
import rclpy
from rclpy.executors import ExternalShutdownException, SingleThreadedExecutor
from rclpy.node import Node
from rclpy.parameter import Parameter
from rclpy.qos import qos_profile_sensor_data
from rclpy.time import Time
from sensor_msgs.msg import LaserScan
from tf2_ros import Buffer, TransformException, TransformListener

try:
    from amr_adv06 import capstone_config as cc
except ImportError:  # python3 src/capstone_mission.py
    import capstone_config as cc

LIFECYCLE_NODES = ['map_server', 'amcl', 'controller_server', 'smoother_server',
                   'planner_server', 'behavior_server', 'velocity_smoother', 'collision_monitor',
                   'bt_navigator', 'waypoint_follower', 'docking_server']
# nodes nothing else waits for -> healed first (navigation servers get twice the time)
EARLY_HEAL = ('map_server', 'amcl', 'docking_server')
DOCK_STATES = {0: 'NONE', 1: 'NAV_TO_STAGING_POSE', 2: 'INITIAL_PERCEPTION', 3: 'CONTROLLING',
               4: 'WAIT_FOR_CHARGE', 5: 'RETRY'}
DOCK_ERRORS = {0: 'NONE', 901: 'DOCK_NOT_IN_DB', 902: 'DOCK_NOT_VALID', 903: 'FAILED_TO_STAGE',
               904: 'FAILED_TO_DETECT_DOCK', 905: 'FAILED_TO_CONTROL', 906: 'FAILED_TO_CHARGE',
               999: 'UNKNOWN'}
LIDAR_X = 0.08        # base_footprint -> lidar_link x offset (Week 07 URDF)
STOP_ZONE_FAR = 0.40  # far edge of the collision_monitor StopZone (config/nav2_overrides.yaml)


def front_min_range(scan, half_angle=math.radians(30.0)):
    """Closest valid range within +-half_angle of the LiDAR x axis (inf if none)."""
    best = math.inf
    for i, r in enumerate(scan.ranges):
        a = scan.angle_min + i * scan.angle_increment
        a = math.atan2(math.sin(a), math.cos(a))
        if abs(a) <= half_angle and scan.range_min <= r <= scan.range_max and r < best:
            best = r
    return best


def evaluate(stages, kpis):
    """stages: [{'name', 'ok'}], kpis: [{'verdict'}] -> (n_ok, n_kpi_ok, 'PASS'|'FAIL')."""
    n_ok = sum(1 for s in stages if s['ok'])
    n_kpi = sum(1 for k in kpis if k['verdict'] == 'PASS')
    ok = bool(stages) and n_ok == len(stages) and all(k['verdict'] != 'FAIL' for k in kpis)
    return n_ok, n_kpi, 'PASS' if ok else 'FAIL'


class Monitor(Node):
    """Background node (own executor thread): ground truth, AMCL pose, odom speed, path log
    and the e-stop latency probe. Callbacks run continuously, so the wall-clock receive times
    used for the latency are not delayed by the mission's blocking action calls."""

    def __init__(self, use_sim_time, path_csv=''):
        super().__init__('capstone_monitor',
                         parameter_overrides=[Parameter('use_sim_time', value=use_sim_time)])
        self.lock = threading.Lock()
        self.gt = None          # (x, y, yaw) true pose in the Gazebo world
        self.speed = 0.0
        self.stage = 'bringup'
        self.tf_buffer = Buffer()
        self.tf_listener = TransformListener(self.tf_buffer, self, spin_thread=False)
        self.probe = None
        self.create_subscription(PoseStamped, 'ground_truth/pose', self.on_gt, 10)
        self.create_subscription(Odometry, 'odom', self.on_odom, 10)
        self.create_subscription(LaserScan, 'scan', self.on_scan, qos_profile_sensor_data)
        self.create_subscription(Twist, 'cmd_vel', self.on_cmd, 10)
        self.csv = None
        if path_csv:
            self.csv = open(path_csv, 'w')
            self.csv.write('t,stage,gt_x,gt_y,gt_yaw,amcl_x,amcl_y,amcl_yaw\n')
            self.create_timer(0.2, self.log_path)

    # ---- data ----
    def now_s(self):
        return self.get_clock().now().nanoseconds * 1e-9

    def on_gt(self, msg):
        q = msg.pose.orientation
        with self.lock:
            self.gt = (msg.pose.position.x, msg.pose.position.y,
                       cc.yaw_from_quaternion(q.x, q.y, q.z, q.w))

    def on_odom(self, msg):
        self.speed = msg.twist.twist.linear.x

    def gt_pose(self):
        with self.lock:
            return self.gt

    def amcl_pose(self):
        try:
            t = self.tf_buffer.lookup_transform('map', 'base_footprint', Time())
        except TransformException:
            return None
        q = t.transform.rotation
        return (t.transform.translation.x, t.transform.translation.y,
                cc.yaw_from_quaternion(q.x, q.y, q.z, q.w))

    def log_path(self):
        gt, am = self.gt_pose(), self.amcl_pose()
        if gt is None or am is None or self.csv is None:
            return
        self.csv.write(f'{self.now_s():.2f},{self.stage},{gt[0]:.4f},{gt[1]:.4f},{gt[2]:.4f},'
                       f'{am[0]:.4f},{am[1]:.4f},{am[2]:.4f}\n')
        self.csv.flush()

    # ---- e-stop probe ----
    def arm_probe(self, scan_threshold):
        with self.lock:
            self.probe = {'threshold': scan_threshold, 't_arm': time.monotonic(),
                          'scan_wall': None, 'scan_stamp': None, 'scan_range': None,
                          'stop_wall': None, 'stop_sim': None}

    def probe_result(self):
        with self.lock:
            return dict(self.probe) if self.probe else None

    def on_scan(self, msg):
        p = self.probe
        if p is None or p['scan_wall'] is not None:
            return
        r = front_min_range(msg)
        if r < p['threshold']:
            with self.lock:
                p['scan_wall'] = time.monotonic()
                p['scan_stamp'] = Time.from_msg(msg.header.stamp).nanoseconds * 1e-9
                p['scan_range'] = r

    def on_cmd(self, msg):
        p = self.probe
        if p is None or p['stop_wall'] is not None:
            return
        if msg.linear.x == 0.0 and msg.angular.z == 0.0:
            with self.lock:
                p['stop_wall'] = time.monotonic()
                p['stop_sim'] = self.now_s()


class Gazebo:
    """Minimal Gazebo transport client: spawn / remove the fault-injection obstacle."""

    def __init__(self, world='warehouse'):
        from gz.transport13 import Node as GzNode
        self.node = GzNode()
        self.world = world

    def spawn_box(self, name, x, y, yaw, size):
        from gz.msgs10.boolean_pb2 import Boolean
        from gz.msgs10.entity_factory_pb2 import EntityFactory
        sx, sy, sz = size
        box = f'<box><size>{sx} {sy} {sz}</size></box>'
        req = EntityFactory()
        req.sdf = (f'<sdf version="1.9"><model name="{name}"><static>true</static>'
                   f'<link name="link"><collision name="c"><geometry>{box}</geometry></collision>'
                   f'<visual name="v"><geometry>{box}</geometry><material>'
                   f'<diffuse>1 0.4 0 1</diffuse></material></visual></link></model></sdf>')
        req.name = name
        req.pose.position.x, req.pose.position.y, req.pose.position.z = x, y, sz / 2.0
        req.pose.orientation.z, req.pose.orientation.w = math.sin(yaw / 2), math.cos(yaw / 2)
        ok, rep = self.node.request(f'/world/{self.world}/create', req, EntityFactory, Boolean,
                                    3000)
        return ok and rep.data

    def remove(self, name):
        from gz.msgs10.boolean_pb2 import Boolean
        from gz.msgs10.entity_pb2 import Entity
        req = Entity()
        req.name = name
        req.type = Entity.MODEL
        ok, rep = self.node.request(f'/world/{self.world}/remove', req, Entity, Boolean, 3000)
        return ok and rep.data


def make_pose(nav, x, y, yaw_deg):
    pose = PoseStamped()
    pose.header.frame_id = 'map'
    pose.header.stamp = nav.get_clock().now().to_msg()
    pose.pose.position.x, pose.pose.position.y = float(x), float(y)
    rad = math.radians(yaw_deg)
    pose.pose.orientation.z, pose.pose.orientation.w = math.sin(rad / 2), math.cos(rad / 2)
    return pose


class CapstoneMission:
    def __init__(self, nav, mon):
        self.nav, self.mon = nav, mon
        self.log = nav.get_logger()
        p = nav.declare_parameter
        self.dwell_scale = p('dwell_scale', 1.0).value
        self.timeout = p('stage_timeout', 150.0).value
        self.estop_enabled = p('estop_test', True).value
        self.bringup_timeout = p('bringup_timeout', 120.0).value
        self.heal_after = p('heal_after', 25.0).value
        self.healed = []
        self.mission = cc.load_mission(p('mission', '').value or None)
        self.targets = cc.load_kpis(p('kpi_file', '').value or None)['kpis']
        self.stages, self.nav_errors, self.amcl_errors = [], [], []
        self.measured = {}

    # ---- helpers ----
    def report(self, ok, text):
        # rclpy pins one severity per call site, so info and error need separate calls
        if ok:
            self.log.info(text)
        else:
            self.log.error(text)

    def wait(self, seconds):
        end = self.mon.now_s() + seconds
        while self.mon.now_s() < end:
            time.sleep(0.05)

    def stage(self, name, ok, t0, detail):
        dt = self.mon.now_s() - t0
        self.stages.append({'name': name, 'ok': ok, 'time': dt})
        self.report(ok, f"Stage {len(self.stages) - 1} {name}: {'PASS' if ok else 'FAIL'} "
                    f'in {dt:.1f} s (sim) | {detail}')
        return ok

    def run_task(self, timeout):
        """Spin the current Nav2 task to completion; returns (TaskResult, last feedback)."""
        t0, last, canceled = self.mon.now_s(), None, False
        while not self.nav.isTaskComplete():
            fb = self.nav.getFeedback()
            if fb is not None:
                last = fb
                self.on_feedback(fb)
            if not canceled and self.mon.now_s() - t0 > timeout:
                self.log.error(f'no result after {timeout:.0f} s, canceling')
                self.nav.cancelTask()
                canceled = True
        return self.nav.getResult(), last

    def on_feedback(self, fb):
        if hasattr(fb, 'state') and fb.state != getattr(self, 'dock_state', None):
            self.dock_state = fb.state
            self.log.info(f'  docking feedback: {DOCK_STATES.get(fb.state, fb.state)} '
                          f'(retries {fb.num_retries})')

    def errors_at(self, x, y, yaw):
        gt, am = self.mon.gt_pose(), self.mon.amcl_pose()
        pos = math.hypot(gt[0] - x, gt[1] - y)
        yaw_err = math.degrees(math.atan2(math.sin(gt[2] - yaw), math.cos(gt[2] - yaw)))
        amcl = math.hypot(am[0] - gt[0], am[1] - gt[1]) if am else float('nan')
        return gt, pos, yaw_err, amcl

    # ---- stages ----
    def bringup(self):
        end = time.monotonic() + 60.0
        while self.mon.now_s() <= 0.0 and time.monotonic() < end:  # wait for /clock
            time.sleep(0.1)
        t0 = self.mon.now_s()
        home = self.mission['home']
        self.log.info(f"Stage 0 System bringup: waiting for {len(LIFECYCLE_NODES)} lifecycle "
                      f"nodes, initial pose at {home['name']} ({home['x']:.2f}, {home['y']:.2f})")
        states = self.lifecycle_supervisor(timeout=self.bringup_timeout)
        active = [n for n, s in states.items() if s == 'active']
        if len(active) == len(LIFECYCLE_NODES):
            self.nav.setInitialPose(make_pose(self.nav, home['x'], home['y'], home['yaw_deg']))
            self.nav.waitUntilNav2Active(localizer='amcl')
        end = time.monotonic() + 20.0
        while self.mon.gt_pose() is None and time.monotonic() < end:
            time.sleep(0.1)
        gt = self.mon.gt_pose()
        ok = len(active) == len(LIFECYCLE_NODES) and gt is not None
        missing = [f'{n}={s}' for n, s in states.items() if s != 'active']
        detail = f'{len(active)}/{len(LIFECYCLE_NODES)} lifecycle nodes ACTIVE'
        if missing:
            detail += f' (not active: {", ".join(missing)})'
        if self.healed:
            detail += f' (supervisor drove: {", ".join(self.healed)})'
        detail += f', ground truth x={gt[0]:.3f} y={gt[1]:.3f}' if gt else ', NO ground truth'
        return self.stage('System bringup', ok, t0, detail)

    def call(self, client, request, timeout=5.0):
        fut = client.call_async(request)
        rclpy.spin_until_future_complete(self.nav, fut, timeout_sec=timeout)
        return fut.result()

    def lifecycle_supervisor(self, timeout):
        """Poll lifecycle_msgs/GetState of every managed node until all are ACTIVE (or timeout).

        Watchdog: a nav2 lifecycle_manager sends each transition request ONCE, right after the
        node's service appears, and then waits for the reply without a timeout. Observed in
        real runs: the node executed the transition ("Configuring" in its log) but the reply
        never reached the manager (lost while DDS discovery was still matching the endpoints),
        so the manager - and with it the whole bringup - hung. A node still in a stable
        non-active state after `heal_after` seconds is therefore driven by the supervisor
        itself (configure/activate via lifecycle_msgs/ChangeState), logged as WARN. Navigation
        servers get extra time because their manager activates them one after another and
        planner_server legitimately waits for the map -> odom TF of AMCL."""
        get = {n: self.nav.create_client(GetState, f'/{n}/get_state') for n in LIFECYCLE_NODES}
        change = {n: self.nav.create_client(ChangeState, f'/{n}/change_state')
                  for n in LIFECYCLE_NODES}
        states = {n: 'unavailable' for n in LIFECYCLE_NODES}
        start = time.monotonic()
        while time.monotonic() - start < timeout:
            for n, cli in get.items():
                if states[n] == 'active' or not cli.wait_for_service(timeout_sec=0.5):
                    continue
                res = self.call(cli, GetState.Request(), 2.0)
                if res is not None:
                    states[n] = res.current_state.label
            if all(s == 'active' for s in states.values()):
                break
            waited = time.monotonic() - start
            for n, s in states.items():
                limit = self.heal_after * (1.0 if n in EARLY_HEAL else 2.0)
                if s in ('unconfigured', 'inactive') and waited > limit and n not in self.healed:
                    self.healed.append(n)
                    self.log.warn(f'supervisor: {n} still {s} after {waited:.0f} s -> '
                                  f'sending its lifecycle transitions directly')
                    steps = ([Transition.TRANSITION_CONFIGURE] if s == 'unconfigured' else [])
                    for t in steps + [Transition.TRANSITION_ACTIVATE]:
                        req = ChangeState.Request()
                        req.transition.id = t
                        res = self.call(change[n], req, 20.0)
                        self.log.warn(f"supervisor: {n} {'configure' if t == 1 else 'activate'}"
                                      f" -> {res.success if res else 'no reply'}")
                    break  # re-poll before touching the next node
            time.sleep(0.5)
        for cli in list(get.values()) + list(change.values()):
            self.nav.destroy_client(cli)
        return states

    def navigate(self, wp):
        self.mon.stage = wp['name']
        t0 = self.mon.now_s()
        self.log.info(f"Stage {len(self.stages)} -> {wp['name']} (x={wp['x']:.2f}, "
                      f"y={wp['y']:.2f}, yaw={wp['yaw_deg']:.0f} deg)")
        self.nav.feedback = None
        if not self.nav.goToPose(make_pose(self.nav, wp['x'], wp['y'], wp['yaw_deg'])):
            return self.stage(wp['name'], False, t0, 'goal rejected')
        result, _ = self.run_task(self.timeout)
        self.wait(0.5)  # let the robot settle before measuring
        gt, pos, yaw_err, amcl = self.errors_at(wp['x'], wp['y'], math.radians(wp['yaw_deg']))
        ok = result == TaskResult.SUCCEEDED
        if ok:
            self.nav_errors.append(pos)
            self.amcl_errors.append(amcl)
        detail = (f'{result.name}, true final error {pos:.3f} m / {yaw_err:+.1f} deg, '
                  f'AMCL error {amcl:.3f} m')
        ok = self.stage(wp['name'], ok, t0, detail)
        if ok and wp.get('dwell'):
            self.wait(wp['dwell'] * self.dwell_scale)
        return ok

    def dock(self):
        d = self.mission['dock']
        self.mon.stage = 'dock'
        t0 = self.mon.now_s()
        true_dock = cc.dock_pose(d)
        sx, sy, _ = cc.staging_pose(d)
        self.log.info(f"Stage {len(self.stages)} -> DockRobot dock_id={d['id']} (true dock "
                      f"x={true_dock[0]:.2f} y={true_dock[1]:.2f} "
                      f"yaw={d['yaw_deg']:.0f} deg, staging x={sx:.2f} y={sy:.2f})")
        self.nav.feedback, self.dock_state = None, None
        if not self.nav.dockRobotByID(d['id'], nav_to_dock=True):
            return self.stage('Dock', False, t0, 'goal rejected')
        result, _ = self.run_task(self.timeout)
        res = self.nav.result_future.result().result if self.nav.result_future else None
        code = res.error_code if res else 999
        self.wait(1.0)
        gt = self.mon.gt_pose()
        err, lat, lon, eyaw = cc.pose_error(gt, true_dock)
        ok = result == TaskResult.SUCCEEDED and res is not None and res.success
        if ok:
            self.measured['docking_error_mm'] = err * 1000.0
            self.measured['docking_yaw_error_deg'] = abs(math.degrees(eyaw))
        return self.stage('Dock', ok, t0,
                          f'success={bool(res and res.success)} error_code={code} '
                          f'({DOCK_ERRORS.get(code, "?")}) '
                          f'retries={res.num_retries if res else -1}'
                          f'; TRUE docking error {err * 1000:.1f} mm (lateral {lat * 1000:+.1f}'
                          f' mm, longitudinal {lon * 1000:+.1f} mm), yaw {math.degrees(eyaw):+.2f}'
                          f' deg; robot x={gt[0]:.4f} y={gt[1]:.4f}')

    def undock(self):
        d = self.mission['dock']
        self.mon.stage = 'undock'
        t0 = self.mon.now_s()
        self.log.info(f"Stage {len(self.stages)} -> UndockRobot dock_type={d['type']}")
        self.nav.feedback = None
        if not self.nav.undockRobot(d['type']):
            return self.stage('Undock', False, t0, 'goal rejected')
        result, _ = self.run_task(60.0)
        self.wait(0.5)
        gt = self.mon.gt_pose()
        dist = math.hypot(gt[0] - d['x'], gt[1] - d['y'])
        ok = result == TaskResult.SUCCEEDED and dist >= 0.5
        return self.stage('Undock', ok, t0, f'{result.name}, robot {dist:.3f} m from the dock '
                                            f'(>= 0.50 m required)')

    def estop_test(self):
        cfg = self.mission['estop_test']
        home = self.mission['home']
        self.mon.stage = 'estop'
        t0 = self.mon.now_s()
        self.log.info(f"Stage {len(self.stages)} -> E-stop fault injection: driving to "
                      f"{home['name']}, box appears {cfg['obstacle_face_distance']:.2f} m ahead "
                      f"at >= {cfg['trigger_speed']:.2f} m/s")
        self.nav.feedback = None
        self.nav.goToPose(make_pose(self.nav, home['x'], home['y'], home['yaw_deg']))
        end = self.mon.now_s() + 40.0
        while self.mon.speed < cfg['trigger_speed'] and self.mon.now_s() < end:
            if self.nav.isTaskComplete():
                break
        if self.mon.speed < cfg['trigger_speed']:
            self.nav.cancelTask()
            return self.stage('E-stop test', False, t0, 'robot never reached trigger speed')
        x, y, yaw = self.mon.gt_pose()
        speed = self.mon.speed
        face = cc.ahead(x, y, yaw, cfg['obstacle_face_distance'])
        cx, cy = cc.ahead(x, y, yaw, cfg['obstacle_face_distance'] + cfg['obstacle_size'][0] / 2)
        gz = Gazebo()
        self.mon.arm_probe(STOP_ZONE_FAR - LIDAR_X)
        sim_spawn = self.mon.now_s()
        spawned = gz.spawn_box('estop_box', cx, cy, yaw, cfg['obstacle_size'])
        self.log.info(f'  box spawned={spawned} at x={cx:.3f} y={cy:.3f} (face '
                      f'{cfg["obstacle_face_distance"]:.2f} m ahead) while v={speed:.3f} m/s')
        end = time.monotonic() + 5.0
        while time.monotonic() < end:
            self.nav.isTaskComplete()  # keep the navigator spinning
            p = self.mon.probe_result()
            if p['stop_wall'] is not None and p['scan_wall'] is not None:
                break
        self.wait(1.5)
        gx, gy, gyaw = self.mon.gt_pose()
        gap = cc.gap_to_face(face, yaw, gx, gy, gyaw)
        p = self.mon.probe_result()
        self.nav.cancelTask()
        removed = gz.remove('estop_box')
        self.wait(1.0)  # let bt_navigator finish the cancel before the next goal
        stopped = p['stop_wall'] is not None and p['scan_wall'] is not None
        detail = f'box removed={removed}'
        if stopped:
            # processing latency: LiDAR scan stamp (sim) -> zero command received (sim clock);
            # wall-clock receive-to-receive difference logged for comparison
            proc_ms = (p['stop_sim'] - p['scan_stamp']) * 1000.0
            proc_wall_ms = (p['stop_wall'] - p['scan_wall']) * 1000.0
            e2e_ms = (p['stop_sim'] - sim_spawn) * 1000.0
            self.measured['estop_processing_ms'] = proc_ms
            self.measured['estop_end_to_end_ms'] = e2e_ms
            self.measured['estop_gap_m'] = gap
            detail = (f'LiDAR saw the box at {p["scan_range"]:.3f} m; scan stamp -> cmd_vel=0 '
                      f'{proc_ms:.1f} ms sim ({proc_wall_ms:.1f} ms wall receive-to-receive); '
                      f'box spawn request -> cmd_vel=0 {e2e_ms:.1f} ms sim; robot stopped with '
                      f'{gap * 100:.1f} cm between bumper and box; ' + detail)
        ok = stopped and gap > 0.0 and spawned
        return self.stage('E-stop test', ok, t0, detail if stopped else
                          f'NO STOP detected (scan={p["scan_wall"]}, stop={p["stop_wall"]})')

    # ---- report ----
    def kpi_rows(self, n_planned):
        rows = []

        def add(key, value, unit):
            t = self.targets[key]
            rows.append({'key': key, 'name': t['name'], 'value': value, 'unit': unit,
                         'target': t['pass'],
                         'verdict': cc.kpi_verdict(value, t['pass'], t.get('lower_is_better',
                                                                           True))})
        # mission stages = every planned stage except the bringup check
        ok_nav = sum(1 for s in self.stages if s['ok'] and s['name'] != 'System bringup')
        add('mission_success_pct', 100.0 * ok_nav / max(n_planned - 1, 1), '%')
        add('nav_final_error_m', max(self.nav_errors) if self.nav_errors else None, 'm')
        add('amcl_error_m', max(self.amcl_errors) if self.amcl_errors else None, 'm')
        add('docking_error_mm', self.measured.get('docking_error_mm'), 'mm')
        add('docking_yaw_error_deg', self.measured.get('docking_yaw_error_deg'), 'deg')
        if self.estop_enabled:
            add('estop_processing_ms', self.measured.get('estop_processing_ms'), 'ms')
            gap = self.measured.get('estop_gap_m')
            add('estop_gap_cm', None if gap is None else gap * 100.0, 'cm')
        return rows

    def run(self):
        mission_t0 = self.mon.now_s()
        steps = [self.bringup] + [lambda wp=wp: self.navigate(wp)
                                  for wp in self.mission['stations']]
        steps += [self.dock, self.undock]
        if self.estop_enabled:
            steps.append(self.estop_test)
        steps.append(lambda: self.navigate(self.mission['home']))
        for step in steps:
            if not step():
                break
        total = self.mon.now_s() - mission_t0
        n_total = len(steps)
        kpis = self.kpi_rows(n_total)
        for k in kpis:
            v = 'n/a' if k['value'] is None else f"{k['value']:.3f}"
            op = '<=' if self.targets[k['key']].get('lower_is_better', True) else '>='
            self.report(k['verdict'] != 'FAIL',
                        f"KPI {k['name']}: {v} {k['unit']} (passing target {op} "
                        f"{k['target']} {k['unit']}) -> {k['verdict']}")
        n_ok, n_kpi, verdict = evaluate(self.stages, kpis)
        if len(self.stages) < n_total:
            verdict = 'FAIL'
        summary = (f'MISSION SUMMARY: {n_ok}/{n_total} stages PASS, {n_kpi}/{len(kpis)} KPIs '
                   f'met, total {total:.1f} s (sim time) -> {verdict}')
        self.report(verdict == 'PASS', summary)
        return verdict == 'PASS'


def main():
    rclpy.init()
    nav = BasicNavigator('capstone_mission')
    path_csv = nav.declare_parameter('path_csv', '').value
    mon = Monitor(nav.get_parameter('use_sim_time').value, path_csv)
    executor = SingleThreadedExecutor()
    executor.add_node(mon)
    spin_thread = threading.Thread(target=executor.spin, daemon=True)
    spin_thread.start()
    ok = False
    try:
        ok = CapstoneMission(nav, mon).run()
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        executor.shutdown()
        if mon.csv:
            mon.csv.close()
        mon.destroy_node()
        nav.destroy_node()
        rclpy.try_shutdown()
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""
Week 16 tools: record the robot path during a mission and plot it on the map.

  ros2 run amr_week16 record_path path.csv --ros-args -p use_sim_time:=true   # Ctrl+C to stop
  ros2 run amr_week16 plot_path path.csv mission_path.png [map.yaml]

record_path samples TF map -> base_footprint (the AMCL-localised pose) at 5 Hz.
"""

import csv
import math
import os
import sys


def record_main(args=None):
    import rclpy
    from rclpy.executors import ExternalShutdownException
    from tf2_ros import Buffer, TransformException, TransformListener

    rclpy.init(args=args)
    argv = rclpy.utilities.remove_ros_args(sys.argv)
    out = argv[1] if len(argv) > 1 else 'path.csv'
    node = rclpy.create_node('record_path')
    buf = Buffer()
    TransformListener(buf, node)
    f = open(out, 'w')
    f.write('t,x,y,yaw\n')

    def tick():
        try:
            t = buf.lookup_transform('map', 'base_footprint', rclpy.time.Time())
        except TransformException:
            return
        q, p = t.transform.rotation, t.transform.translation
        yaw = math.atan2(2 * (q.w * q.z + q.x * q.y), 1 - 2 * (q.y * q.y + q.z * q.z))
        stamp = t.header.stamp.sec + t.header.stamp.nanosec * 1e-9
        f.write(f'{stamp:.2f},{p.x:.3f},{p.y:.3f},{yaw:.3f}\n')
        f.flush()

    node.create_timer(0.2, tick)
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        f.close()
        node.destroy_node()
        rclpy.try_shutdown()


def plot(csv_path, png_path, map_yaml):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import numpy as np
    from amr_week12.map_tools import load_map
    from amr_week16.final_mission_executor import MISSION

    grid, info = load_map(map_yaml)
    res, (ox, oy) = info['resolution'], info['origin'][:2]
    img = np.full(grid.shape, 0.8)
    img[grid == 0] = 1.0
    img[grid == 100] = 0.0
    with open(csv_path) as f:
        rows = list(csv.DictReader(f))
    xs, ys = [float(r['x']) for r in rows], [float(r['y']) for r in rows]
    fig, ax = plt.subplots(figsize=(6.4, 6.4), dpi=110)
    ax.imshow(img, cmap='gray', vmin=0, vmax=1, origin='lower', interpolation='nearest',
              extent=[ox, ox + grid.shape[1] * res, oy, oy + grid.shape[0] * res])
    ax.plot(xs, ys, '-', color='tab:blue', lw=1.8, label='robot path (TF map->base_footprint, AMCL)')
    ax.plot([0], [0], 's', color='tab:green', ms=8, label='start / Home')
    for i, wp in enumerate(MISSION, 1):
        ax.plot(wp['x'], wp['y'], 'o', mfc='none', mec='tab:red', ms=14, mew=1.6)
        ax.annotate(f"{i}. {wp['name']}", (wp['x'], wp['y']), xytext=(8, 8),
                    textcoords='offset points', fontsize=8, color='tab:red')
    ax.set_xlabel('x [m] (map frame)')
    ax.set_ylabel('y [m]')
    ax.grid(alpha=0.25)
    ax.set_title('Week 16 mission - real headless run (Gazebo + Nav2)', fontsize=10)
    ax.legend(loc='lower right', fontsize=8)
    fig.tight_layout()
    fig.savefig(png_path)
    plt.close(fig)
    return len(rows)


def plot_main():
    if len(sys.argv) < 3:
        print('usage: plot_path path.csv out.png [map.yaml]')
        sys.exit(2)
    if len(sys.argv) > 3:
        map_yaml = sys.argv[3]
    else:
        from ament_index_python.packages import get_package_share_directory
        map_yaml = os.path.join(get_package_share_directory('amr_week12'), 'maps',
                                'warehouse_map.yaml')
    n = plot(sys.argv[1], sys.argv[2], map_yaml)
    print(f'wrote {sys.argv[2]} ({n} samples)')


if __name__ == '__main__':
    plot_main()

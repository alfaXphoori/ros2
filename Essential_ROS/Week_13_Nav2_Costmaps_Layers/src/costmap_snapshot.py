#!/usr/bin/env python3
"""
Week 13 Lab tool: take one snapshot of the published costmaps and print what the
numbers mean (optionally save a PNG of the global costmap).

  ros2 run amr_week13 costmap_snapshot
  ros2 run amr_week13 costmap_snapshot --png global_costmap.png

nav_msgs/OccupancyGrid  (/<name>/costmap)     : 0 free, 1..98 inflated, 99 inscribed,
                                                100 lethal, -1 unknown
nav2_msgs/Costmap       (/<name>/costmap_raw) : 0 free, 1..252 inflated, 253 inscribed,
                                                254 lethal, 255 no information
"""

import argparse
import collections
import time

import numpy as np


def occupancy_summary(data):
    c = collections.Counter(data)
    return {'unknown(-1)': c.get(-1, 0), 'free(0)': c.get(0, 0),
            'inflated(1..98)': sum(v for k, v in c.items() if 1 <= k <= 98),
            'inscribed(99)': c.get(99, 0), 'lethal(100)': c.get(100, 0)}


def raw_summary(data):
    c = collections.Counter(data)
    return {'free(0)': c.get(0, 0), 'inflated(1..252)': sum(v for k, v in c.items() if 1 <= k <= 252),
            'inscribed(253)': c.get(253, 0), 'lethal(254)': c.get(254, 0),
            'no_information(255)': c.get(255, 0)}


def render_png(grid, origin, res, path, title):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    img = np.ma.masked_less(grid.astype(float), 0)
    cmap = plt.get_cmap('magma_r').copy()
    cmap.set_bad('#9ecae1')
    extent = [origin[0], origin[0] + grid.shape[1] * res, origin[1], origin[1] + grid.shape[0] * res]
    fig, ax = plt.subplots(figsize=(6.6, 6.0), dpi=110)
    im = ax.imshow(img, cmap=cmap, vmin=0, vmax=100, origin='lower', extent=extent,
                   interpolation='nearest')
    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04,
                 label='OccupancyGrid value (100 lethal, 99 inscribed, blue = unknown)')
    ax.set_xlabel('x [m] (map frame)')
    ax.set_ylabel('y [m]')
    ax.set_title(title, fontsize=10)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def main(argv=None):
    import rclpy
    from nav2_msgs.msg import Costmap
    from nav_msgs.msg import OccupancyGrid
    from rclpy.qos import DurabilityPolicy, QoSProfile, ReliabilityPolicy

    ap = argparse.ArgumentParser(description='Print costmap value statistics')
    ap.add_argument('--png', help='save the global costmap as PNG')
    ap.add_argument('--timeout', type=float, default=60.0)
    args, ros_args = ap.parse_known_args(argv)

    rclpy.init(args=ros_args)
    node = rclpy.create_node('costmap_snapshot')
    got = {}
    qos = QoSProfile(depth=1, durability=DurabilityPolicy.TRANSIENT_LOCAL,
                     reliability=ReliabilityPolicy.RELIABLE)
    topics = [('/global_costmap/costmap', OccupancyGrid), ('/local_costmap/costmap', OccupancyGrid),
              ('/global_costmap/costmap_raw', Costmap)]
    for name, typ in topics:
        node.create_subscription(typ, name, lambda m, n=name: got.__setitem__(n, m), qos)
    end = time.monotonic() + args.timeout
    while time.monotonic() < end and len(got) < len(topics):
        rclpy.spin_once(node, timeout_sec=0.2)

    for name in ('/global_costmap/costmap', '/local_costmap/costmap'):
        if name not in got:
            print(f'{name}: not received')
            continue
        m = got[name]
        print(f'{name}: frame={m.header.frame_id} {m.info.width}x{m.info.height} cells '
              f'@ {m.info.resolution:.2f} m')
        print('  ' + ', '.join(f'{k}: {v}' for k, v in occupancy_summary(list(m.data)).items()))
    if '/global_costmap/costmap_raw' in got:
        r = got['/global_costmap/costmap_raw']
        print(f'/global_costmap/costmap_raw: {r.metadata.size_x}x{r.metadata.size_y} cells (raw 0..255)')
        print('  ' + ', '.join(f'{k}: {v}' for k, v in raw_summary(list(r.data)).items()))
    if args.png and '/global_costmap/costmap' in got:
        m = got['/global_costmap/costmap']
        grid = np.array(m.data, dtype=np.int16).reshape(m.info.height, m.info.width)
        render_png(grid, (m.info.origin.position.x, m.info.origin.position.y), m.info.resolution,
                   args.png, 'Global costmap (static + obstacle + inflation layers)')
        print(f'wrote {args.png}')
    node.destroy_node()
    rclpy.try_shutdown()


if __name__ == '__main__':
    main()

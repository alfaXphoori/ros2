#!/usr/bin/env python3
"""
Advanced Module 06: plot a capstone run (path CSV from capstone_mission -p path_csv:=...).

  ros2 run amr_adv06 plot_capstone results/capstone_path.csv images/capstone_path_real.png

Draws the real Week 12 SLAM map, the TRUE robot path (Gazebo ground truth), the AMCL estimate,
the stations, the charger (dock pose + AprilTag) and, if present, the e-stop test segment.
"""

import csv
import math
import os
import sys


def plot(csv_path, png_path, map_yaml, mission):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import numpy as np
    from amr_week12.map_tools import load_map
    try:
        from amr_adv06 import capstone_config as cc
    except ImportError:
        import capstone_config as cc

    grid, info = load_map(map_yaml)
    res, (ox, oy) = info['resolution'], info['origin'][:2]
    img = np.full(grid.shape, 0.85)
    img[grid == 0] = 1.0
    img[grid == 100] = 0.0
    with open(csv_path) as f:
        rows = list(csv.DictReader(f))
    col = {k: np.array([float(r[k]) for r in rows]) for k in
           ('gt_x', 'gt_y', 'amcl_x', 'amcl_y')}
    stage = np.array([r['stage'] for r in rows])

    fig, ax = plt.subplots(figsize=(6.6, 6.6), dpi=110)
    ax.imshow(img, cmap='gray', vmin=0, vmax=1, origin='lower', interpolation='nearest',
              extent=[ox, ox + grid.shape[1] * res, oy, oy + grid.shape[0] * res])
    ax.plot(col['gt_x'], col['gt_y'], '-', color='#1f6fb4', lw=1.8,
            label='true path (Gazebo ground truth)')
    ax.plot(col['amcl_x'], col['amcl_y'], '--', color='#e07b00', lw=1.0,
            label='AMCL estimate (TF map -> base_footprint)')
    est = stage == 'estop'
    if est.any():
        ax.plot(col['gt_x'][est], col['gt_y'][est], '-', color='#c62828', lw=3.0, zorder=5,
                label='e-stop test (drive -> box appears -> stop)')
        ax.plot(col['gt_x'][est][-1], col['gt_y'][est][-1], 'o', color='#c62828', ms=6,
                zorder=6)
        ax.annotate('E-stop', (col['gt_x'][est][-1], col['gt_y'][est][-1]), xytext=(8, 4),
                    textcoords='offset points', fontsize=8, color='#c62828')
    home = mission['home']
    ax.plot(home['x'], home['y'], 's', color='#2e7d32', ms=8, label='Home (start / end)')
    for i, wp in enumerate(mission['stations'], 1):
        ax.plot(wp['x'], wp['y'], 'o', mfc='none', mec='#6a1b9a', ms=14, mew=1.6)
        ax.annotate(f"{i}. {wp['name']}", (wp['x'], wp['y']), xytext=(-30, -20),
                    textcoords='offset points', fontsize=8, color='#6a1b9a')
    d = mission['dock']
    dx, dy, dyaw = cc.dock_pose(d)
    tx, ty, _, _ = cc.tag_world(d)
    sx, sy, _ = cc.staging_pose(d)
    ax.arrow(dx, dy, 0.25 * math.cos(dyaw), 0.25 * math.sin(dyaw), width=0.03,
             color='#00897b', length_includes_head=True)
    ax.plot([tx], [ty], 'D', color='#00897b', ms=6, label='charger AprilTag (id 0)')
    ax.plot([sx], [sy], 'x', color='#00897b', ms=8, mew=2, label='staging pose')
    ax.annotate(f"{len(mission['stations']) + 1}. Dock {d['id']}", (dx, dy), xytext=(10, -12),
                textcoords='offset points', fontsize=8, color='#00897b')
    ax.set_xlabel('x [m] (map ~ Gazebo world)')
    ax.set_ylabel('y [m]')
    ax.grid(alpha=0.25)
    ax.set_title('Capstone mission - real headless run (Gazebo + Nav2 + docking)', fontsize=10)
    ax.legend(loc='upper right', fontsize=7, framealpha=0.95)
    fig.tight_layout()
    fig.savefig(png_path)
    plt.close(fig)
    return len(rows)


def main():
    if len(sys.argv) < 3:
        print('usage: plot_capstone path.csv out.png [map.yaml] [mission.yaml]')
        sys.exit(2)
    from ament_index_python.packages import get_package_share_directory
    from amr_adv06.capstone_config import load_mission
    map_yaml = sys.argv[3] if len(sys.argv) > 3 else os.path.join(
        get_package_share_directory('amr_week12'), 'maps', 'warehouse_map.yaml')
    mission = load_mission(sys.argv[4] if len(sys.argv) > 4 else None)
    n = plot(sys.argv[1], sys.argv[2], map_yaml, mission)
    print(f'wrote {sys.argv[2]} ({n} samples)')


if __name__ == '__main__':
    main()

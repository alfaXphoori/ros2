#!/usr/bin/env python3
"""
Week 12 helpers: load a nav2 map (.yaml + .pgm), rasterise the ground-truth
warehouse.sdf into the same grid, compute coverage / IoU, and render a PNG.

  ros2 run amr_week12 render_map --map maps/warehouse_map.yaml --out images/warehouse_map.png

Pure numpy/matplotlib so it is unit-testable without a ROS graph.
"""

import argparse
import os
import xml.etree.ElementTree as ET

import numpy as np
import yaml


def read_pgm(path):
    """Read a binary (P5) PGM into a uint8 array (row 0 = top of the image)."""
    with open(path, 'rb') as f:
        data = f.read()
    tokens, pos = [], 0
    while len(tokens) < 4:                      # magic, width, height, maxval
        while data[pos:pos + 1].isspace():
            pos += 1
        if data[pos:pos + 1] == b'#':
            pos = data.index(b'\n', pos) + 1
            continue
        start = pos
        while not data[pos:pos + 1].isspace():
            pos += 1
        tokens.append(data[start:pos])
    if tokens[0] != b'P5':
        raise ValueError(f'{path}: only binary P5 PGM supported')
    w, h = int(tokens[1]), int(tokens[2])
    return np.frombuffer(data[pos + 1:pos + 1 + w * h], dtype=np.uint8).reshape(h, w)


def load_map(yaml_path):
    """Return (grid, info) where grid[row, col] uses row 0 = lowest y (ROS convention)
    and values: 100 occupied, 0 free, -1 unknown (trinary, as map_server publishes)."""
    with open(yaml_path) as f:
        info = yaml.safe_load(f)
    img = read_pgm(os.path.join(os.path.dirname(yaml_path), info['image']))
    p = (255.0 - img) / 255.0 if not info.get('negate', 0) else img / 255.0
    grid = np.full(img.shape, -1, dtype=np.int8)
    grid[p > info['occupied_thresh']] = 100
    grid[p < info['free_thresh']] = 0
    return np.flipud(grid), info


def sdf_boxes(sdf_path):
    """[(cx, cy, sx, sy, name)] of every <collision> box in the world (static models)."""
    boxes = []
    for col in ET.parse(sdf_path).getroot().iter('collision'):
        size = col.find('geometry/box/size')
        if size is None:
            continue
        pose = [float(v) for v in col.find('pose').text.split()] if col.find('pose') is not None \
            else [0.0] * 6
        sx, sy, _ = (float(v) for v in size.text.split())
        boxes.append((pose[0], pose[1], sx, sy, col.get('name')))
    return boxes


def rasterize(boxes, shape, resolution, origin):
    """Boolean occupancy grid (row 0 = lowest y) of the SDF boxes in the map frame."""
    h, w = shape
    xs = origin[0] + (np.arange(w) + 0.5) * resolution
    ys = origin[1] + (np.arange(h) + 0.5) * resolution
    gx, gy = np.meshgrid(xs, ys)
    occ = np.zeros(shape, dtype=bool)
    for cx, cy, sx, sy, _ in boxes:
        occ |= (np.abs(gx - cx) <= sx / 2) & (np.abs(gy - cy) <= sy / 2)
    return occ


def dilate(mask, cells):
    out = mask.copy()
    for dy in range(-cells, cells + 1):
        for dx in range(-cells, cells + 1):
            out |= np.roll(np.roll(mask, dy, axis=0), dx, axis=1)
    return out


def iou(a, b):
    union = np.logical_or(a, b).sum()
    return float(np.logical_and(a, b).sum()) / union if union else 0.0


def map_stats(yaml_path, sdf_path, tol_cells=2):
    grid, info = load_map(yaml_path)
    res, origin = info['resolution'], info['origin']
    occ = grid == 100
    truth = rasterize(sdf_boxes(sdf_path), grid.shape, res, origin)
    ys, xs = np.nonzero(grid >= 0)
    known_extent = ((xs.max() - xs.min() + 1) * res, (ys.max() - ys.min() + 1) * res)
    # tolerance-aware IoU: a cell counts as matched if within tol_cells of the other set
    matched_map = np.logical_and(occ, dilate(truth, tol_cells))
    matched_truth = np.logical_and(truth, dilate(occ, tol_cells))
    precision = matched_map.sum() / max(occ.sum(), 1)
    recall_walls = matched_truth.sum() / max(truth.sum(), 1)
    return {
        'width': grid.shape[1], 'height': grid.shape[0], 'resolution': res,
        'origin': origin[:2],
        'size_m': (round(grid.shape[1] * res, 3), round(grid.shape[0] * res, 3)),
        'known_extent_m': (round(float(known_extent[0]), 3), round(float(known_extent[1]), 3)),
        'occupied': int(occ.sum()), 'free': int((grid == 0).sum()),
        'unknown': int((grid == -1).sum()),
        'iou_strict': round(iou(occ, truth), 3),
        'precision_tol': round(float(precision), 3), 'recall_tol': round(float(recall_walls), 3),
    }


def render(yaml_path, sdf_path, out_png, title='SLAM Toolbox map (real run)'):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.patches import Rectangle

    grid, info = load_map(yaml_path)
    res, (ox, oy) = info['resolution'], info['origin'][:2]
    img = np.full(grid.shape, 0.75)
    img[grid == 0] = 1.0
    img[grid == 100] = 0.0
    extent = [ox, ox + grid.shape[1] * res, oy, oy + grid.shape[0] * res]
    fig, ax = plt.subplots(figsize=(6.4, 6.4), dpi=110)
    ax.imshow(img, cmap='gray', vmin=0, vmax=1, origin='lower', extent=extent,
              interpolation='nearest')
    if sdf_path:
        for i, (cx, cy, sx, sy, _) in enumerate(sdf_boxes(sdf_path)):
            ax.add_patch(Rectangle((cx - sx / 2, cy - sy / 2), sx, sy, fill=False,
                                   ec='tab:red', lw=0.8, ls='--',
                                   label='warehouse.sdf (ground truth)' if i == 0 else None))
        ax.legend(loc='upper right', fontsize=8)
    ax.set_xlabel('x [m] (map frame)')
    ax.set_ylabel('y [m]')
    ax.set_title(title, fontsize=10)
    ax.grid(alpha=0.25)
    fig.tight_layout()
    fig.savefig(out_png)
    plt.close(fig)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split('\n\n')[0])
    ap.add_argument('--map', required=True, help='map .yaml from map_saver_cli')
    ap.add_argument('--sdf', default=None, help='world .sdf to overlay / compare')
    ap.add_argument('--out', default=None, help='output PNG')
    args = ap.parse_args(argv)
    sdf = args.sdf
    if sdf is None:
        try:
            from ament_index_python.packages import get_package_share_directory
            sdf = os.path.join(get_package_share_directory('amr_week10'), 'worlds', 'warehouse.sdf')
        except Exception:  # noqa: BLE001 - optional overlay
            sdf = None
    if sdf:
        for k, v in map_stats(args.map, sdf).items():
            print(f'{k}: {v}')
    if args.out:
        render(args.map, sdf, args.out)
        print(f'wrote {args.out}')


if __name__ == '__main__':
    main()

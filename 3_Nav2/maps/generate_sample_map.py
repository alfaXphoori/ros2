#!/usr/bin/env python3
"""
Generate a sample warehouse map (PGM image + YAML metadata) for ROS 2 Navigation 2 (Nav2).
Grid size: 300x300 cells (15.0m x 15.0m at 0.05m resolution).
Origin: [-7.5, -7.5, 0.0] (center at 0, 0).
"""

import os
import sys

def generate_map(output_dir="."):
    width = 300
    height = 300
    resolution = 0.05  # 5 cm/pixel
    origin_x = -7.5
    origin_y = -7.5
    origin_yaw = 0.0

    # Pixel values in standard ROS map representation:
    # 254: free space (white)
    # 0:   occupied obstacle (black)
    # 205: unknown space (gray)

    # Initialize grid with free space
    grid = [[254 for _ in range(width)] for _ in range(height)]

    # 1. Outer perimeter walls (thickness 3 pixels)
    wall_thickness = 3
    for y in range(height):
        for x in range(width):
            if x < wall_thickness or x >= width - wall_thickness or \
               y < wall_thickness or y >= height - wall_thickness:
                grid[y][x] = 0

    # Helper function to draw filled rectangle
    def draw_box(x1, y1, x2, y2, val=0):
        for y in range(max(0, y1), min(height, y2)):
            for x in range(max(0, x1), min(width, x2)):
                grid[y][x] = val

    # Helper to convert metric coordinates to grid cell (row y, col x)
    # (0, 0) in metric is at index (150, 150)
    def to_cell(mx, my):
        gx = int((mx - origin_x) / resolution)
        gy = int((my - origin_y) / resolution)
        return gx, gy

    # 2. Add Warehouse Shelves / Racks
    # Left racks (aisle 1)
    # Shelf 1: x in [-5.0, -3.5], y in [1.5, 5.5]
    c1x, c1y = to_cell(-5.0, 1.5)
    c2x, c2y = to_cell(-3.5, 5.5)
    draw_box(c1x, c1y, c2x, c2y, 0)

    # Shelf 2: x in [-5.0, -3.5], y in [-5.5, -1.5]
    c1x, c1y = to_cell(-5.0, -5.5)
    c2x, c2y = to_cell(-3.5, -1.5)
    draw_box(c1x, c1y, c2x, c2y, 0)

    # Center-Right racks (aisle 2)
    # Shelf 3: x in [1.0, 2.5], y in [1.5, 5.5]
    c1x, c1y = to_cell(1.0, 1.5)
    c2x, c2y = to_cell(2.5, 5.5)
    draw_box(c1x, c1y, c2x, c2y, 0)

    # Shelf 4: x in [1.0, 2.5], y in [-5.5, -1.5]
    c1x, c1y = to_cell(1.0, -5.5)
    c2x, c2y = to_cell(2.5, -1.5)
    draw_box(c1x, c1y, c2x, c2y, 0)

    # Far-Right storage zone (aisle 3)
    # Shelf 5: x in [4.5, 6.0], y in [-3.5, 3.5]
    c1x, c1y = to_cell(4.5, -3.5)
    c2x, c2y = to_cell(6.0, 3.5)
    draw_box(c1x, c1y, c2x, c2y, 0)

    # 3. Add Warehouse Pillars (Four central square pillars)
    pillars = [(-1.5, 3.5), (-1.5, -3.5), (3.5, 3.5), (3.5, -3.5)]
    for px, py in pillars:
        cx, cy = to_cell(px, py)
        draw_box(cx - 4, cy - 4, cx + 5, cy + 5, 0)

    # 4. Unknown areas outside building / loading dock alcove
    # e.g., small partition room in top-left corner
    rc1x, rc1y = to_cell(-7.5, 5.0)
    rc2x, rc2y = to_cell(-6.0, 7.5)
    draw_box(rc1x, rc1y, rc2x, rc2y, 0)

    # Convert to PGM bytes (P5 format: top row is image row 0)
    # In Cartesian: y=0 is at bottom (origin_y). In PGM: row 0 is at top.
    # So we invert the row order for saving
    raw_bytes = bytearray(width * height)
    for row in range(height):
        img_row = height - 1 - row
        for col in range(width):
            raw_bytes[img_row * width + col] = grid[row][col]

    os.makedirs(output_dir, exist_ok=True)
    pgm_path = os.path.join(output_dir, "warehouse_map.pgm")
    yaml_path = os.path.join(output_dir, "warehouse_map.yaml")

    header = f"P5\n# Generated warehouse map for Nav2 simulation\n{width} {height}\n255\n".encode('ascii')
    with open(pgm_path, 'wb') as f:
        f.write(header)
        f.write(raw_bytes)

    yaml_content = f"""image: warehouse_map.pgm
mode: trinary
resolution: {resolution:.6f}
origin: [{origin_x:.6f}, {origin_y:.6f}, {origin_yaw:.6f}]
negate: 0
occupied_thresh: 0.65
free_thresh: 0.25
"""
    with open(yaml_path, 'w', encoding='utf-8') as f:
        f.write(yaml_content)

    print(f"Map generated successfully:")
    print(f"  PGM:  {pgm_path} ({os.path.getsize(pgm_path)} bytes)")
    print(f"  YAML: {yaml_path}")

if __name__ == "__main__":
    out_dir = os.path.dirname(os.path.abspath(__file__))
    if len(sys.argv) > 1:
        out_dir = sys.argv[1]
    generate_map(out_dir)

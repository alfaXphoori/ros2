#!/usr/bin/env python3

"""
ce_webots / save_map.py
========================
ROS 2 node to save OccupancyGrid (/map topic) as standard PGM image and YAML metadata,
compatible with ROS 2 Nav2 map_server and nav2_map_server.

Usage:
  ros2 run ce_webots save_map --ros-args -p map_name:=warehouse_map -p output_dir:=/path/to/maps
"""

import os
import sys
import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, DurabilityPolicy, HistoryPolicy
from nav_msgs.msg import OccupancyGrid


class MapSaver(Node):
    def __init__(self):
        super().__init__('ce_map_saver')

        # Declare parameters
        self.declare_parameter('map_topic', '/map')
        self.declare_parameter('map_name', 'warehouse_map')
        self.declare_parameter('output_dir', '.')
        self.declare_parameter('occupied_thresh', 0.65)
        self.declare_parameter('free_thresh', 0.25)
        self.declare_parameter('save_once', True)

        self.map_topic = self.get_parameter('map_topic').get_parameter_value().string_value
        self.map_name = self.get_parameter('map_name').get_parameter_value().string_value
        self.output_dir = self.get_parameter('output_dir').get_parameter_value().string_value
        self.occupied_thresh = self.get_parameter('occupied_thresh').get_parameter_value().double_value
        self.free_thresh = self.get_parameter('free_thresh').get_parameter_value().double_value
        self.save_once = self.get_parameter('save_once').get_parameter_value().bool_value

        self.saved = False

        # Map topics typically use Transient Local durability
        qos_profile = QoSProfile(
            reliability=ReliabilityPolicy.RELIABLE,
            durability=DurabilityPolicy.TRANSIENT_LOCAL,
            history=HistoryPolicy.KEEP_LAST,
            depth=1
        )

        self.get_logger().info(f"Subscribing to '{self.map_topic}' and waiting for map data...")
        self.subscription = self.create_subscription(
            OccupancyGrid,
            self.map_topic,
            self.map_callback,
            qos_profile
        )

        # Fallback subscription with default QoS in case publisher uses volatile durability
        self.subscription_volatile = self.create_subscription(
            OccupancyGrid,
            self.map_topic,
            self.map_callback,
            10
        )

    def map_callback(self, msg: OccupancyGrid):
        if self.saved and self.save_once:
            return

        width = msg.info.width
        height = msg.info.height
        resolution = msg.info.resolution
        origin_x = msg.info.origin.position.x
        origin_y = msg.info.origin.position.y
        origin_z = msg.info.origin.position.z

        self.get_logger().info(f"Received map: {width}x{height} cells, resolution={resolution:.3f}m/cell")

        # Ensure output directory exists
        os.makedirs(self.output_dir, exist_ok=True)

        pgm_filename = f"{self.map_name}.pgm"
        yaml_filename = f"{self.map_name}.yaml"
        pgm_path = os.path.join(self.output_dir, pgm_filename)
        yaml_path = os.path.join(self.output_dir, yaml_filename)

        # Convert OccupancyGrid data to PGM grayscale (P5 binary)
        # Note: OccupancyGrid row 0 is at bottom (y=0). PGM image row 0 is at top.
        # So we iterate rows from height - 1 down to 0.
        pixels = bytearray(width * height)
        occ_thresh_val = int(self.occupied_thresh * 100)
        free_thresh_val = int(self.free_thresh * 100)

        for y in range(height):
            # Invert row index for image coordinates
            img_y = (height - 1 - y)
            row_start = y * width
            img_row_start = img_y * width

            for x in range(width):
                val = msg.data[row_start + x]
                if val < 0:
                    # Unknown: gray (205)
                    pixel = 205
                elif val >= occ_thresh_val:
                    # Occupied: black (0)
                    pixel = 0
                elif val <= free_thresh_val:
                    # Free space: white (254)
                    pixel = 254
                else:
                    # Intermediate probability
                    pixel = int(254 - (val / 100.0) * 254)

                pixels[img_row_start + x] = pixel

        # Write PGM binary (P5)
        header = f"P5\n# Created by ce_webots map_saver\n{width} {height}\n255\n".encode('ascii')
        with open(pgm_path, 'wb') as f:
            f.write(header)
            f.write(pixels)

        # Write YAML metadata
        yaml_content = f"""image: {pgm_filename}
mode: trinary
resolution: {resolution:.6f}
origin: [{origin_x:.6f}, {origin_y:.6f}, {origin_z:.6f}]
negate: 0
occupied_thresh: {self.occupied_thresh:.2f}
free_thresh: {self.free_thresh:.2f}
"""
        with open(yaml_path, 'w', encoding='utf-8') as f:
            f.write(yaml_content)

        self.get_logger().info(f"✅ Successfully saved map files:")
        self.get_logger().info(f"   PGM:  {pgm_path}")
        self.get_logger().info(f"   YAML: {yaml_path}")

        self.saved = True

        if self.save_once:
            self.get_logger().info("Map saved successfully. Shutting down map saver node.")
            rclpy.shutdown()


def main(args=None):
    rclpy.init(args=args)
    node = MapSaver()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, rclpy.executors.ExternalShutdownException):
        pass
    finally:
        if rclpy.ok():
            node.destroy_node()
            rclpy.shutdown()


if __name__ == '__main__':
    main()

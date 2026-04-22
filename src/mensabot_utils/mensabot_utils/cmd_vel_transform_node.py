#!/usr/bin/env python3

from geometry_msgs.msg import Twist, TwistStamped
from sensor_msgs.msg import LaserScan   
import rclpy
from rclpy.node import Node

class TwistToStamped(Node):
    def __init__(self):
        super().__init__('twist_to_stamped')

        self.sub = self.create_subscription(
            Twist,
            '/cmd_vel',
            self.cb,
            10
        )

        self.pub = self.create_publisher(
            TwistStamped,
            '/mensabot_base_controller/cmd_vel',
            10
        )

        self.sub_merged_laser_scan = self.create_subscription( #only use is forcing the laser scan merger to start, since it is not used anywhere else
            LaserScan,
            '/merged_scan',
            self.cb_laser_scan,
            10
        )

        self.get_logger().info("cmd_vel transform node has been started.")

    def cb(self, msg):
        out = TwistStamped()
        out.header.stamp = self.get_clock().now().to_msg()
        out.header.frame_id = "base_link"
        out.twist = msg
        self.pub.publish(out)

    def cb_laser_scan(self, msg):
        pass   

def main(args=None):
    """
    Entry point for the TwistToStamped node.

    Initializes rclpy, spins the node, and performs
    a clean shutdown when the node stops.
    """
    rclpy.init(args=args)
    node = TwistToStamped()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()
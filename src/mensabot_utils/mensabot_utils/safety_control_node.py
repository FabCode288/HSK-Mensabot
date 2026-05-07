#!/usr/bin/env python3

import rclpy
from rclpy.node import Node

from geometry_msgs.msg import Twist
from std_msgs.msg import Bool

from rclpy.action import ActionClient
from nav2_msgs.action import NavigateToPose

import gpiod


class SafetyControlNode(Node):

    def __init__(self):
        super().__init__('safety_control_node')

        # ================= GPIO =================

        self.gpio_chip_name = 'gpiochip4'
        self.gpio_line_number = 17

        self.chip = gpiod.Chip(self.gpio_chip_name)

        self.estop_line = self.chip.get_line(self.gpio_line_number)

        self.estop_line.request(
            consumer='safety_control_node',
            type=gpiod.LINE_REQ_DIR_IN
        )

        # ================= FLAGS =================

        self.estop_active = False

        self.connected = False

        self.nav2_goal_canceled = False

        # ================= SUBSCRIBER =================

        self.cmd_vel_sub = self.create_subscription(
            Twist,
            '/cmd_vel',
            self.cmd_vel_callback,
            10
        )

        self.connected_sub = self.create_subscription(
            Bool,
            '/hardware/connected',
            self.connected_callback,
            10
        )

        # ================= PUBLISHER =================

        self.cmd_vel_pub = self.create_publisher(
            Twist,
            '/safety/cmd_vel',
            10
        )

        self.estop_pub = self.create_publisher(
            Bool,
            '/safety/estop',
            10
        )

        # ================= NAV2 ACTION CLIENT =================

        self.nav_to_pose_client = ActionClient(
            self,
            NavigateToPose,
            '/navigate_to_pose'
        )

        # ================= TIMER =================

        self.timer = self.create_timer(
            0.02,
            self.timer_callback
        )

        self.get_logger().info('Safety Control Node started')

    # ==========================================================
    # CMD VEL CALLBACK
    # ==========================================================

    def cmd_vel_callback(self, msg: Twist):

        # BLOCK MOTION
        if self.estop_active or not self.connected:

            self.publish_zero_twist()

            return

        # FORWARD CMD_VEL
        self.cmd_vel_pub.publish(msg)

    # ==========================================================
    # CONNECTED CALLBACK
    # ==========================================================

    def connected_callback(self, msg: Bool):

        self.connected = msg.data

    # ==========================================================
    # TIMER CALLBACK
    # ==========================================================

    def timer_callback(self):

        gpio_state = self.estop_line.get_value()

        # ======================================================
        # ESTOP ACTIVE
        # ======================================================

        if gpio_state == 1:

            self.estop_active = True

            estop_msg = Bool()
            estop_msg.data = True

            self.estop_pub.publish(estop_msg)

            self.publish_zero_twist()

            # Cancel Nav2 goal only once
            if not self.nav2_goal_canceled:

                self.cancel_nav2_goal()

                self.nav2_goal_canceled = True

        # ======================================================
        # ESTOP RELEASED
        # ======================================================

        else:

            self.estop_active = False

            estop_msg = Bool()
            estop_msg.data = False

            self.estop_pub.publish(estop_msg)

            self.nav2_goal_canceled = False

            # Still block if not connected
            if not self.connected:

                self.publish_zero_twist()

    # ==========================================================
    # ZERO TWIST
    # ==========================================================

    def publish_zero_twist(self):

        zero_msg = Twist()

        zero_msg.linear.x = 0.0
        zero_msg.linear.y = 0.0
        zero_msg.linear.z = 0.0

        zero_msg.angular.x = 0.0
        zero_msg.angular.y = 0.0
        zero_msg.angular.z = 0.0

        self.cmd_vel_pub.publish(zero_msg)

    # ==========================================================
    # CANCEL NAV2 GOAL
    # ==========================================================

    def cancel_nav2_goal(self):

        self.get_logger().warn('ESTOP ACTIVE -> Cancel Nav2 Goal')

        if not self.nav_to_pose_client.wait_for_server(timeout_sec=1.0):

            self.get_logger().warn('NavigateToPose action server not available')

            return

        future = self.nav_to_pose_client._cancel_goal_async(None)

        self.get_logger().warn('Nav2 cancel request sent')

    # ==========================================================
    # CLEANUP
    # ==========================================================

    def destroy_node(self):

        self.estop_line.release()

        self.chip.close()

        super().destroy_node()


# ==============================================================
# MAIN
# ==============================================================

def main(args=None):

    rclpy.init(args=args)

    node = SafetyControlNode()

    try:

        rclpy.spin(node)

    except KeyboardInterrupt:

        pass

    node.destroy_node()

    rclpy.shutdown()


if __name__ == '__main__':
    main()
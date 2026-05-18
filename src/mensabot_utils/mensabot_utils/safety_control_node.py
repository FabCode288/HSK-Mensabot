#!/usr/bin/env python3

import rclpy
from rclpy.node import Node

from geometry_msgs.msg import Twist
from std_msgs.msg import Bool
from std_msgs.msg import Float32

import gpiod


class SafetyControlNode(Node):

    def __init__(self):
        super().__init__('safety_control_node')

        # ======================================================
        # GPIO CONFIG
        # ======================================================

        # GPIO for external ESTOP relay / button
        self.gpio_chip_name = 'gpiochip4'
        self.gpio_line_number = 17

        self.chip = gpiod.Chip(self.gpio_chip_name)

        self.estop_line = self.chip.get_line(self.gpio_line_number)

        self.estop_line.request(consumer='safety_control_node',type=gpiod.LINE_REQ_DIR_IN)

        # ======================================================
        # PARAMETERS
        # ======================================================

        self.normal_speed_limit = 100.0
        self.warning_speed_limit = 30.0
        self.estop_speed_limit = 0.0

        # ======================================================
        # STATES
        # ======================================================

        self.hardware_connected = False

        self.estop_gpio_active = False
        self.estop_scanner_active = False
        self.warning_field_active = False

        self.current_speed_limit = -1.0

        # ======================================================
        # SUBSCRIBERS
        # ======================================================

        # Sick field output
        # TRUE = field active
        self.sick_field_sub = self.create_subscription(
            Bool,
            '/sick_field_output',
            self.sick_field_callback,
            10
        )

        # Hardware connected
        self.connected_sub = self.create_subscription(
            Bool,
            '/hardware/connected',
            self.connected_callback,
            10
        )

        # Original cmd_vel
        self.cmd_vel_sub = self.create_subscription(
            Twist,
            '/cmd_vel',
            self.cmd_vel_callback,
            10
        )

        # ======================================================
        # PUBLISHERS
        # ======================================================

        # Nav2 velocity smoother speed limit
        self.speed_limit_pub = self.create_publisher(
            Float32,
            '/speed_limit',
            10
        )

        # ESTOP output
        self.estop_pub = self.create_publisher(
            Bool,
            '/safety/estop',
            10
        )

        # Safe cmd_vel
        self.cmd_vel_pub = self.create_publisher(
            Twist,
            '/safety/cmd_vel',
            10
        )

        # ======================================================
        # TIMER
        # ======================================================

        self.timer = self.create_timer(
            0.02,
            self.timer_callback
        )

        self.get_logger().info('Safety Control Node started')

    # ==========================================================
    # SICK FIELD CALLBACK
    # ==========================================================

    def sick_field_callback(self, msg: Bool):

        field_active = msg.data

        # ------------------------------------------------------
        # FIELD INTERPRETATION
        #
        # Example:
        # FALSE = normal operation
        # TRUE  = warning field active
        #
        # You can later expand this to multiple fields.
        # ------------------------------------------------------

        self.warning_field_active = field_active

        if self.warning_field_active:
            self.get_logger().warn('WARNING FIELD ACTIVE')

    # ==========================================================
    # HARDWARE CONNECTED CALLBACK
    # ==========================================================

    def connected_callback(self, msg: Bool):

        self.hardware_connected = msg.data

        if not self.hardware_connected:
            self.get_logger().error('NO CONNECTION TO MOTOR DRIVER')

    # ==========================================================
    # CMD VEL CALLBACK
    # ==========================================================

    def cmd_vel_callback(self, msg: Twist):

        # ------------------------------------------------------
        # BLOCK MOVEMENT
        # ------------------------------------------------------

        if self.is_estop_active():

            self.publish_zero_twist()
            return

        if not self.hardware_connected:

            self.publish_zero_twist()
            return

        # ------------------------------------------------------
        # SAFE FORWARDING
        # ------------------------------------------------------

        self.cmd_vel_pub.publish(msg)

    # ==========================================================
    # TIMER CALLBACK
    # ==========================================================

    def timer_callback(self):

        # ======================================================
        # GPIO ESTOP
        # ======================================================

        gpio_state = self.estop_line.get_value()

        # HIGH = ESTOP ACTIVE
        self.estop_gpio_active = (gpio_state == 1)

        if self.estop_gpio_active:
            self.get_logger().error('GPIO ESTOP ACTIVE')

        # ======================================================
        # ESTOP LOGIC
        # ======================================================

        estop_active = self.is_estop_active()

        estop_msg = Bool()
        estop_msg.data = estop_active

        self.estop_pub.publish(estop_msg)

        # ======================================================
        # SPEED LIMIT LOGIC
        # ======================================================

        speed_limit = self.normal_speed_limit

        # ESTOP
        if estop_active:

            speed_limit = self.estop_speed_limit

            self.publish_zero_twist()

        # WARNING FIELD
        elif self.warning_field_active:

            speed_limit = self.warning_speed_limit

        # NORMAL
        else:

            speed_limit = self.normal_speed_limit

        # Publish only on changes
        if speed_limit != self.current_speed_limit:

            self.current_speed_limit = speed_limit

            speed_msg = Float32()
            speed_msg.data = speed_limit

            self.speed_limit_pub.publish(speed_msg)

            self.get_logger().info(f'SPEED LIMIT: {speed_limit}%')

    # ==========================================================
    # ESTOP CHECK
    # ==========================================================

    def is_estop_active(self):

        # GPIO ESTOP
        if self.estop_gpio_active:
            return True

        # Scanner ESTOP
        if self.estop_scanner_active:
            return True

        return False

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
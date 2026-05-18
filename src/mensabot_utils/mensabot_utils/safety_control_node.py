#!/usr/bin/env python3

import rclpy
from rclpy.node import Node

from geometry_msgs.msg import Twist
from std_msgs.msg import Bool
from std_msgs.msg import Float32
from nav2_msgs.msg import SpeedLimit

import gpiod
from gpiod.line import Direction


class SafetyControlNode(Node):

    def __init__(self):
        super().__init__('safety_control_node')

        # ======================================================
        # GPIO CONFIG
        # ======================================================

        self.gpio_chip_path = "/dev/gpiochip4"
        self.gpio_line_number = 17

        try:

            self.gpio_request = gpiod.request_lines(
                self.gpio_chip_path,
                consumer="safety_control_node",
                config={
                    self.gpio_line_number: gpiod.LineSettings(
                        direction=Direction.INPUT
                    )
                }
            )

            self.get_logger().info(
                f'GPIO initialized: {self.gpio_chip_path} '
                f'Line {self.gpio_line_number}'
            )

        except Exception as e:

            self.get_logger().fatal(
                f'GPIO INIT FAILED: {e}'
            )

            raise

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

        # Debug state tracking
        self.last_gpio_estop_state = False
        self.last_warning_state = False
        self.last_connection_state = False

        # ======================================================
        # SUBSCRIBERS
        # ======================================================

        self.sick_field_sub = self.create_subscription(
            Bool,
            '/sick_field_output',
            self.sick_field_callback,
            10
        )

        self.connected_sub = self.create_subscription(
            Bool,
            '/hardware/connected',
            self.connected_callback,
            10
        )

        self.cmd_vel_sub = self.create_subscription(
            Twist,
            '/cmd_vel',
            self.cmd_vel_callback,
            10
        )

        # ======================================================
        # PUBLISHERS
        # ======================================================

        self.speed_limit_pub = self.create_publisher(
            SpeedLimit,
            '/speed_limit',
            10
        )

        self.estop_pub = self.create_publisher(
            Bool,
            '/safety/estop',
            10
        )

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

        # Publish initial state
        self.publish_speed_limit(
            self.normal_speed_limit
        )

        self.get_logger().info(
            'Safety Control Node started'
        )

    # ==========================================================
    # SICK FIELD CALLBACK
    # ==========================================================

    def sick_field_callback(self, msg: Bool):

        self.warning_field_active = msg.data

        # Debug only on state change
        if self.warning_field_active != self.last_warning_state:

            if self.warning_field_active:

                self.get_logger().warn(
                    'WARNING FIELD ACTIVE'
                )

            else:

                self.get_logger().info(
                    'WARNING FIELD CLEARED'
                )

            self.last_warning_state = (
                self.warning_field_active
            )

    # ==========================================================
    # HARDWARE CONNECTED CALLBACK
    # ==========================================================

    def connected_callback(self, msg: Bool):

        self.hardware_connected = msg.data

        # Debug only on state change
        if self.hardware_connected != self.last_connection_state:

            if self.hardware_connected:

                self.get_logger().info(
                    'MOTOR DRIVER CONNECTED'
                )

            else:

                self.get_logger().error(
                    'NO CONNECTION TO MOTOR DRIVER'
                )

            self.last_connection_state = (
                self.hardware_connected
            )

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

        try:

            gpio_state = self.gpio_request.get_value(
                self.gpio_line_number
            )

            self.estop_gpio_active = bool(gpio_state)

        except Exception as e:

            self.get_logger().error(f'GPIO READ ERROR: {e}')

            self.estop_gpio_active = True

        # Debug only on state change
        if self.estop_gpio_active != self.last_gpio_estop_state:

            if self.estop_gpio_active:

                self.get_logger().error(
                    'GPIO ESTOP ACTIVE'
                )

            else:

                self.get_logger().info(
                    'GPIO ESTOP RELEASED'
                )

            self.last_gpio_estop_state = (
                self.estop_gpio_active
            )

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

            self.publish_speed_limit(
                speed_limit
            )

    # ==========================================================
    # SPEED LIMIT PUBLISHER
    # ==========================================================

    def publish_speed_limit(self, value):

        self.current_speed_limit = value

        speed_msg = SpeedLimit()

        speed_msg.speed_limit = float(value)
        speed_msg.percentage = True

        self.speed_limit_pub.publish(speed_msg)

        #self.get_logger().info(f'SPEED LIMIT: {value}%')

    # ==========================================================
    # ESTOP CHECK
    # ==========================================================

    def is_estop_active(self):

        if self.estop_gpio_active:
            return True

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

        try:

            self.gpio_request.release()

        except Exception:
            pass

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

    finally:

        node.destroy_node()

        rclpy.shutdown()


if __name__ == '__main__':
    main()